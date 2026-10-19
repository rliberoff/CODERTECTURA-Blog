---
title: 'Managed HSM con claves externas ya es GA: qué cambia de verdad y cómo montarlo
  paso a paso'
date: '2026-10-19T06:36:59+00:00'
draft: true
slug: managed-hsm-con-claves-externas-ya-es-ga-que-cambia-de-verdad-y-como-montarlo-pa
description: Azure Managed HSM ya permite gestión externa de claves en disponibilidad
  general. Te explico qué cambia de verdad y cómo montar EKM con Azure CLI.
categories:
- Azure
- Arquitectura de Software
- Seguridad
tags:
- Managed HSM
- Azure Key Vault
- Seguridad
- Claves gestionadas por el cliente
- Cumplimiento
- Azure CLI
image: /images/managed-hsm-con-claves-externas-ya-es-ga-que-cambia-de-verdad-y-como-montarlo-pa/cover.png
comments: true
ai:
  assisted: true
  article_type: technical
  model: gpt-5.4
  prompt_version: 2026-08-21.1
  generated_at: '2026-10-19T06:36:59+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://azure.microsoft.com/updates?id=574296
    title: '[Launched] Generally Available: External key management for Azure Key
      Vault Managed HSM'
    published_date: '2026-10-16'
  - url: https://learn.microsoft.com/en-us/azure/key-vault/managed-hsm/external-key-management-networking
    title: Configure networking and mTLS for Azure Key Vault Managed HSM external
      key management | Microsoft Learn
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/security/fundamentals/key-management
    title: Overview of key management in Azure | Microsoft Learn
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/key-vault/managed-hsm/external-key-management-overview
    title: What is Managed HSM external key management? | Microsoft Learn
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/key-vault/managed-hsm/external-key-management-quickstart-cli
    title: 'Quickstart: Create your first external key in Azure Key Vault Managed
      HSM using the Azure CLI | Microsoft Learn'
    published_date: null
---

La llegada a disponibilidad general de la gestión externa de claves para Azure Key Vault Managed HSM me parece una de esas novedades que no hacen demasiado ruido, pero que **resuelven un problema muy concreto**. Si trabajas en entornos con requisitos de soberanía, custodia física o separación estricta de responsabilidades, aquí hay un cambio importante: ahora puedes seguir usando el patrón de CMK de servicios de Azure, pero dejando la *key-encryption key* fuera de la infraestructura de Microsoft mediante un HSM externo y un EKM Proxy operado por ti o por tu proveedor.

