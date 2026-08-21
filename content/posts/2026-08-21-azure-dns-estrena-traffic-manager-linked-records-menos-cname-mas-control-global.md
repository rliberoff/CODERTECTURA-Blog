---
title: 'Azure DNS estrena Traffic Manager linked records: menos CNAME, más control
  global'
date: '2026-08-21T11:29:50+00:00'
draft: true
slug: azure-dns-estrena-traffic-manager-linked-records-menos-cname-mas-control-global
description: Analizo la preview de Traffic Manager linked records en Azure DNS y te
  enseño por qué elimina fricción operativa, mejora la higiene DNS y simplifica el
  failover global.
categories:
- Azure
- Arquitectura de Software
- Networking
tags:
- Azure DNS
- Azure Traffic Manager
- Networking
- Alta disponibilidad
- DNS
- Arquitectura cloud
image: /images/azure-dns-estrena-traffic-manager-linked-records-menos-cname-mas-control-global/cover.png
comments: true
ai:
  assisted: true
  article_type: technical
  model: gpt-5.4
  prompt_version: 2026-08-21.1
  generated_at: '2026-08-21T11:29:50+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://azure.microsoft.com/updates?id=569743
    title: '[Launched] Generally Available: Summarized advertised gateway prefixes
      for route advertisement'
    published_date: '2026-08-20'
  - url: https://learn.microsoft.com/en-us/azure/traffic-manager/traffic-manager-overview
    title: Azure Traffic Manager overview | Microsoft Learn
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/traffic-manager/secure-traffic-manager
    title: Secure your Azure Traffic Manager deployment | Microsoft Learn
    published_date: null
  - url: https://techcommunity.microsoft.com/blog/azurenetworkingblog/azure-dns-introduces-traffic-manager-linked-records-public-preview/4547112
    title: Azure DNS introduces Traffic Manager linked records (Public Preview) |
      Microsoft Community Hub
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/dns/dns-traffic-manager-linked-records
    title: Traffic Manager Linked Records overview - Azure DNS | Microsoft Learn
    published_date: null
---

Si diseñas aplicaciones globales, hay una novedad de Azure que a mí me parece bastante más importante de lo que sugiere el nombre. La **preview de Traffic Manager linked records** en Azure DNS no es un simple retoque cosmético: elimina el patrón clásico del CNAME hacia `trafficmanager.net`, simplifica la resolución DNS y, sobre todo, deja una topología más limpia para escenarios de resiliencia, multi-región e incluso DNSSEC. Yo la veo como una de esas mejoras que no te obligan a rediseñar la plataforma entera, pero sí te quitan fricción justo en una capa donde cualquier detalle acaba importando mucho.

