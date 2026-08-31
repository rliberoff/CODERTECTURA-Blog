---
title: 'Menos ruido BGP en Azure: cómo resumir prefijos anunciados en un hub-and-spoke'
date: '2026-08-31T12:53:30+00:00'
draft: true
slug: menos-ruido-bgp-en-azure-como-resumir-prefijos-anunciados-en-un-hub-and-spoke
description: Te enseño a usar «advertised gateway prefixes» en Azure para resumir
  rutas BGP en un hub-and-spoke híbrido y validar el cambio de forma reproducible.
categories:
- Azure
- Arquitectura de Software
tags:
- Azure Networking
- BGP
- ExpressRoute
- VPN Gateway
- Hub and Spoke
- Arquitectura de Red
image: /images/menos-ruido-bgp-en-azure-como-resumir-prefijos-anunciados-en-un-hub-and-spoke/cover.png
comments: true
ai:
  assisted: true
  article_type: technical
  model: gpt-5.4
  prompt_version: 2026-08-21.1
  generated_at: '2026-08-31T12:53:30+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://techcommunity.microsoft.com/t5/azure-networking-blog/advertised-gateway-prefixes-in-azure/ba-p/4550940
    title: Advertised gateway prefixes in Azure
    published_date: '2026-08-28'
  - url: https://learn.microsoft.com/en-us/azure/virtual-network/advertised-gateway-prefixes-overview
    title: Advertised gateway prefixes in Azure virtual networks
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/expressroute/expressroute-routing
    title: 'Azure ExpressRoute: Routing requirements | Microsoft Learn'
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/virtual-network/virtual-network-peering-overview
    title: Azure Virtual Network Peering | Microsoft Learn
    published_date: null
---

Cuando una topología híbrida en Azure empieza a crecer de verdad, el problema ya no es solo conectar redes. El problema es **mantener la tabla de rutas bajo control**. En un diseño hub-and-spoke con *gateway transit*, Azure puede anunciar hacia *on-premises* no solo el espacio del hub, sino también los prefijos de cada *spoke* conectado. Y cuando pasas de unos pocos *spokes* a decenas —o a cientos—, eso deja de ser un detalle simpático y se convierte en ruido BGP, complejidad operativa y, en el peor momento posible, un límite de escala demasiado cerca.