La clave de todo esto no está solo en “tener más control”, sino en **dónde vive realmente el material criptográfico más sensible**. El [anuncio de disponibilidad general de External key management para Managed HSM](https://azure.microsoft.com/updates?id=574296) indica que la característica ya está disponible en todas las regiones públicas de Azure. Y la [visión general de Managed HSM external key management](https://learn.microsoft.com/en-us/azure/key-vault/managed-hsm/external-key-management-overview) deja bastante claro el modelo: el servicio de Azure sigue cifrando tus datos con una DEK, pero la KEK que protege esa DEK permanece en tu HSM externo.

### Qué problema resuelve exactamente

Si ya usas *customer-managed keys* en Azure, esto te sonará. En el modelo clásico, la CMK vive en Azure Key Vault o en Managed HSM. Eso encaja muy bien en muchos escenarios, pero no en todos. Hay organizaciones para las que no basta con gestionar la clave: necesitan que el material de la KEK **no resida físicamente en infraestructura de Microsoft** por razones regulatorias, contractuales o, directamente, de soberanía.

Aquí entra EKM. La [visión general de gestión de claves en Azure](https://learn.microsoft.com/en-us/azure/security/fundamentals/key-management) distingue entre PMK, CMK y escenarios BYOK, pero EKM va un paso más allá. No se trata de importar la clave y alojarla en Azure, sino de mantener la KEK fuera, mientras Managed HSM sigue siendo la interfaz que entienden los servicios de Azure para autenticación, autorización y operaciones asociadas al uso de la clave.

Dicho de forma práctica: Azure no delega el cifrado masivo de tus datos al HSM externo. El servicio de Azure sigue usando su DEK para cifrar y descifrar datos. Lo que se externaliza es la operación criptográfica sobre la clave que protege esa DEK. **Y eso cambia mucho la conversación**, porque reduces el impacto operativo frente a intentar sacar fuera de Azure todo el plano de datos.

### Cómo encaja la arquitectura

La [arquitectura de Managed HSM external key management](https://learn.microsoft.com/en-us/azure/key-vault/managed-hsm/external-key-management-overview) gira alrededor de cuatro piezas muy concretas:

- Un servicio de Azure compatible con CMK.
- Tu Managed HSM en Azure.
- Un EKM Proxy que expones tú o tu proveedor.
- Un HSM externo donde reside la KEK.

El flujo simplificado es este:

1. El servicio de Azure necesita proteger o recuperar una DEK.
2. Habla con Managed HSM usando el modelo normal de CMK.
3. Managed HSM establece una conexión saliente al EKM Proxy.
4. El proxy reenvía la operación al HSM externo.
5. Se devuelve el resultado de `wrap` o `unwrap`, pero **la KEK no sale del HSM externo**.

Esto tiene una consecuencia arquitectónica importante. Managed HSM no necesita entrar en tu red como un cliente “con IP fija”. La [guía de red y mTLS para EKM](https://learn.microsoft.com/en-us/azure/key-vault/managed-hsm/external-key-management-networking) explica que la identidad de confianza no se basa en *allow-lists* de IP, porque las IP de origen no son estáticas, sino en autenticación mutua con certificados X.509. Private Link puede añadir aislamiento de red, sí, pero no sustituye a mTLS. Y conviene no confundir una cosa con la otra, porque de ahí salen muchos diseños de seguridad equivocados.

### Antes de empezar

Si quieres reproducir el flujo de extremo a extremo, yo prepararía esto primero:

- Una suscripción de Azure activa.
- Azure CLI **2.75 o superior**.
- La extensión `keyvault` actualizada en Azure CLI.
- Un recurso **Azure Key Vault Managed HSM** ya creado.
- Permisos sobre el HSM con los roles que menciona la [guía rápida de Azure CLI para claves externas](https://learn.microsoft.com/en-us/azure/key-vault/managed-hsm/external-key-management-quickstart-cli): al menos **Managed HSM EKM Administrator** y **Managed HSM Crypto User**.
- Un EKM Proxy accesible por FQDN público si vas por el modelo de internet público.
- La cadena de confianza de servidor del proxy y acceso para configurar en ese proxy la confianza del certificado cliente de Managed HSM.
- Un endpoint `/info` operativo en el proxy, porque la guía rápida lo usa para verificar la conectividad.

Yo, además, validaría dos cosas fuera de Azure antes de tocar nada: que el FQDN del proxy resuelve correctamente y que el proxy está preparado para aceptar mTLS con el certificado cliente de Managed HSM. Parece obvio, pero es el tipo de comprobación que te ahorra una tarde entera de diagnóstico (y algún que otro suspiro dramático).

### Paso 1: preparar Azure CLI para EKM

La [guía rápida oficial con Azure CLI](https://learn.microsoft.com/en-us/azure/key-vault/managed-hsm/external-key-management-quickstart-cli) parte de la extensión `keyvault`. Yo lo dejaría así, de forma explícita y reproducible:

```bash
# Azure CLI 2.75+ y extensión keyvault actualizada
az version --output json
az extension add --name keyvault --upgrade  # así evito distinguir entre instalar y actualizar
az login
az account set --subscription "00000000-1111-2222-3333-444444444444"
```

La salida relevante que deberías ver en `az version` es la versión de Azure CLI y la presencia de `keyvault`. Si la extensión no está al día, yo no seguiría. En funcionalidades recientes, trabajar con una extensión antigua es una manera muy eficiente de perder tiempo sin aprender nada útil.

### Paso 2: obtener el certificado cliente de Managed HSM para configurar mTLS

Este paso es crítico y, para mí, es donde mejor se entiende el modelo de confianza. Managed HSM presenta un certificado cliente al EKM Proxy en cada conexión entrante al proxy. Antes de crear la conexión, tienes que extraer el `subjectCommonName` y las CA raíz para que tu proxy pueda validar que el cliente es realmente tu Managed HSM.

```bash
az keyvault ekm-connection certificate show \
  --hsm-name mhsm-regulado-prod \
  --output json
```

La salida esperada será similar a esta:

```json
{
  "caCertificates": [
    "MIIDj..."
  ],
  "subjectCommonName": "contoso.managedhsmclient.azure.net"
}
```

Con esto, en tu EKM Proxy debes configurar la validación del cliente para aceptar certificados con ese `subjectCommonName` y encadenados a una de esas CA. La [documentación de red y mTLS](https://learn.microsoft.com/en-us/azure/key-vault/managed-hsm/external-key-management-networking) insiste en que **la seguridad aquí se apoya en certificados, no en IPs de origen**. Y me parece importante subrayarlo, porque diseñar protección alrededor de *allow-lists* de IP en este escenario es empezar por el sitio equivocado.

{{< figure src="/images/managed-hsm-con-claves-externas-ya-es-ga-que-cambia-de-verdad-y-como-montarlo-pa/body-2.png" alt="Esquema del flujo mTLS entre Managed HSM y EKM Proxy" caption="El canal de confianza en EKM se basa en mTLS: identidad por certificados, no por IP." >}}{{< /figure >}}

### Paso 3: crear la conexión EKM hacia tu proxy

Cuando el proxy ya confía en el certificado cliente de Managed HSM, puedes crear la conexión. Esta conexión vincula tu HSM gestionado con un único EKM Proxy e incluye el host, la CA del servidor y, opcionalmente, un prefijo de ruta.

```bash
az keyvault ekm-connection create \
  --hsm-name mhsm-regulado-prod \
  --host ekmproxy.contoso-security.es \
  --server-ca-certificate "$(awk 'NF {sub(/\r/, ""); printf "%s\n", $0;}' ekmproxy-root-ca.pem)" \
  --path-prefix ekm \
  --output json
```

La parte delicada aquí es `--server-ca-certificate`: **estás entregando el ancla de confianza del servidor que Managed HSM usará para validar el proxy**. Por eso prefiero leer el PEM preservando correctamente los saltos de línea, en lugar de confiar en un `cat` rápido que luego termina siendo el sospechoso habitual cuando algo falla.

Si el comando devuelve errores de confianza TLS, yo revisaría primero la CA del servidor y después la configuración mTLS del proxy. Casi nunca compensa empezar revisando Azure antes que la cadena de certificados. Además, la [guía de red](https://learn.microsoft.com/en-us/azure/key-vault/managed-hsm/external-key-management-networking) describe dos modelos de conectividad —internet público y Private Link—, pero aclara que la integración con Azure Private Link para este escenario sigue en *preview*. Así que, si estás montando hoy algo productivo sobre la parte GA, **yo asumiría internet público con mTLS fuerte como línea base** y solo evaluaría Private Link si realmente necesitas esa capa adicional y aceptas el riesgo de una integración todavía en *preview*.

### Paso 4: verificar el proxy con la sonda `/info`

La [guía rápida de CLI](https://learn.microsoft.com/en-us/azure/key-vault/managed-hsm/external-key-management-quickstart-cli) menciona la verificación de conexión, y una práctica muy útil es comprobar que el proxy responde por la ruta informativa que espera el flujo de EKM. Si tu proxy expone `/info`, puedes validarlo primero desde tu entorno de administración para asegurarte de que el endpoint existe y entrega metadatos coherentes.

```bash
curl --silent --show-error --fail \
  https://ekmproxy.contoso-security.es/ekm/info | jq
```

Aquí he añadido `--fail` y `--show-error` por una razón muy simple: si el endpoint devuelve un `404` o un `500`, prefiero enterarme en ese momento y no recibir una falsa sensación de “todo parece correcto”. Deberías obtener un documento JSON válido. El contenido exacto depende de la implementación del proveedor, pero si no recibes `200 OK` y JSON coherente, yo no seguiría con la creación de claves externas.

Después, la verificación verdaderamente importante es que Managed HSM pueda usar ese camino. Si la conexión EKM está bien montada, las siguientes operaciones sobre una *external key* deberían completarse sin errores de conectividad ni de TLS.

### Paso 5: crear una external key y probar el camino criptográfico

Aquí está el punto de verdad. Según la [guía rápida para crear tu primera external key con Azure CLI](https://learn.microsoft.com/en-us/azure/key-vault/managed-hsm/external-key-management-quickstart-cli), el objetivo es crear una referencia de clave externa en Managed HSM y usar después su URI como CMK en un servicio compatible.

```bash
az keyvault key create \
  --hsm-name mhsm-regulado-prod \
  --name finance-ekm-key \
  --kty RSA-HSM \
  --ops wrapKey unwrapKey \
  --exportable false \
  --output json
```

La salida debería incluir el identificador de la clave, normalmente en `key.kid`, y las operaciones permitidas `wrapKey` y `unwrapKey`. Después puedes inspeccionarla así:

```bash
az keyvault key show \
  --hsm-name mhsm-regulado-prod \
  --name finance-ekm-key \
  --output json
```

Deberías ver un JSON con la URI completa de la clave. Esa URI es la que luego usarás al configurar CMK en el servicio de Azure compatible que quieras proteger.

### Paso 6: validar `wrap`/`unwrap` sobre la clave de prueba

Para mí, este es el chequeo mínimo que separa una configuración “aparentemente correcta” de una que realmente funciona. Si el camino EKM está bien montado, Managed HSM podrá ejecutar la operación de protección y recuperación de la clave de prueba a través del proxy y del HSM externo.

```bash
az keyvault key encrypt \
  --hsm-name mhsm-regulado-prod \
  --name finance-ekm-key \
  --algorithm RSA-OAEP \
  --value "U29tZVNlY3JldERFS0J5dGVz" \
  --output json
```

La salida debería incluir un campo `result` en base64url, señal de que la operación criptográfica se completó. Y la comprobación inversa:

```bash
az keyvault key decrypt \
  --hsm-name mhsm-regulado-prod \
  --name finance-ekm-key \
  --algorithm RSA-OAEP \
  --value "<resultado-devuelto-en-el-paso-anterior>" \
  --output json
```

Aquí deberías recuperar el valor original. Si el descifrado falla, yo revisaría por este orden: operaciones permitidas de la clave, soporte del algoritmo en el proxy o en el HSM externo y, después, logs de mTLS y del *back-end* del EKM Proxy. **No asumiría de entrada que “es un problema de Azure”**, porque en este tipo de integración el punto frágil suele estar en la confianza TLS o en la implementación del proveedor.

### Qué cambia para equipos de seguridad y arquitectura

Más allá del tutorial, yo creo que el valor real de esta GA está en cómo permite dividir responsabilidades sin romper la integración nativa de Azure. Managed HSM sigue siendo el punto de entrada que entienden los servicios de Azure, pero la custodia material de la KEK puede quedarse bajo tus controles o bajo los de un tercero especializado. Eso encaja especialmente bien en banca, sector público, defensa o entornos con restricciones serias de residencia criptográfica.

También cambia la conversación con *compliance*. Antes, muchas veces la pregunta era “¿la clave está en Azure?”. Ahora la pregunta correcta pasa a ser “¿qué clave está en Azure y cuál no?”. Y esa distinción importa bastante, porque la [documentación de visión general](https://learn.microsoft.com/en-us/azure/key-vault/managed-hsm/external-key-management-overview) explica que el patrón sigue siendo *envelope encryption*: la DEK opera en el servicio, la KEK externa protege esa DEK y no se libera desde el HSM externo.

{{< figure src="/images/managed-hsm-con-claves-externas-ya-es-ga-que-cambia-de-verdad-y-como-montarlo-pa/body-3.png" alt="Comparativa visual entre CMK tradicional y EKM con KEK externa" caption="Comparación conceptual: con EKM la KEK permanece fuera de Microsoft, mientras el servicio de Azure sigue cifrando con la DEK." >}}{{< /figure >}}

### Mis cautelas antes de lanzarte a producción

Yo no vendería esto como una solución mágica. Tiene ventajas muy claras, pero también eleva el listón operativo.

La primera cautela es la disponibilidad del EKM Proxy. Si ese proxy o el HSM externo se convierten en un cuello de botella, puedes afectar operaciones de protección de claves de servicios críticos. La segunda es la gestión de certificados: la [guía de networking y mTLS](https://learn.microsoft.com/en-us/azure/key-vault/managed-hsm/external-key-management-networking) remarca el ciclo de vida y la rotación, y aquí **un certificado caducado no es un detalle menor**; puede convertirse en un incidente de producción bastante serio. La tercera es la compatibilidad: EKM aplica a servicios de Azure que ya soportan CMK con Managed HSM, así que conviene revisar el servicio concreto antes de diseñar la plataforma alrededor de esta capacidad.

Yo añadiría una cautela más, aunque sea menos glamurosa: operativamente, esto introduce otra pieza que tienes que monitorizar, securizar y mantener. Y eso significa más observabilidad, más procedimientos de rotación y más disciplina de operación. No es necesariamente malo; simplemente conviene llamarlo por su nombre.

### Mi conclusión

Yo veo esta GA como una pieza muy potente para arquitecturas de seguridad de alto valor. No porque sustituya a Key Vault o a Managed HSM en el sentido clásico, sino porque añade una opción intermedia muy interesante: seguir aprovechando la integración nativa de Azure sin renunciar a mantener la KEK fuera de Microsoft.

Si tu requisito es simplemente “quiero CMK”, probablemente no necesites esta complejidad. Pero si tu requisito es “quiero CMK y además demostrar custodia externa real de la KEK”, entonces sí: **esta funcionalidad cambia bastante el juego**.

Y eso, en seguridad, no pasa tan a menudo.