Según el anuncio en el [Azure Networking Blog sobre Traffic Manager linked records](https://techcommunity.microsoft.com/blog/azurenetworkingblog/azure-dns-introduces-traffic-manager-linked-records-public-preview/4547112), Azure DNS puede asociar directamente un record set público con un perfil de Azure Traffic Manager y resolver internamente la decisión de enrutado. La [documentación oficial de la funcionalidad](https://learn.microsoft.com/en-us/azure/dns/dns-traffic-manager-linked-records) lo define como un vínculo gestionado entre Azure DNS y Traffic Manager mediante la propiedad `trafficManagementProfile`, devolviendo al cliente la respuesta final sin el salto intermedio a `trafficmanager.net`.

### Por qué esta preview sí merece tu atención

Hasta ahora, el patrón más habitual consistía en publicar un CNAME o un alias que terminaba exponiendo un nombre de `trafficmanager.net`. Funcionaba, por supuesto. Y [Traffic Manager sigue siendo un balanceador global basado en DNS con health checks y distintos métodos de routing](https://learn.microsoft.com/en-us/azure/traffic-manager/traffic-manager-overview). Pero ese enfoque tenía tres peajes bastante claros.

El primero era la complejidad de resolución: el cliente recibía un nombre intermedio y tenía que hacer una consulta adicional. El segundo era la higiene DNS: estabas enseñando una dependencia operativa que, en realidad, pertenece a tu implementación interna y no aporta nada al consumidor del dominio. Y el tercero, que para mí es el más fino pero también el más interesante, es que la [resolución integrada mantiene la cadena de confianza para DNSSEC](https://learn.microsoft.com/en-us/azure/dns/dns-traffic-manager-linked-records), algo que ese salto al dominio intermedio podía romper.

**Mi lectura arquitectónica es muy simple: menos acoplamiento visible, menos superficie operativa y un modelo DNS bastante más coherente.** No sustituye a Front Door, no convierte Traffic Manager en un proxy y no cambia su naturaleza. Lo que hace es mejorar precisamente el caso de uso para el que Traffic Manager ya era una herramienta muy válida: decidir por DNS a qué endpoint público debe ir el cliente según salud y política de enrutado.

{{< figure src="/images/azure-dns-estrena-traffic-manager-linked-records-menos-cname-mas-control-global/source-1.png" alt="Diagrama general de funcionamiento de Azure Traffic Manager" caption="Azure Traffic Manager sigue siendo la pieza que toma la decisión de enrutado global basada en DNS y salud de los endpoints. Fuente: [learn.microsoft.com](https://learn.microsoft.com/en-us/azure/traffic-manager/traffic-manager-overview)" >}}{{< /figure >}}

### Qué cambia exactamente frente al patrón antiguo

La diferencia importante no está en que Traffic Manager deje de enrutar, sino en **dónde se materializa la respuesta final**. Con el enfoque anterior, tu zona DNS devolvía un CNAME hacia el perfil de Traffic Manager. Con linked records, Azure DNS consulta internamente ese perfil y responde al cliente con la IP o el FQDN final, según el tipo de registro configurado. La [documentación de Azure DNS](https://learn.microsoft.com/en-us/azure/dns/dns-traffic-manager-linked-records) llama a este comportamiento *DNS flattening*.

En la práctica, esto trae varias consecuencias muy útiles:

- Ocultas `trafficmanager.net` en la respuesta DNS;
- Reduces una consulta adicional del lado del cliente;
- Mejoras la compatibilidad con DNSSEC en una zona firmada;
- Simplificas algunas revisiones de seguridad y gobierno del DNS;
- Sigues aprovechando los métodos de enrutado, monitorización y failover de Traffic Manager.

Si tú trabajas como arquitecto o llevas una plataforma, esto te interesa especialmente cuando quieres mantener una **fachada DNS corporativa estable** mientras cambias por debajo la lógica de distribución, failover o despliegue regional. Y eso, aunque parezca pequeño, suele tener bastante valor. A veces más del que aparenta en una nota de producto de tres minutos.

### Antes de empezar

Para reproducir el escenario que te propongo, yo partiría de estos requisitos:

- Una suscripción de Azure activa.
- [Azure CLI](https://learn.microsoft.com/en-us/azure/dns/dns-traffic-manager-linked-records) instalada y actualizada. Yo asumiré **Azure CLI 2.75 o superior** para evitar sorpresas con comandos recientes.
- Permisos suficientes sobre la suscripción o el grupo de recursos. En la práctica, **Contributor** sobre el grupo de recursos donde vas a crear Traffic Manager y DNS suele ser un mínimo razonable.
- Dos endpoints públicos accesibles por Internet para simular disponibilidad regional. Para que el ejemplo sea reproducible, usaré dos FQDN públicos estables: `www.microsoft.com` y `learn.microsoft.com` como endpoints externos de demostración en Traffic Manager.
- Una zona pública de Azure DNS que controles. En el ejemplo crearé `codertectura-demo.net`.
- `Dig` o `nslookup` en tu equipo para verificar respuestas DNS.

Importante: esta funcionalidad está en **public preview**, tal y como indica la [documentación oficial de Traffic Manager Linked Records](https://learn.microsoft.com/en-us/azure/dns/dns-traffic-manager-linked-records). Yo no la metería todavía en una plataforma crítica sin validar antes soporte, comportamiento de TTL y un plan de rollback decente. Sí, ya sé: esto suena menos emocionante que una demo. Pero luego llegan los viernes por la tarde.

### Paso 1: crear el perfil de Traffic Manager

Voy a montar primero el plano de enrutado global. En este ejemplo uso el método `Priority`, porque es el más fácil de verificar en una demo de failover: mientras el endpoint primario esté sano, se devuelve ese; si no, cae al secundario.

```bash
# Azure CLI 2.75+
az group create \
  --name rg-dns-linkedrecords-demo \
  --location westeurope

az network traffic-manager profile create \
  --resource-group rg-dns-linkedrecords-demo \
  --name tm-codertectura-global \
  --routing-method Priority \
  --unique-dns-name tm-codertectura-global-demo \
  --ttl 30 \
  --protocol HTTPS \
  --port 443 \
  --path / \
  --interval 30 \
  --timeout 10 \
  --max-failures 3
```

La salida esperada debería devolverte un JSON con `profileStatus` en `Enabled`, `trafficRoutingMethod` en `Priority` y el FQDN público del perfil terminado en `trafficmanager.net`.

Ahora añado dos endpoints externos. No son mis aplicaciones, pero sí me sirven para demostrar que Traffic Manager puede decidir entre destinos públicos distintos sin meter ruido adicional en la demo.

```bash
# Azure CLI 2.75+
az network traffic-manager endpoint create \
  --resource-group rg-dns-linkedrecords-demo \
  --profile-name tm-codertectura-global \
  --name primary-web \
  --type externalEndpoints \
  --target www.microsoft.com \
  --endpoint-status Enabled \
  --priority 1

az network traffic-manager endpoint create \
  --resource-group rg-dns-linkedrecords-demo \
  --profile-name tm-codertectura-global \
  --name secondary-web \
  --type externalEndpoints \
  --target learn.microsoft.com \
  --endpoint-status Enabled \
  --priority 2
```

Si todo va bien, en ambos casos verás `endpointStatus` en `Enabled` y la prioridad correspondiente. Poco después, los endpoints deberían aparecer ya como monitorizados correctamente.

Para comprobarlo, yo consultaría el perfil así:

```bash
# Azure CLI 2.75+
az network traffic-manager profile show \
  --resource-group rg-dns-linkedrecords-demo \
  --name tm-codertectura-global \
  --query "{dnsConfig:dnsConfig.fqdn, monitorConfig:monitorConfig, endpoints:endpoints[].{name:name,target:target,priority:endpointProperties.priority,status:endpointStatus,monitorStatus:endpointMonitorStatus}}"
```

```json
{
  "dnsConfig": "tm-codertectura-global-demo.trafficmanager.net",
  "monitorConfig": {
    "path": "/",
    "port": 443,
    "protocol": "HTTPS"
  },
  "endpoints": [
    {
      "name": "primary-web",
      "monitorStatus": "Online",
      "priority": 1,
      "status": "Enabled",
      "target": "www.microsoft.com"
    },
    {
      "name": "secondary-web",
      "monitorStatus": "Online",
      "priority": 2,
      "status": "Enabled",
      "target": "learn.microsoft.com"
    }
  ]
}
```

### Paso 2: crear la zona DNS pública y el linked record

Aquí está la parte realmente interesante. La [documentación de Azure DNS sobre linked records](https://learn.microsoft.com/en-us/azure/dns/dns-traffic-manager-linked-records) explica que el nuevo vínculo se expresa con la propiedad `trafficManagementProfile`. Como la forma más fiable de reproducir esto suele ser infraestructura como código, prefiero enseñártelo con **Bicep** en vez de depender de que cada instalación de CLI exponga exactamente la misma superficie.

{{< figure src="/images/azure-dns-estrena-traffic-manager-linked-records-menos-cname-mas-control-global/body-2.png" alt="Esquema de Azure DNS con linked record hacia Traffic Manager" caption="Con linked records, Azure DNS consulta internamente Traffic Manager y devuelve la respuesta final sin exponer trafficmanager.net." >}}{{< /figure >}}

Este template crea la zona pública y un registro `app` de tipo CNAME enlazado al perfil de Traffic Manager sin publicar el CNAME clásico hacia `trafficmanager.net`.

```bicep
param dnsZoneName string = 'codertectura-demo.net'
param trafficManagerProfileId string

resource dnsZone 'Microsoft.Network/dnsZones@2018-05-01' = {
  name: dnsZoneName
  location: 'global'
}

resource appLinkedRecord 'Microsoft.Network/dnsZones/CNAME@2018-05-01' = {
  name: '${dnsZone.name}/app'
  properties: {
    TTL: 30
    trafficManagementProfile: {
      id: trafficManagerProfileId // esta línea activa el vínculo gestionado con Traffic Manager
    }
  }
}
```

Y este sería el despliegue:

```bash
# Azure CLI 2.75+ y Bicep CLI 0.30+
TM_ID=$(az network traffic-manager profile show \
  --resource-group rg-dns-linkedrecords-demo \
  --name tm-codertectura-global \
  --query id -o tsv)

cat > main.bicep <<'EOF'
param dnsZoneName string = 'codertectura-demo.net'
param trafficManagerProfileId string

resource dnsZone 'Microsoft.Network/dnsZones@2018-05-01' = {
  name: dnsZoneName
  location: 'global'
}

resource appLinkedRecord 'Microsoft.Network/dnsZones/CNAME@2018-05-01' = {
  name: '${dnsZone.name}/app'
  properties: {
    TTL: 30
    trafficManagementProfile: {
      id: trafficManagerProfileId
    }
  }
}
EOF

az deployment group create \
  --resource-group rg-dns-linkedrecords-demo \
  --template-file main.bicep \
  --parameters dnsZoneName='codertectura-demo.net' trafficManagerProfileId="$TM_ID"
```

La salida debería terminar con `provisioningState` en `Succeeded`. Si inspeccionas el recurso, verás el record set `app` creado dentro de la zona.

Para comprobar que el registro existe:

```bash
# Azure CLI 2.75+
az network dns record-set cname show \
  --resource-group rg-dns-linkedrecords-demo \
  --zone-name codertectura-demo.net \
  --name app
```

Lo que deberías ver es un JSON con el `TTL` y la referencia al perfil de Traffic Manager. Lo relevante aquí es que **la resolución la hará Azure DNS internamente**, no el cliente mediante un salto intermedio expuesto.

### Paso 3: verificar la resolución DNS y el efecto práctico

Una vez delegada la zona en tu registrador o en un entorno de pruebas equivalente, toca verificar el comportamiento desde el lado del cliente. Si todavía no has delegado la zona, puedes validar la existencia del recurso dentro de Azure; pero para ver la respuesta final necesitas que la zona sea resoluble públicamente.

```bash
# Verificación con dig
# Si quieres evitar cachés recursivas, consulta directamente a los NS autoritativos de tu zona.
dig app.codertectura-demo.net CNAME +short
dig app.codertectura-demo.net A +short
```

Lo esperable, según el modelo descrito en la [explicación de DNS flattening de Azure DNS](https://learn.microsoft.com/en-us/azure/dns/dns-traffic-manager-linked-records), es que no aparezca una respuesta intermedia apuntando a `trafficmanager.net`, sino la respuesta final resuelta por Azure DNS a partir del perfil enlazado.

{{< figure src="/images/azure-dns-estrena-traffic-manager-linked-records-menos-cname-mas-control-global/source-3.png" alt="Configuración DNS clásica con CNAME intermedio hacia Traffic Manager" caption="El patrón clásico con CNAME intermedio ayuda a entender justo qué elimina esta nueva integración. Fuente: [learn.microsoft.com](https://learn.microsoft.com/en-us/azure/dns/dns-traffic-manager-linked-records)" >}}{{< /figure >}}

Este matiz, para mí, es la clave de todo. **El nombre público que tú controlas sigue siendo el centro de la arquitectura.** Traffic Manager continúa tomando la decisión, pero ya no te obliga a enseñar ese detalle de implementación en la respuesta DNS del cliente.

### Paso 4: simular failover y observar el cambio

Ahora viene la parte divertida (o lo más parecido a divertida que puede ser una demo de DNS): el failover. En un perfil `Priority`, basta con deshabilitar el endpoint primario para que Traffic Manager responda usando el secundario.

```bash
# Azure CLI 2.75+
az network traffic-manager endpoint update \
  --resource-group rg-dns-linkedrecords-demo \
  --profile-name tm-codertectura-global \
  --name primary-web \
  --type externalEndpoints \
  --endpoint-status Disabled

az network traffic-manager profile show \
  --resource-group rg-dns-linkedrecords-demo \
  --name tm-codertectura-global \
  --query "endpoints[].{name:name,status:endpointStatus,monitorStatus:endpointMonitorStatus,target:target}"
```

```json
[
  {
    "name": "primary-web",
    "status": "Disabled",
    "monitorStatus": "Disabled",
    "target": "www.microsoft.com"
  },
  {
    "name": "secondary-web",
    "status": "Enabled",
    "monitorStatus": "Online",
    "target": "learn.microsoft.com"
  }
]
```

Después de esperar el TTL configurado, repite la resolución DNS:

```bash
# Verificación del failover
# La decisión cambia en Traffic Manager, pero recuerda que los resolvers intermedios pueden cachear hasta agotar el TTL.
dig app.codertectura-demo.net CNAME +short
dig app.codertectura-demo.net A +short
```

Lo que deberías observar es una respuesta coherente con el endpoint secundario. El tiempo exacto dependerá del TTL y de las cachés DNS intermedias, pero la decisión de enrutado la sigue tomando Traffic Manager, tal y como explica la [visión general de Azure Traffic Manager](https://learn.microsoft.com/en-us/azure/traffic-manager/traffic-manager-overview).

### Implicaciones de seguridad y operación que no conviene pasar por alto

Hay una segunda lectura de esta feature que, sinceramente, me parece casi más interesante que la puramente técnica. En la [guía para securizar despliegues de Traffic Manager](https://learn.microsoft.com/en-us/azure/traffic-manager/secure-traffic-manager) se insiste en permitir correctamente las sondas de salud y en proteger bien la configuración DNS, porque un fallo ahí puede provocar desvíos de tráfico o falsas caídas. Linked records no elimina esa responsabilidad, pero sí mejora el perímetro conceptual.

Al no exponer `trafficmanager.net` en la respuesta, reduces dependencias visibles y evitas ciertas configuraciones demasiado amplias alrededor de un dominio compartido. Además, la [documentación de linked records](https://learn.microsoft.com/en-us/azure/dns/dns-traffic-manager-linked-records) menciona expresamente la mejora de higiene DNS y la reducción del riesgo asociado a subdominios colgantes por configuraciones huérfanas.

Eso sí: no confundas esta mejora con un cambio de capa. Traffic Manager **sigue siendo DNS-based**, no un proxy de capa 7. Si tú necesitas terminación TLS global, WAF, aceleración *anycast* o afinidad en el edge, seguirás mirando a Front Door. Linked records mejora el modelo DNS; no lo convierte en otra pieza distinta. Y esto conviene tenerlo claro para no pedirle a la herramienta algo que nunca quiso ser.

{{< figure src="/images/azure-dns-estrena-traffic-manager-linked-records-menos-cname-mas-control-global/body-4.png" alt="Flujo de failover DNS entre endpoint primario y secundario" caption="En un perfil Priority, el failover cambia la respuesta DNS efectiva cuando el endpoint primario deja de estar disponible." >}}{{< /figure >}}

### Mi recomendación práctica

Si ya usas Traffic Manager con Azure DNS público, yo sí empezaría a probar esta preview en entornos no críticos. Especialmente si te molestaba exponer `trafficmanager.net`, si estás trabajando con DNSSEC o si quieres una topología DNS más limpia para aplicaciones multi-región. El beneficio no está en “hacer más”, sino en **hacer lo mismo de una forma más integrada, más limpia y más segura**.

Si estás diseñando una plataforma global nueva, mi consejo es valorar este patrón desde el principio. Te deja un nombre DNS corporativo estable, te permite mantener el control del enrutado en Traffic Manager y evita arrastrar un detalle de implementación histórico que ya no aporta demasiado valor. En arquitectura, muchas veces las mejores mejoras son estas: las que eliminan una capa accidental sin complicarte la vida.

Y aquí, sinceramente, creo que Azure ha acertado.
