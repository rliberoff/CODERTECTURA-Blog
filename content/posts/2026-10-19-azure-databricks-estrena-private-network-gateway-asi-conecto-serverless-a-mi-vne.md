---
title: 'Azure Databricks estrena Private Network Gateway: así conecto serverless a
  mi VNet sin romper el modelo de seguridad'
date: '2026-10-19T06:32:50+00:00'
draft: true
slug: azure-databricks-estrena-private-network-gateway-asi-conecto-serverless-a-mi-vne
description: La vista previa pública de Private Network Gateway cambia cómo conecto
  Azure Databricks serverless con recursos privados. Te cuento qué implica en arquitectura
  y cómo dejarlo configurado sin trampas.
categories:
- Azure
- Arquitectura de Software
- Inteligencia Artificial
tags:
- Azure Databricks
- Redes
- Serverless
- Private Link
- Seguridad
- Arquitectura
image: /images/azure-databricks-estrena-private-network-gateway-asi-conecto-serverless-a-mi-vne/cover.png
comments: true
ai:
  assisted: true
  article_type: technical
  model: gpt-5.4
  prompt_version: 2026-08-21.1
  generated_at: '2026-10-19T06:32:50+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://azure.microsoft.com/updates?id=576556
    title: '[In preview] Public Preview: Azure Databricks Private network gateway'
    published_date: '2026-10-16'
  - url: https://learn.microsoft.com/en-us/azure/databricks/security/network/serverless-network-security/manage-private-endpoint-rules
    title: Manage private endpoint rules - Azure Databricks | Microsoft Learn
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/databricks/release-notes/product/2026/october
    title: October 2026 - Azure Databricks | Microsoft Learn
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/databricks/release-notes/product/2026/september
    title: September 2026 - Azure Databricks | Microsoft Learn
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/databricks/security/network/serverless-network-security/private-network-gateway/configure-private-network-gateway
    title: Configure a private network gateway - Azure Databricks
    published_date: null
---

