---
title: Cómo rotar credenciales en Azure API Management sin tumbar producción
date: '2026-11-23T06:20:26+00:00'
draft: true
slug: como-rotar-credenciales-en-azure-api-management-sin-provocar-una-caida
description: 'Te cuento cómo rotar secretos en Azure API Management sin cortar tráfico:
  orden correcto, validación real y revocación segura.'
categories:
- Azure
- Arquitectura de Software
- Seguridad
tags:
- Azure API Management
- Seguridad
- Rotación de secretos
- Azure CLI
- APIs
image: /images/como-rotar-credenciales-en-azure-api-management-sin-provocar-una-caida/cover.png
comments: true
ai:
  assisted: true
  article_type: technical
  model: gpt-5.4
  prompt_version: 2026-08-21.1
  generated_at: '2026-11-23T06:20:26+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://techcommunity.microsoft.com/t5/azure-integration-services-blog/rotating-credentials-in-azure-api-management/ba-p/4575478
    title: Rotating credentials in Azure API Management
    published_date: '2026-11-21'
  - url: https://azure.microsoft.com/updates?id=581463
    title: '[Launched] Generally Available: Governance policy guidance in Foundry
      Canvas and VS Code'
    published_date: '2026-11-21'
---

Rotar credenciales en Azure API Management parece una tarea rutinaria… hasta que el orden de los pasos te tira una API en producción. Yo lo he visto más de una vez: el problema casi nunca está en cambiar un secreto, sino en **cambiarlo en el sitio equivocado o en el momento equivocado**. Si actualizas APIM antes de que el emisor acepte la nueva credencial, rompes llamadas. Si revocas la antigua demasiado pronto, cortas tráfico. Y si solo tocas APIM pero no el sistema que emite la credencial, en realidad no has rotado nada.