La buena noticia es que Azure ya trae una forma nativa de resumir esos anuncios: los *advertised gateway prefixes*. Según el [anuncio oficial de la funcionalidad](https://techcommunity.microsoft.com/t5/azure-networking-blog/advertised-gateway-prefixes-in-azure/ba-p/4550940) y la [documentación de Azure sobre advertised gateway prefixes](https://learn.microsoft.com/en-us/azure/virtual-network/advertised-gateway-prefixes-overview), esta capacidad permite que los *gateways* híbridos anuncien uno o varios CIDR agregados en lugar de propagar cada prefijo individual del hub y los *spokes* cubiertos. Dicho de otra forma: menos ruido, menos entradas y una lectura bastante más limpia desde el lado *on-premises*.

En este artículo te voy a enseñar qué resuelve exactamente, cuándo lo usaría yo sin dudarlo y cómo configurarlo y validarlo de forma reproducible. Porque sí, cambiar una propiedad en una VNet es fácil. Lo importante de verdad es saber **por qué lo haces, qué efecto esperas y cómo compruebas que no te has contado una historia bonita a ti mismo**.

### Qué cambia realmente con «advertised gateway prefixes»

El comportamiento por defecto en un hub-and-spoke híbrido es bastante directo. Tal y como encaja con el modelo de [Virtual Network Peering y tránsito de gateway](https://learn.microsoft.com/en-us/azure/virtual-network/virtual-network-peering-overview), el *gateway* anuncia el *address space* del hub y también los *address spaces* de los *spokes* emparejados que usan *gateway transit*. Eso funciona, claro. Pero también implica que, a medida que crece el número de redes, la vista desde el router *on-premises* se va llenando de prefijos individuales.

Imagina este caso sencillo:

- Hub: `10.27.0.0/24`
- Spoke 1: `10.27.1.0/24`
- Spoke 2: `10.27.2.0/24`
- Spoke 3: `10.27.3.0/24`

Sin resumen, Azure anunciará esos cuatro prefijos. Con *advertised gateway prefixes*, puedes pedirle al *gateway* que anuncie `10.27.0.0/22`, siempre que esa agregación cubra realmente esos espacios. **La mejora no es cosmética**: reduces entradas BGP, limpias la visibilidad de la red y haces que tu plan de direccionamiento se entienda mucho mejor desde fuera de Azure.

{{< figure src="/images/menos-ruido-bgp-en-azure-como-resumir-prefijos-anunciados-en-un-hub-and-spoke/body-1.png" alt="Diagrama de resumen de rutas BGP en una topología hub-and-spoke" caption="El valor de la funcionalidad está en sustituir muchos prefijos de spokes por uno o varios CIDR agregados anunciados desde el hub." >}}{{< /figure >}}

Aquí hay un matiz que a mí me parece especialmente sano. Esta funcionalidad no “inventa” cobertura ni tapa redes mágicamente. Si tienes un *spoke* fuera del rango resumido, ese prefijo seguirá anunciándose por separado. Y eso, lejos de ser una limitación, me parece una virtud. El resumen funciona cuando tu direccionamiento está bien pensado; **no rescata un plan IP caótico**.

### Cuándo lo usaría yo, y cuándo no

Yo lo usaría en cuanto se cumplan tres condiciones. La primera: tienes una topología híbrida real con `VPN Gateway` o `ExpressRoute Gateway` en el hub. La segunda: estás usando *gateway transit* para que los *spokes* sean alcanzables desde *on-premises*. Y la tercera: tu direccionamiento en Azure tiene cierta estructura, por ejemplo bloques por entorno, por dominio funcional o por plataforma, de forma que puedas resumir con `/20`, `/18` o `/16` que tengan sentido.

La razón práctica se entiende especialmente bien en ExpressRoute. La [documentación de routing de ExpressRoute](https://learn.microsoft.com/en-us/azure/expressroute/expressroute-routing) y el propio [artículo técnico de Microsoft](https://techcommunity.microsoft.com/t5/azure-networking-blog/advertised-gateway-prefixes-in-azure/ba-p/4550940) sitúan esta funcionalidad en un contexto muy claro: gestionar mejor el crecimiento de prefijos anunciados desde la red virtual hacia *on-premises*. **Esperar a tocar el límite para reaccionar me parece una mala estrategia**. Si puedes resumir antes, ganas margen operativo y reduces la probabilidad de acabar investigando incidencias de red a horas poco cristianas (que suele ser cuando aparecen estas cosas, curiosamente).

¿Cuándo no lo usaría? Cuando el espacio IP en Azure esté fragmentado sin criterio, cuando el resumen cubra redes que no deberían ser alcanzables por esa conexión o cuando dependas de una visibilidad muy granular en routers *on-premises* para políticas muy específicas. Resumir simplifica, sí, pero también abstrae detalle. Y en red, como casi siempre, la virtud suele estar en elegir **la simplificación correcta**, no en simplificar por deporte.

### Antes de empezar

Si quieres reproducir lo que te muestro aquí, yo partiría de estos requisitos:

- Una suscripción de Azure activa.
- Un hub VNet ya creado con `GatewaySubnet`.
- Un `Virtual Network Gateway` de tipo VPN o ExpressRoute ya desplegado en el hub.
- Uno o varios *spokes* emparejados al hub con *gateway transit* configurado.
- Permisos para modificar la red virtual del hub: al menos **Network Contributor** sobre el *resource group* o la propia VNet.
- [Azure CLI](https://learn.microsoft.com/en-us/azure/virtual-network/advertised-gateway-prefixes-overview) instalada. En este artículo doy por hecho **Azure CLI 2.75 o superior**, porque necesito actualizar propiedades ARM de forma fiable.
- Opcional, pero muy recomendable: acceso al router *on-premises* o, como mínimo, a la herramienta con la que inspeccionas rutas BGP recibidas.

La propiedad que nos interesa es `summarizedGatewayPrefixes`, expuesta en el portal como **Advertised gateway prefixes** y asociada a la VNet del hub, tal y como recoge la [documentación oficial](https://learn.microsoft.com/en-us/azure/virtual-network/advertised-gateway-prefixes-overview).

{{< figure src="/images/menos-ruido-bgp-en-azure-como-resumir-prefijos-anunciados-en-un-hub-and-spoke/source-2.png" alt="Topología de peering con gateway remoto en Azure" caption="El peering con tránsito de gateway es la base sobre la que el hub puede anunciar hacia on-premises los espacios de red de los spokes. Fuente: [learn.microsoft.com](https://learn.microsoft.com/en-us/azure/virtual-network/virtual-network-peering-overview)" >}}{{< /figure >}}

### Paso 1: inspeccionar la VNet del hub antes del cambio

Antes de tocar nada, yo prefiero inspeccionar el recurso y dejar evidencia del estado actual. No por obsesión (bueno, quizá un poco), sino porque así comparo después contra algo real y no contra mi memoria, que no siempre es un sistema de observabilidad fiable.

Este comando consulta la VNet del hub y extrae tanto sus prefijos actuales como la propiedad `summarizedGatewayPrefixes`:

```bash
az network vnet show \
  --resource-group rg-hybrid-prod \
  --name vnet-hub-prod \
  --query "{name:name,addressSpace:addressSpace.addressPrefixes,summarizedGatewayPrefixes:summarizedGatewayPrefixes}" \
  --output json
```

Si todavía no has configurado esta funcionalidad, deberías ver algo parecido a esto:

```json
{
  "addressSpace": [
    "10.27.0.0/24"
  ],
  "name": "vnet-hub-prod",
  "summarizedGatewayPrefixes": null
}
```

Si en tu caso ya aparece una lista de CIDR, entonces el resumen ya existe en esa VNet. Ahí mi consejo es simple: no sigas en automático. Primero revisa si esos prefijos cubren exactamente lo que quieres anunciar y, sobre todo, si siguen reflejando la intención actual del diseño.

### Paso 2: configurar «summarizedGatewayPrefixes» en la VNet del hub

Aquí está el cambio importante. Según el [artículo técnico de Microsoft sobre advertised gateway prefixes](https://techcommunity.microsoft.com/t5/azure-networking-blog/advertised-gateway-prefixes-in-azure/ba-p/4550940), la configuración vive en la VNet del hub, no en cada *spoke* ni directamente en el recurso del *gateway*. A mí esto me encaja bastante: el hub es el punto donde tiene sentido expresar la intención de agregación de toda la topología.

En este ejemplo voy a resumir varios segmentos dentro de `10.27.0.0/22`. Supón que cubren estas redes reales:

- Hub: `10.27.0.0/24`
- Spoke de aplicaciones: `10.27.1.0/24`
- Spoke de datos: `10.27.2.0/24`
- Spoke de integración: `10.27.3.0/24`

Puedes actualizar la propiedad así:

```bash
az network vnet update \
  --resource-group rg-hybrid-prod \
  --name vnet-hub-prod \
  --set summarizedGatewayPrefixes='["10.27.0.0/22"]'  # Declaro el resumen en la VNet del hub, que es donde Azure espera esta intención
```

La respuesta será un JSON bastante largo con la definición completa de la VNet. Lo importante es comprobar que aparece esta propiedad con el valor esperado:

```json
"summarizedGatewayPrefixes": [
  "10.27.0.0/22"
]
```

Si necesitas más de un bloque resumido porque tu direccionamiento no cabe en una sola agregación limpia, puedes pasar varios CIDR:

```bash
az network vnet update \
  --resource-group rg-hybrid-prod \
  --name vnet-hub-prod \
  --set summarizedGatewayPrefixes='["10.27.0.0/22","10.28.0.0/20"]'  # Solo tiene sentido si ambos bloques responden a un diseño real
```

Yo aquí sería conservador. **Solo resumiría bloques que expresen una intención de diseño clara**, no un contenedor enorme para hacer desaparecer rutas incómodas de la vista. Si el resumen te queda “demasiado bonito”, sospecha un poco.

### Paso 3: verificar en Azure que la propiedad se ha aplicado

Después del cambio, vuelvo a consultar la VNet con una salida más compacta. No es la parte más glamurosa del artículo, lo sé, pero en operaciones reales este tipo de comprobación rápida evita bastantes errores tontos.

```bash
az network vnet show \
  --resource-group rg-hybrid-prod \
  --name vnet-hub-prod \
  --query "summarizedGatewayPrefixes" \
  --output tsv
```

La salida esperada debería ser esta:

```text
10.27.0.0/22
```

Si has configurado varios prefijos, verás varias líneas. Si no ves nada, yo no asumiría nada bueno: repetiría la consulta completa en JSON, revisaría que la operación se haya persistido correctamente y comprobaría la actividad reciente del recurso. A veces el problema no es de red; a veces simplemente no has dejado el recurso como creías.

{{< figure src="/images/menos-ruido-bgp-en-azure-como-resumir-prefijos-anunciados-en-un-hub-and-spoke/body-3.png" alt="Diagrama de configuración de summarizedGatewayPrefixes en la VNet del hub" caption="La propiedad summarizedGatewayPrefixes se configura en la VNet del hub, no en cada spoke." >}}{{< /figure >}}

### Paso 4: validar el efecto en las rutas anunciadas hacia «on-premises»

Aquí está la prueba de fuego. Configurar la propiedad está bien, pero lo que de verdad importa es que el vecino BGP deje de ver una colección de rutas específicas y empiece a ver el resumen esperado. La [documentación de overview](https://learn.microsoft.com/en-us/azure/virtual-network/advertised-gateway-prefixes-overview) describe precisamente ese comportamiento: sustituir múltiples prefijos individuales cubiertos por uno o varios prefijos agregados.

La validación final depende de dónde observes BGP. Si tienes acceso al router *on-premises*, ese es el mejor sitio para mirar. En un equipo Cisco IOS XE, una comprobación típica podría ser esta:

```bash
show ip bgp neighbors 192.168.100.2 received-routes | include 10.27.
```

Antes del cambio, esperarías algo de este estilo:

```text
*>i 10.27.0.0/24    192.168.100.2
*>i 10.27.1.0/24    192.168.100.2
*>i 10.27.2.0/24    192.168.100.2
*>i 10.27.3.0/24    192.168.100.2
```

Después del cambio, lo razonable es ver el resumen en lugar de las rutas individuales cubiertas:

```text
*>i 10.27.0.0/22    192.168.100.2
```

Y si existe una red en Azure fuera del resumen —por ejemplo `172.16.1.0/24`—, seguirá apareciendo como prefijo independiente. Ese comportamiento coincide con el ejemplo que Microsoft explica en su [descripción técnica de la funcionalidad](https://techcommunity.microsoft.com/t5/azure-networking-blog/advertised-gateway-prefixes-in-azure/ba-p/4550940).

Si no controlas el router *on-premises*, mi alternativa mínima sería coordinar la validación con el equipo de red y pedir una exportación de rutas recibidas antes y después. No es tan inmediato, pero sigue siendo una forma perfectamente válida de demostrar que el cambio ha tenido el efecto esperado.

### Un ejemplo mental de impacto: de 200 spokes a una tabla razonable

Imagina un hub con 200 *spokes*, cada uno con un `/24`, todos dentro de un bloque corporativo ordenado como `10.60.0.0/16`. Sin resumen, el *gateway* puede terminar anunciando cientos de prefijos individuales hacia *on-premises*. Con una agregación bien pensada, podrías reducir una gran parte de ese conjunto a uno o varios prefijos agregados, según cómo hayas repartido entornos y dominios.

Esto no solo ayuda con límites. También ayuda con la operación diaria. Cuando alguien revisa rutas en el proveedor, en el *core* *on-premises* o durante una incidencia, entiende mejor lo que está viendo. **Una tabla BGP más limpia también documenta la arquitectura**. Y esa clase de documentación viva suele envejecer bastante mejor que el típico diagrama perdido en una wiki que nadie actualiza.

{{< figure src="/images/menos-ruido-bgp-en-azure-como-resumir-prefijos-anunciados-en-un-hub-and-spoke/source-4.png" alt="Esquema de conectividad entre ExpressRoute y el gateway de Azure" caption="En ExpressRoute, reducir la cantidad de prefijos anunciados ayuda a mantener una conectividad híbrida más escalable y legible. Fuente: [learn.microsoft.com](https://learn.microsoft.com/en-us/azure/expressroute/expressroute-routing)" >}}{{< /figure >}}

### Riesgos y precauciones que yo no ignoraría

La primera precaución es bastante obvia, pero también bastante importante: no resumas bloques que incluyan espacios que no debes anunciar. Si agregas de más, *on-premises* puede asumir que Azure tiene alcance hacia rangos que en realidad no existen o no deberían usarse por esa conexión. Eso no siempre rompe algo de inmediato, pero sí te deja el terreno perfecto para un *troubleshooting* desagradable.

La segunda es organizativa. Esta funcionalidad brilla cuando el direccionamiento IP está gobernado con disciplina. Si cada equipo crea *spokes* con rangos improvisados, luego no hay resumen elegante que te salve. En mi experiencia, los *advertised gateway prefixes* son más bien el premio a una buena arquitectura de direccionamiento, no el parche de una mala.

La tercera tiene que ver con el control del cambio. Aunque la modificación sea sencilla, estás alterando lo que Azure anuncia por BGP hacia tu red corporativa. Yo la aplicaría con ventana de cambio, comparación de rutas antes y después y *rollback* preparado. No porque espere desastre, sino porque en red me gusta mucho más la tranquilidad que la épica.

Si necesitas deshacerlo, puedes dejar la lista vacía así:

```bash
az network vnet update \
  --resource-group rg-hybrid-prod \
  --name vnet-hub-prod \
  --set summarizedGatewayPrefixes='[]'  # Vaciar la lista devuelve el comportamiento al anuncio específico por prefijo
```

Tras ese *rollback*, lo esperable es que `summarizedGatewayPrefixes` aparezca como lista vacía y que el vecino BGP vuelva a recibir los prefijos específicos originales.

### Mi conclusión

Yo veo esta capacidad como una mejora pequeña en apariencia, pero muy relevante en redes híbridas grandes. No cambia la topología, no sustituye a ExpressRoute ni a VPN Gateway y, desde luego, no arregla un mal direccionamiento. Lo que sí hace es darte una forma nativa de **reducir ruido BGP sin trucos raros**, aprovechando mejor un diseño hub-and-spoke que ya tienes.

Si me preguntas por una hoja de ruta sensata, yo iría así: primero ordenar el plan IP, después comprobar qué *spokes* usan *gateway transit*, luego definir resúmenes seguros y, por último, validar el efecto desde el vecino BGP real. Ahí es donde esta funcionalidad demuestra su valor de verdad. Menos rutas. Menos fricción. Y una red bastante más fácil de operar.