La llegada en **Public Preview** de [Azure Databricks Private network gateway](https://azure.microsoft.com/updates?id=576556) me parece una de esas novedades que no suelen acaparar titulares, pero que sí cambian decisiones de arquitectura de verdad. No tiene el brillo de un nuevo runtime ni el gancho fácil de una feature de IA, pero toca justo donde más suelen atascarse los proyectos serios: la red. Si trabajas con analytics o AI sobre Azure Databricks y quieres usar **serverless compute sin abrir agujeros en seguridad**, esto te interesa bastante.

Hasta ahora, la conversación era incómoda. Por un lado, quieres elasticidad, menos operación y toda la promesa del modelo *serverless*. Por otro, tus datos viven detrás de VNets, resolutores DNS privados, *peerings*, hubs, spokes y, con un poco de suerte, algún firewall corporativo que nadie se atreve a tocar un viernes por la tarde. Según [el anuncio oficial de Azure](https://azure.microsoft.com/updates?id=576556), esta preview habilita conectividad desde el cómputo serverless hacia recursos privados dentro de tu VNet y también hacia redes conectadas transitivamente, usando un único gateway gestionado. Y ahí está el cambio importante: **reduce la fricción entre el modelo serverless y el modelo corporativo de red**.

### Por qué esta novedad importa de verdad

En muchos entornos, el problema nunca fue “levantar Databricks”. El problema era integrarlo con lo que ya existe sin desmontar la política de seguridad de medio departamento. Storage con acceso privado, SQL gestionado expuesto solo por nombres internos, zonas privadas de DNS, topologías hub-and-spoke, conectividad híbrida... si el plano serverless no puede alcanzar esos destinos de forma controlada, acabas renunciando a una parte del servicio o vuelves a diseños más pesados.

La [guía para configurar el private network gateway](https://learn.microsoft.com/en-us/azure/databricks/security/network/serverless-network-security/private-network-gateway/configure-private-network-gateway) deja bastante claro el modelo: el gateway vive en una subnet delegada, en la misma región que la Network Connectivity Configuration (NCC) y los *workspaces* objetivo, y depende de resolutores DNS privados alcanzables desde esa subnet. Este último matiz es crucial. **Si el DNS no resuelve como crees que resuelve, la conectividad privada no existe**, aunque el diagrama de red quede precioso en PowerPoint.

{{< figure src="/images/azure-databricks-estrena-private-network-gateway-asi-conecto-serverless-a-mi-vne/source-1.png" alt="Diagrama de arquitectura del private network gateway de Azure Databricks" caption="Arquitectura base del Private Network Gateway para conectar cómputo serverless con recursos privados. Fuente: [learn.microsoft.com](https://learn.microsoft.com/en-us/azure/databricks/security/network/serverless-network-security/private-network-gateway/configure-private-network-gateway)" >}}{{< /figure >}}

Además, la documentación sobre [gestión de private endpoint rules](https://learn.microsoft.com/en-us/azure/databricks/security/network/serverless-network-security/manage-private-endpoint-rules) introduce dos implicaciones prácticas que yo no perdería de vista. La primera es operativa: los estados existen, importan y no siempre cambian al instante. Puedes encontrarte reglas en `PENDING`, `ESTABLISHED`, `REJECTED`, `DISCONNECTED` o `EXPIRED`, y la propagación suele tardar unos 10 minutos, aunque algunos cambios pueden llegar hasta 24 horas. La segunda es mucho menos glamurosa, pero muy real: esas reglas tienen coste mientras existan, independientemente de su estado. Traducido al castellano llano: no basta con crear recursos; también hay que gobernarlos y limpiar lo que ya no uses.

### Qué cambia en el diseño de red

Yo lo veo como un punto intermedio bastante sensato entre dos extremos. En uno está la aspiración de consumir Azure Databricks serverless como un servicio totalmente gestionado, sin pensar demasiado en nodos, capacidad ni redes de cómputo propias. En el otro está la realidad de organizaciones que exigen rutas privadas, DNS controlado, segmentación y, en algunos casos, inspección del tráfico antes de llegar al dato.

Con este gateway, el patrón de diseño se vuelve más explícito. El cómputo serverless deja de ser una “caja lejana” y pasa a apoyarse en una configuración de conectividad de red que enruta hacia destinos concretos o hacia la red privada definida. Ya no basta con pensar en un simple Private Endpoint. Ahora tienes que diseñar **NCC, subnet delegada, alcance DNS y destinos permitidos** como una sola pieza arquitectónica.

{{< figure src="/images/azure-databricks-estrena-private-network-gateway-asi-conecto-serverless-a-mi-vne/body-2.png" alt="Esquema de la relación entre serverless compute, NCC, gateway y destinos privados" caption="Cómo encajo NCC, gateway privado, DNS y destinos concretos en el diseño de conectividad." >}}{{< /figure >}}

Eso, de paso, cambia también la conversación con el equipo de plataforma. Ya no se trata solo de pedir “acceso para Databricks”, sino de acordar decisiones muy concretas:

- En qué subnet va a vivir el gateway,
- Qué resolutores privados va a usar,
- Qué nombres DNS deben resolverse por esa vía,
- Qué destinos entran en el modo de tráfico configurado,
- Y si ese tráfico tendrá que cruzar redes conectadas o appliances ya existentes.

Si me preguntas por la consecuencia más importante, yo diría esta: **serverless deja de ser sinónimo de desconectado de tu red privada**. Y eso abre la puerta a usarlo en escenarios donde antes el bloqueo no era funcional ni de rendimiento, sino puramente de conectividad y cumplimiento.

### Antes de empezar

Para reproducir esta configuración, yo partiría de unos prerrequisitos bastante concretos:

- Una suscripción de Azure activa.
- Un *workspace* de Azure Databricks y una [Network Connectivity Configuration](https://learn.microsoft.com/en-us/azure/databricks/security/network/serverless-network-security/manage-private-endpoint-rules) creada en la misma región.
- Permisos de **Azure Databricks account administrator**, tal y como exige la [documentación del gateway](https://learn.microsoft.com/en-us/azure/databricks/security/network/serverless-network-security/private-network-gateway/configure-private-network-gateway).
- Un *service principal* con credenciales OAuth válidas para invocar la Account REST API.
- **Azure CLI 2.75 o superior**.
- **Curl 8.x** y **jq 1.7** para lanzar y validar llamadas REST sin sufrir más de la cuenta.
- Una VNet con una subnet dedicada exclusivamente al gateway, en la misma región que la NCC y los *workspaces*.
- La subnet delegada a `Microsoft.Databricks/workspaces`.
- Un resolvedor DNS privado alcanzable desde esa subnet.
- Si tus recursos usan Azure Private DNS Zone, la zona enlazada a la VNet del gateway, como indica la [guía de configuración](https://learn.microsoft.com/en-us/azure/databricks/security/network/serverless-network-security/private-network-gateway/configure-private-network-gateway).

Sí, hay varias piezas. Y sí, aquí el detalle de red importa más de lo que parece al principio.

### Paso 1: delegar la subnet del gateway

La [documentación oficial](https://learn.microsoft.com/en-us/azure/databricks/security/network/serverless-network-security/private-network-gateway/configure-private-network-gateway) indica que la subnet debe estar delegada a `Microsoft.Databricks/workspaces` antes de crear el gateway. Yo no daría esto por hecho: lo comprobaría y, si hace falta, lo aplicaría explícitamente con Azure CLI.

```bash
az network vnet subnet update \
  --resource-group rg-analytics-prod \
  --vnet-name vnet-data-hub-weu \
  --name snet-databricks-gateway \
  --delegations Microsoft.Databricks/workspaces  # Obligatorio para que Databricks pueda crear el gateway en esta subnet
```

La salida debería reflejar la delegación correcta en el JSON de la subnet:

```json
{
  "name": "snet-databricks-gateway",
  "delegations": [
    {
      "serviceName": "Microsoft.Databricks/workspaces"
    }
  ]
}
```

Si no ves esa delegación, yo no seguiría. El gateway no está pensado para una subnet compartida ni improvisada.

### Paso 2: obtener un token OAuth para la Account API

La [guía de configuración](https://learn.microsoft.com/en-us/azure/databricks/security/network/serverless-network-security/private-network-gateway/configure-private-network-gateway) explica que la creación del gateway se hace mediante la account REST API y requiere un *access token* OAuth obtenido con *client credentials*. Este paso parece menor, pero no lo es. Cuando falla, mucha gente acaba diagnosticando “problemas de red” que en realidad son simplemente permisos mal montados.

Yo prefiero separar bien la obtención del token y validar la respuesta antes de seguir:

```bash
set -euo pipefail

TENANT_ID="11111111-2222-3333-4444-555555555555"
CLIENT_ID="66666666-7777-8888-9999-aaaaaaaaaaaa"
CLIENT_SECRET="DatabricksProdSecret2026"
DATABRICKS_ACCOUNT_ID="bbbbbbbb-cccc-dddd-eeee-ffffffffffff"

ACCESS_TOKEN=$(curl -sS --fail -X POST \
  "https://login.microsoftonline.com/${TENANT_ID}/oauth2/v2.0/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "client_id=${CLIENT_ID}" \
  --data-urlencode "client_secret=${CLIENT_SECRET}" \
  --data-urlencode "grant_type=client_credentials" \
  --data-urlencode "scope=2ff814a6-3304-4ab8-85cb-cd0e6f879c1d/.default" \
  | jq -er '.access_token')

printf '%s
' "${ACCESS_TOKEN:0:40}..."
```

Aquí he endurecido un poco el ejemplo por una razón sencilla: `--fail` y `jq -e` hacen que el script reviente si la llamada devuelve error o si no hay `access_token`. Parece una tontería, pero evita seguir con un token `null` como si nada (que es una forma bastante eficiente de perder tiempo).

Si todo va bien, verás una cadena JWT recortada similar a esta:

```text
eyJ0eXAiOiJKV1QiLCJub25jZSI6IkpPV3p5b0...
```

Si obtienes `null` o un error de Entra ID, revisa primero credenciales y permisos del *service principal* en la cuenta de Databricks.

### Paso 3: crear el Private Network Gateway

Aquí está el corazón de la novedad. Según la [documentación del endpoint de configuración](https://learn.microsoft.com/en-us/azure/databricks/security/network/serverless-network-security/private-network-gateway/configure-private-network-gateway), el gateway se crea bajo el endpoint `private-network-gateways` asociado a tu NCC. Y, cuando trabajas en modo `SPECIFIC_DESTINATIONS`, tienes que indicar expresamente los nombres DNS que quieres enrutar a través del gateway.

En este ejemplo apunto a una cuenta de Storage privada accesible por `blob` y `dfs`, además de un nombre privado para SQL, usando un resolvedor DNS interno en `10.20.4.10`:

```bash
ACCOUNT_HOST="https://accounts.azuredatabricks.net"
NCC_ID="ncc-4b2f1c9e8a7d6f01"
GATEWAY_SUBNET_ID="/subscriptions/12345678-90ab-cdef-1234-567890abcdef/resourceGroups/rg-analytics-prod/providers/Microsoft.Network/virtualNetworks/vnet-data-hub-weu/subnets/snet-databricks-gateway"

jq -n \
  --arg gateway_name "pvg-serverless-weu-prod" \
  --arg subnet_id "${GATEWAY_SUBNET_ID}" \
  --arg resolver "10.20.4.10" \
  '{
    gateway_name: $gateway_name,
    traffic_mode: "SPECIFIC_DESTINATIONS",
    destinations: [
      "stlandingprodweu.blob.core.windows.net",
      "stlandingprodweu.dfs.core.windows.net",
      "sql-mi-analytics.privatelink.database.windows.net"
    ],
    private_dns_resolvers: [$resolver],
    azure_cloud_connection: {
      gateway_subnet: {
        resource_id: $subnet_id  
      }
    }
  }' \
| curl -sS --fail -X POST \
    "${ACCOUNT_HOST}/api/2.0/accounts/${DATABRICKS_ACCOUNT_ID}/network-connectivity-configurations/${NCC_ID}/private-network-gateways" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json" \
    --data-binary @- \
| jq
```

He preferido construir el cuerpo con `jq -n` en lugar de interpolar JSON a mano. No es por estética: es para evitar errores tontos de comillas, escapado o variables vacías justo en el punto más delicado de la llamada.

La respuesta debería devolverte un objeto JSON con el identificador del gateway y su configuración inicial. Un ejemplo simplificado sería este:

```json
{
  "gateway_name": "pvg-serverless-weu-prod",
  "traffic_mode": "SPECIFIC_DESTINATIONS",
  "private_dns_resolvers": [
    "10.20.4.10"
  ],
  "destinations": [
    "stlandingprodweu.blob.core.windows.net",
    "stlandingprodweu.dfs.core.windows.net",
    "sql-mi-analytics.privatelink.database.windows.net"
  ]
}
```

Aquí yo vigilaría dos cosas con bastante obsesión. La primera, que los destinos sean exactamente los nombres DNS reales de los recursos privados a los que quieres llegar. La segunda, que el resolvedor indicado sepa contestar correctamente desde esa topología. **El gateway no “descubre” nada por ti: depende por completo de que tu DNS privado esté bien diseñado**.

### Paso 4: listar y verificar el gateway creado

Una vez creado, yo comprobaría inmediatamente que la NCC ya ve el gateway y que el objeto existe con la configuración esperada. La propia [guía oficial](https://learn.microsoft.com/en-us/azure/databricks/security/network/serverless-network-security/private-network-gateway/configure-private-network-gateway) indica que puedes listarlos con un `GET` sobre el mismo ámbito.

```bash
curl -sS --fail -X GET \
  "${ACCOUNT_HOST}/api/2.0/accounts/${DATABRICKS_ACCOUNT_ID}/network-connectivity-configurations/${NCC_ID}/private-network-gateways" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
| jq '.[] | {gateway_name, traffic_mode, destinations, private_dns_resolvers}'
```

Yo aquí no necesito todo el JSON: me basta con filtrar los campos que validan que estoy mirando el gateway correcto. Si no aparece `pvg-serverless-weu-prod`, o si los destinos no cuadran, algo ha fallado o estás consultando otra NCC distinta (que también pasa más de lo que debería).

{{< figure src="/images/azure-databricks-estrena-private-network-gateway-asi-conecto-serverless-a-mi-vne/body-3.png" alt="Diagrama de estados de reglas de private endpoint en Azure Databricks" caption="Estados operativos que conviene vigilar al validar la conectividad privada desde serverless." >}}{{< /figure >}}

### Paso 5: comprobar las reglas de conectividad privada y sus estados

Aunque el gateway es la pieza nueva, la operación real no termina ahí. La [documentación de private endpoint rules](https://learn.microsoft.com/en-us/azure/databricks/security/network/serverless-network-security/manage-private-endpoint-rules) deja claro que los estados de las reglas importan, y que los cambios no siempre son instantáneos.

Mi recomendación práctica es muy simple: no declares victoria hasta ver `ESTABLISHED`. Si una regla está en `PENDING`, sigues en propagación. Si aparece `REJECTED` o `DISCONNECTED`, ya no estás ante un problema genérico “de Databricks”, sino ante un fallo concreto de aprobación, conectividad o configuración del recurso remoto.

Lo esperable es algo como esto:

```text
Estado esperado de la regla privada: ESTABLISHED
Tiempo típico de propagación: alrededor de 10 minutos
Tiempo máximo documentado para aplicación completa: hasta 24 horas
```

No parece muy espectacular, lo sé. Pero en red muchas veces la diferencia entre “funciona” y “aún no funciona” es simplemente saber esperar lo correcto y mirar el estado correcto.

### Cómo encaja con redes de tránsito y appliances existentes

La parte realmente interesante del anuncio no es solo llegar a la VNet local, sino también a **redes conectadas transitivamente**. Esa frase del [anuncio oficial de la preview](https://azure.microsoft.com/updates?id=576556) es la que me hace pensar que esta novedad puede desbloquear bastantes escenarios reales en topologías hub-and-spoke o con conectividad híbrida.

{{< figure src="/images/azure-databricks-estrena-private-network-gateway-asi-conecto-serverless-a-mi-vne/source-4.png" alt="Topología de red con tránsito entre VNet, hub y sistemas conectados" caption="Ejemplo visual de una topología con redes transitivas, útil para entender el encaje del gateway en escenarios hub-and-spoke. Fuente: [learn.microsoft.com](https://learn.microsoft.com/en-us/azure/databricks/release-notes/product/2026/october)" >}}{{< /figure >}}

Si la VNet donde resides el gateway ya enruta hacia un hub central, hacia *network virtual appliances* o incluso hacia conectividad *on-premises*, esa topología pasa a formar parte del camino disponible para el cómputo serverless. Dicho de otra forma: puedes empezar a encajar el tráfico serverless dentro del estándar corporativo en lugar de tratarlo como una excepción incómoda.

Eso sí, yo aquí sería prudente. Que exista ruta no significa que el diseño sea automáticamente correcto. Antes de darlo por bueno, validaría al menos estas tres cosas:

- Resolución DNS coherente de extremo a extremo,
- Rutas efectivas desde la subnet del gateway hasta el destino,
- Y políticas de inspección o filtrado compatibles con el patrón de tráfico generado por Databricks.

Si tu organización ya impone appliances de seguridad obligatorios, esta preview puede ser justo la pieza que faltaba. Pero también puede destapar algo menos agradable: que tu red privada estaba más “intuitivamente entendida” que realmente diseñada como sistema reproducible.

### Lo que yo haría antes de llevarlo a producción

Yo no activaría esto directamente en un entorno crítico sin una checklist bastante concreta. Empezaría con un solo destino privado bien conocido, por ejemplo una cuenta de Storage de aterrizaje. Después validaría la resolución DNS desde la perspectiva de la subnet del gateway, confirmaría el estado `ESTABLISHED` de las reglas asociadas y solo entonces ampliaría el conjunto de destinos.

También revisaría con calma el coste operativo. La [documentación sobre private endpoint rules](https://learn.microsoft.com/en-us/azure/databricks/security/network/serverless-network-security/manage-private-endpoint-rules) recuerda que hay cargos de red cuando cargas serverless conectan con recursos del cliente y que las reglas privadas facturan por hora mientras existan. **La seguridad de red mal gobernada no solo complica la arquitectura; también encarece la factura**.

Y hay un último punto que para mí es clave: el *ownership*. En este tipo de diseños casi siempre intervienen tres mundos distintos —plataforma de datos, red corporativa y seguridad— y si nadie tiene claro quién mantiene el DNS privado, quién aprueba rutas o quién elimina reglas obsoletas, el sistema envejece fatal. Rápido, además.

### Mi conclusión

Yo creo que Azure Databricks Private Network Gateway viene a resolver una tensión muy real: querer lo mejor del modelo *serverless* sin renunciar al perímetro de red que exige una plataforma de datos seria. La preview apunta justo al punto donde más dolía: la conexión controlada con recursos privados y redes transitivas.

¿Es una novedad vistosa? No especialmente. ¿Es importante? Para mí, muchísimo. **Cuando una capacidad de red desbloquea serverless para cargas seguras, no estás viendo un detalle de infraestructura: estás viendo un cambio de arquitectura**. Si trabajas con Azure Databricks en entornos regulados, con segmentación fuerte o con topologías corporativas complejas, yo la seguiría muy de cerca y empezaría a probarla ya en un *landing zone* controlado.

Porque sí: aquí tampoco hay magia. Pero precisamente por eso me gusta. Todo depende de diseñar bien la red, el DNS y el gobierno. Y, una vez hecho, el modelo *serverless* deja de pelearse con tu seguridad para empezar a trabajar con ella.