La guía de [rotación de credenciales en Azure API Management](https://techcommunity.microsoft.com/t5/azure-integration-services-blog/rotating-credentials-in-azure-api-management/ba-p/4575478) deja la idea central bastante clara: cuando la credencial antigua y la nueva pueden convivir durante una ventana temporal, el orden seguro es crear primero la nueva en el emisor, actualizar después APIM, probar el flujo completo y revocar la anterior al final. Parece casi de sentido común cuando lo lees así. Pero en operaciones con prisa, tickets abiertos y alguien preguntando por Teams si «ya está», justo ese orden es lo primero que se sacrifica.

### El principio que de verdad evita la caída

Si me preguntas por la regla más importante de todo este proceso, yo la resumiría así: **la rotación ocurre donde nace la credencial, no donde se consume**. APIM consume secretos en muchos sitios: *named values*, credenciales de backend, secretos de clientes OAuth 2.0 u OpenID Connect, cadenas de conexión de loggers e incluso valores incrustados directamente en políticas. Pero la validez real de esa credencial no la decide APIM; la decide el backend, el proveedor de identidad o el servicio que la emitió.

Eso cambia por completo la forma de operar. Actualizar un *named value* en APIM no invalida la clave anterior en tu backend. Cambiar el secreto de un *authorization server* en APIM no revoca por sí solo el secreto del cliente en Microsoft Entra ID o en el IdP que estés usando. Por eso me parece tan útil la [recomendación oficial sobre el orden de rotación](https://techcommunity.microsoft.com/t5/azure-integration-services-blog/rotating-credentials-in-azure-api-management/ba-p/4575478): primero emites la nueva credencial, luego la consumes desde APIM, verificas que todo el camino funciona y, solo entonces, retiras la antigua.

{{< figure src="/images/como-rotar-credenciales-en-azure-api-management-sin-provocar-una-caida/body-1.png" alt="Diagrama del orden seguro de rotación en APIM" caption="El orden correcto evita la caída: emitir, actualizar APIM, probar y revocar." >}}{{< /figure >}}

### Qué credenciales merece la pena revisar en APIM

Antes de tocar nada, yo haría inventario. Siempre. Según [la guía de Microsoft](https://techcommunity.microsoft.com/t5/azure-integration-services-blog/rotating-credentials-in-azure-api-management/ba-p/4575478), hay varios puntos que conviene revisar como mínimo:

- *Subscription keys*.
- *Named values* que contienen secretos.
- Credenciales de backend en cabeceras, *query string* o certificados cliente.
- Secretos de clientes OAuth 2.0 y OpenID Connect.
- *Connection strings* de loggers, por ejemplo Event Hubs o Application Insights.
- Secretos escritos directamente dentro de políticas.

Este último punto es el que más disgustos suele dar. Mucha gente da por hecho que todos los secretos viven en *named values* o en Key Vault, pero luego aparece una policy con un `set-header`, un `send-request` o una cadena codificada que incrusta un token o una API key en texto claro. **Y ahí se rompe la ilusión de control**: la rotación se marca como completada, pero en realidad queda una dependencia vieja todavía viva en algún rincón del gateway.

### Antes de empezar

Para seguir este recorrido de principio a fin, yo partiría de unos prerrequisitos bastante terrenales:

- Azure CLI instalado, idealmente **Azure CLI 2.75 o superior**.
- Sesión iniciada con `az login` en una suscripción donde exista al menos una instancia de APIM.
- Permisos para leer y actualizar API Management en la instancia objetivo.
- Una instancia de Azure API Management ya creada.
- Al menos un backend o una API que dependa de una credencial rotatoria.
- Acceso a `management.azure.com` si usas la Management API.
- `Curl` disponible para validar respuestas HTTP desde terminal.

Si quieres reproducir los ejemplos tal cual, yo voy a asumir una instancia llamada `apim-prod-payments` en el grupo `rg-integration-prod`, dentro de una suscripción ya accesible con tu sesión actual.

### Paso 1: localizar tus instancias de APIM

Yo empezaría por lo más básico: saber cuántas instancias tienes realmente. Puede parecer una tontería, pero en entornos con varias suscripciones o varios entornos, olvidarte de un APIM secundario, uno regional o uno de preproducción es bastante más fácil de lo que debería.

La [consulta con Azure Resource Graph que propone Microsoft](https://techcommunity.microsoft.com/t5/azure-integration-services-blog/rotating-credentials-in-azure-api-management/ba-p/4575478) me parece una buena forma de empezar porque te da una vista rápida de todas las instancias visibles para tu identidad.

```bash
# Azure CLI 2.75+
az graph query \
  -q "resources | where type =~ 'microsoft.apimanagement/service' | project name, resourceGroup, subscriptionId, location" \
  --output table
```

La salida esperada será una tabla con, al menos, estas columnas:

```text
Name                 ResourceGroup         SubscriptionId                         Location
-------------------  --------------------  -------------------------------------  ---------
apim-prod-payments   rg-integration-prod   11111111-2222-3333-4444-555555555555   westeurope
apim-pre-payments    rg-integration-pre    11111111-2222-3333-4444-555555555555   westeurope
```

Si no ves ninguna fila, yo sospecharía de dos cosas antes de volverme creativo: permisos insuficientes o contexto equivocado de tenant o suscripción. No suele haber mucha más magia que esa.

### Paso 2: inventariar named values y detectar secretos

El siguiente paso es identificar dónde puede haber credenciales activas dentro de APIM. Para los *named values*, [Microsoft recomienda usar Azure CLI](https://techcommunity.microsoft.com/t5/azure-integration-services-blog/rotating-credentials-in-azure-api-management/ba-p/4575478), y a mí me parece un buen punto de partida porque muchísimas policies dependen de ellos aunque no siempre sea evidente a simple vista.

```bash
# Azure CLI 2.75+
az apim nv list \
  --resource-group rg-integration-prod \
  --service-name apim-prod-payments \
  --output table
```

La salida mostrará los *named values* existentes. Yo me fijaría sobre todo en nombres que delaten contenido sensible y en si están marcados como secretos:

```text
DisplayName                 Name                          Secret    Tags
--------------------------  ----------------------------  --------  -----------------
PaymentsBackendApiKey       payments-backend-api-key      True      integration,payments
OAuthClientSecret           payments-oauth-client-secret  True      oauth
BackendBaseUrl              payments-backend-base-url     False     config
```

Aquí suelo hacerme dos preguntas. La primera: si el secreto está en APIM, ¿hay un proceso de rotación definido o vive ahí desde hace meses como si fuera mobiliario urbano? La segunda: si el valor viene de Key Vault, ¿está bien gobernada la referencia y el consumidor recoge realmente la nueva versión cuando toca? La [guía de rotación](https://techcommunity.microsoft.com/t5/azure-integration-services-blog/rotating-credentials-in-azure-api-management/ba-p/4575478) insiste en que esto importa porque **no rotas igual un secreto almacenado directamente en APIM que uno referenciado desde Key Vault**.

{{< figure src="/images/como-rotar-credenciales-en-azure-api-management-sin-provocar-una-caida/body-2.png" alt="Inventario de secretos en Azure API Management" caption="Antes de rotar, yo revisaría named values, backends, OAuth, loggers y policies." >}}{{< /figure >}}

### Paso 3: revisar backends, authorization servers y loggers

Una rotación segura no termina en los *named values*. Yo revisaría también backends, proveedores OAuth/OpenID y loggers, porque ahí suelen esconderse dependencias menos obvias y, por tanto, más peligrosas.

Puedes listar backends con la Management API de APIM usando la versión `2024-05-01`, tal y como aparece en [la referencia práctica publicada por Microsoft](https://techcommunity.microsoft.com/t5/azure-integration-services-blog/rotating-credentials-in-azure-api-management/ba-p/4575478):

```bash
# Azure CLI 2.75+ usando la Management API de APIM
az rest --method get \
  --url "https://management.azure.com/subscriptions/11111111-2222-3333-4444-555555555555/resourceGroups/rg-integration-prod/providers/Microsoft.ApiManagement/service/apim-prod-payments/backends?api-version=2024-05-01" \
  --output json
```

Deberías obtener un JSON con la colección `value` y los backends definidos. Si alguno usa cabeceras de autorización, parámetros de *query* o certificados de cliente, yo lo metería directamente en el alcance de la rotación. No porque vaya a darte problemas seguro, sino porque si te lo dejas fuera, el problema aparecerá cuando menos gracia te haga.

La misma [guía de Microsoft](https://techcommunity.microsoft.com/t5/azure-integration-services-blog/rotating-credentials-in-azure-api-management/ba-p/4575478) enumera también los endpoints para revisar *authorization servers*, proveedores OpenID Connect, *identity providers*, *authorization providers* y loggers. La mecánica es la misma: listar, localizar qué credencial está activa y mapear quién la emite de verdad. Esa última parte es la importante. Si no sabes quién emite la credencial, no sabes realmente dónde empieza la rotación.

### Paso 4: actualizar APIM solo después de emitir la nueva credencial

Aquí está la parte delicada. Imagina que tu backend acepta una API key nueva y la antigua al mismo tiempo durante una pequeña ventana de transición. Ese es el escenario ideal para una rotación sin interrupción.

El orden seguro sería este:

1. Crear la nueva clave en el backend o sistema emisor.
2. Actualizar APIM para que use la nueva.
3. Probar llamadas reales a través de APIM.
4. Revocar la clave antigua en el backend.

Para un caso sencillo con un *named value* secreto, puedes actualizarlo desde Azure CLI así:

```bash
# Azure CLI 2.75+
az apim nv update \
  --resource-group rg-integration-prod \
  --service-name apim-prod-payments \
  --named-value-id payments-backend-api-key \
  --secret true \
  --value "sk_live_2026_11_rotated_9f3a" \
  --output json
```

La salida debería confirmar la actualización del recurso. Lo normal es que el secreto no se devuelva en claro, pero sí verás el identificador y la marca de secreto:

```json
{
  "displayName": "PaymentsBackendApiKey",
  "keyVault": null,
  "name": "payments-backend-api-key",
  "secret": true,
  "tags": [
    "integration",
    "payments"
  ]
}
```

Si tu policy usa ese *named value* para construir una cabecera `Authorization` o `x-api-key`, APIM empezará a enviar el nuevo valor cuando la configuración quede aplicada. La condición para que esto no rompa nada es muy simple, y a la vez muy fácil de incumplir: **el backend ya tiene que estar aceptando la nueva clave**. Si haces este paso antes, el corte lo has introducido tú.

### Paso 5: validar el camino completo antes de revocar

Yo no revocaría nunca la credencial antigua sin una prueba funcional de extremo a extremo. Ver que el recurso de APIM se ha actualizado no basta. Necesitas comprobar que la llamada real pasa por el gateway y llega al backend con la nueva credencial funcionando.

Un ejemplo sencillo es invocar la API publicada en APIM con una *subscription key* válida y revisar el código HTTP:

```bash
# curl 8.x
curl --include --fail-with-body \
  "https://apim-prod-payments.azure-api.net/payments/health" \
  -H "Ocp-Apim-Subscription-Key: 4f6e8c19a5d24f57b3a7f8d0c1e2b9aa" # compruebo el flujo real a través del gateway, no solo la configuración
```

La salida esperada debería incluir una respuesta satisfactoria del backend, por ejemplo:

```text
HTTP/1.1 200 OK
content-type: application/json
x-backend-service: payments-api

{"status":"ok","dependency":"authorized"}
```

Si recibes `401 Unauthorized` o `403 Forbidden`, yo no seguiría con la revocación ni de broma. En ese punto revisaría tres cosas: si el backend tiene realmente activa la nueva credencial, si APIM está apuntando al *named value* correcto y si existe alguna policy a nivel global, de API, de operación o de producto que siga inyectando el secreto viejo por otro camino. Esto último pasa más de lo que debería (y sí, suele descubrirse cuando alguien ya ha desactivado la credencial antigua).

{{< figure src="/images/como-rotar-credenciales-en-azure-api-management-sin-provocar-una-caida/body-3.png" alt="Validación del flujo entre cliente, APIM y backend" caption="La prueba importante no es el cambio en configuración, sino la llamada real pasando por el gateway." >}}{{< /figure >}}

### Un runbook mínimo que sí me parece sensato

Cuando tengo que dejar esto documentado para un equipo, yo prefiero escribir un runbook operativo y no una nota vaga del estilo «acordarse de cambiar también APIM». Mi versión mínima sería esta:

1. Inventariar todos los puntos donde APIM consume la credencial.
2. Crear una nueva credencial en el emisor y permitir coexistencia temporal.
3. Actualizar APIM: *named values*, backends, *authorization servers* o policies, según corresponda.
4. Ejecutar pruebas funcionales reales a través del gateway.
5. Revisar logs y códigos de respuesta durante una pequeña ventana de observación.
6. Revocar la credencial antigua en el emisor.
7. Volver a probar para confirmar que solo la nueva sigue en uso.

Lo importante no es solo seguir estos pasos, sino entender por qué están en ese orden. **La disponibilidad depende de la superposición temporal entre la credencial vieja y la nueva**. Si tu sistema emisor no permite esa convivencia, entonces ya no estás ante una rotación tranquila, sino ante una operación coordinada con más riesgo y, seguramente, con ventana controlada.

### Ojo con las policies: ahí suelen esconderse los problemas

La propia [guía de Microsoft sobre APIM](https://techcommunity.microsoft.com/t5/azure-integration-services-blog/rotating-credentials-in-azure-api-management/ba-p/4575478) recomienda revisar policies globales, de API, de operación y de producto precisamente porque es habitual que allí queden secretos incrustados. Yo le daría mucha prioridad a esa revisión. Un *named value* bien rotado no te sirve de gran cosa si una policy heredada sigue metiendo una cabecera con un token antiguo en una operación concreta.

Si gestionas APIM como código, mejor todavía. Busca patrones como `Authorization`, `api-key`, `password`, `token`, `connectionString` o valores Base64 sospechosos dentro de las policies exportadas. No es una técnica sofisticada, pero es de esas comprobaciones con una relación esfuerzo/beneficio francamente buena.

### Mi recomendación práctica

Si te quedas con una sola idea, que sea esta: en APIM, rotar secretos de forma segura es sobre todo una cuestión de **disciplina operativa**. Inventaria primero, rota en el emisor, actualiza APIM después, prueba el flujo completo y revoca al final. Suena obvio escrito así, pero en la práctica es justo el paso que más se salta la gente cuando hay presión.

Yo no intentaría convertir esta operación en un gesto manual improvisado desde el portal. La automatizaría con Azure CLI o con la Management API, dejaría trazabilidad de cada cambio y haría explícito el orden de operaciones en un runbook. Cuando haces eso, la rotación deja de ser un momento de tensión y pasa a ser una rutina segura.

Si estás revisando ahora mismo una instancia de APIM, yo empezaría por lo más rentable: listar *named values*, revisar backends y buscar secretos embebidos en policies. Ahí suele estar el 80 % del riesgo. Y como puedes ver, **no hay magia**. Solo orden, visibilidad y bastante menos improvisación.
