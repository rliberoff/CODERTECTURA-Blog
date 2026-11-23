---
title: Cómo llevar tus propias IP públicas a Azure Firewall en un Virtual WAN secured
  hub
date: '2026-11-23T06:24:56+00:00'
draft: true
slug: como-llevar-tus-propias-ip-publicas-a-azure-firewall-en-un-virtual-wan-secured-h
description: Te explico cómo desplegar un secured hub de Virtual WAN con Azure Firewall
  usando IP públicas propias, qué cambia en la arquitectura y cómo validarlo paso
  a paso.
categories:
- Azure
- Arquitectura de Software
- Redes
tags:
- Azure Firewall
- Virtual WAN
- Redes
- Infraestructura como código
- AVM
image: /images/como-llevar-tus-propias-ip-publicas-a-azure-firewall-en-un-virtual-wan-secured-h/cover.png
comments: true
ai:
  assisted: true
  article_type: technical
  model: gpt-5.4
  prompt_version: 2026-08-21.1
  generated_at: '2026-11-23T06:24:56+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://techcommunity.microsoft.com/t5/azure-infrastructure-blog/implement-virtual-wan-secure-hub-with-customer-owned-public-ips/ba-p/4575390
    title: Implement Virtual WAN Secure Hub with Customer-Owned Public IPs for Firewall
      using AVM
    published_date: '2026-11-21'
  - url: https://learn.microsoft.com/en-us/azure/virtual-network/virtual-network-peering-overview
    title: Azure Virtual Network Peering | Microsoft Learn
    published_date: null
---

Si trabajas con conectividad corporativa en Azure, tarde o temprano te encuentras con una necesidad bastante poco glamurosa, pero muy real: **no quieres que la IP pública del firewall te la decida el despliegue**. Quieres una IP conocida, controlada por ti, con un ciclo de vida separado, útil para listas blancas, para DNAT y, sobre todo, para no romper integraciones externas cada vez que tocas la plataforma. Justo ahí es donde me parece especialmente interesante el patrón de [secured hub de Virtual WAN con *customer-owned public IPs* para Azure Firewall](https://techcommunity.microsoft.com/t5/azure-infrastructure-blog/implement-virtual-wan-secure-hub-with-customer-owned-public-ips/ba-p/4575390): no es un simple detalle operativo, es una decisión de arquitectura.

En este artículo quiero aterrizar ese patrón sin adornos innecesarios. Voy a explicarte qué cambia frente a un enfoque más clásico, qué restricciones conviene tener presentes y cómo reproducir un despliegue de extremo a extremo con Azure CLI y Bicep, apoyándome en el patrón descrito por Microsoft. Mi idea de fondo es bastante simple: **si ya has adoptado Virtual WAN como plano de conectividad, aportar tus propias IP públicas al firewall te da mucho más control sin renunciar al modelo gestionado**.

### Antes de empezar

Para seguir este recorrido de forma reproducible, yo partiría de estos requisitos:

- Una suscripción de Azure donde puedas crear recursos de red y seguridad.
- Permisos suficientes para crear y asociar recursos de red. En la práctica, yo usaría una identidad con privilegios equivalentes a contribución sobre el grupo de recursos y capacidad para administrar red.
- [Azure CLI](https://techcommunity.microsoft.com/t5/azure-infrastructure-blog/implement-virtual-wan-secure-hub-with-customer-owned-public-ips/ba-p/4575390) instalada y autenticada. En mi ejemplo apunto a **Azure CLI 2.75 o superior**.
- Soporte para desplegar Bicep desde Azure CLI. El ejemplo usa la **Bicep CLI integrada en Azure CLI 2.75+**.
- Una región donde quieras crear el Virtual WAN hub y las IP públicas estándar estáticas.
- Tener claro que estamos hablando de **Azure Firewall en un secured virtual hub de Virtual WAN**, no del despliegue clásico dentro de una VNet hub-spoke.

Además, me parece útil tener una imagen mental del patrón hub-spoke tradicional, porque ayuda a entender por qué Virtual WAN mueve el punto de control y de enrutamiento. La documentación de [Azure Virtual Network Peering](https://learn.microsoft.com/en-us/azure/virtual-network/virtual-network-peering-overview) sigue siendo una buena referencia para ese modelo base y para capacidades como *service chaining* o el tráfico privado sobre el backbone de Microsoft.

### Qué problema resuelve exactamente este patrón

En un secured hub de Virtual WAN, Azure te ofrece un punto centralizado para conectividad, *routing* y seguridad. Tal y como explica [el artículo técnico de Microsoft sobre *customer-owned public IPs* en secure hub](https://techcommunity.microsoft.com/t5/azure-infrastructure-blog/implement-virtual-wan-secure-hub-with-customer-owned-public-ips/ba-p/4575390), esas IP públicas del firewall importan tanto para tráfico saliente como entrante. En salida, son la identidad visible frente a Internet; en entrada, son el punto de terminación para escenarios como DNAT.

La diferencia práctica es muy concreta. El modelo deja de ser «crea N IPs para el firewall» y pasa a ser «usa exactamente estas IPs públicas que yo gestiono». Y eso encaja muy bien cuando dependes de *allowlists* externas, de requisitos de cumplimiento o de una gobernanza en la que red y seguridad no quieren que el ciclo de vida de las IP quede acoplado al del firewall.

**Para mí, el valor real no está en la IP en sí, sino en desacoplar la identidad pública del despliegue del servicio gestionado.** Ese desacoplamiento reduce fricción operativa, hace los cambios más predecibles y evita una clase de sustos que normalmente solo descubres cuando un tercero te dice que ya no ve tu tráfico desde la IP esperada.

### Qué cambia frente a un hub-and-spoke clásico

Aquí merece la pena hacer una pausa, porque es fácil mezclar ambos modelos en la cabeza. En un hub-and-spoke tradicional, tú controlas la VNet hub, las subredes, el Azure Firewall, los *peerings* y el *route steering*. La propia guía de [Azure Virtual Network Peering](https://learn.microsoft.com/en-us/azure/virtual-network/virtual-network-peering-overview) insiste en capacidades como la conectividad privada entre VNets, el *service chaining* y el control del enrutamiento entre redes.

En un Virtual WAN secured hub, buena parte de esas piezas pasan a un plano gestionado. Ya no estás diseñando la VNet hub al milímetro ni colocando el firewall en `AzureFirewallSubnet` como harías en una topología clásica. Estás trabajando con un **Virtual Hub gestionado**, con políticas, asociaciones y comportamiento de enrutamiento sujetos a las reglas del servicio.

Eso tiene dos consecuencias bastante claras. La primera: ganas simplicidad operativa y un modelo más homogéneo para sedes, VPN, ExpressRoute y VNets. La segunda: pierdes parte de la libertad “artesanal” del hub clásico y tienes que aceptar las restricciones del servicio, incluidas las relativas a SKUs y asociaciones de IP. No es ni mejor ni peor por definición; simplemente es otro contrato operativo.

{{< figure src="/images/como-llevar-tus-propias-ip-publicas-a-azure-firewall-en-un-virtual-wan-secured-h/body-2.png" alt="Diagrama del flujo en un secured hub de Virtual WAN con Azure Firewall e IP públicas propias" caption="Vista simplificada del patrón: IP públicas propiedad del cliente asociadas al firewall gestionado dentro del Virtual Hub." >}}{{< /figure >}}

### Paso 1: crear las IP públicas que serán tuyas

Yo empiezo por lo más importante: las IP públicas las creo antes que el firewall. Deben ser **Standard** y **Static**, porque el patrón de *customer-owned public IPs* se basa precisamente en asociar recursos de IP pública ya existentes y estables.

Este ejemplo usa **Azure CLI 2.75** y crea dos IP públicas en West Europe dentro de un grupo de recursos dedicado:

```bash
# Azure CLI 2.75+
set -euo pipefail

SUBSCRIPTION="Contoso-Production"
RG="rg-vwan-fw-prod-we"
LOC="westeurope"
PIP1="pip-vwan-fw-prod-01"
PIP2="pip-vwan-fw-prod-02"

az login
az account set --subscription "$SUBSCRIPTION"

az group create \
  --name "$RG" \
  --location "$LOC"

az network public-ip create \
  --resource-group "$RG" \
  --name "$PIP1" \
  --location "$LOC" \
  --sku Standard \
  --allocation-method Static \
  --version IPv4 \
  --zone 1 2 3 # fijo una configuración explícita para evitar ambigüedades en un activo de perímetro

az network public-ip create \
  --resource-group "$RG" \
  --name "$PIP2" \
  --location "$LOC" \
  --sku Standard \
  --allocation-method Static \
  --version IPv4 \
  --zone 1 2 3
```

Lo que me interesa aquí no es solo que el comando termine bien, sino que las propiedades queden exactamente como espero. Si consultas los recursos, deberías obtener algo equivalente a esto:

```bash
az network public-ip show \
  --resource-group "$RG" \
  --name "$PIP1" \
  --query "{name:name,sku:sku.name,allocation:publicIPAllocationMethod,ip:ipAddress}" \
  -o json

az network public-ip show \
  --resource-group "$RG" \
  --name "$PIP2" \
  --query "{name:name,sku:sku.name,allocation:publicIPAllocationMethod,ip:ipAddress}" \
  -o json
```

Salida esperada:

```json
{
  "allocation": "Static",
  "ip": "20.31.144.18",
  "name": "pip-vwan-fw-prod-01",
  "sku": "Standard"
}
```

Y otra salida similar para la segunda IP. Si aquí ya ves una SKU o un modo de asignación distinto, yo no seguiría. Parece una tontería, pero luego esas pequeñas desviaciones son las que te hacen perder una mañana entera.

### Paso 2: desplegar Virtual WAN, Virtual Hub y Azure Firewall con patrón AVM

El [artículo de Microsoft Tech Community sobre secure hub con *customer-owned* IPs usando AVM](https://techcommunity.microsoft.com/t5/azure-infrastructure-blog/implement-virtual-wan-secure-hub-with-customer-owned-public-ips/ba-p/4575390) pone el foco precisamente en este enfoque modular. Y a mí me parece importante por una razón muy poco romántica: cuando algo tiene dependencias de red, seguridad, *routing intent* y recursos preexistentes, hacerlo “a mano” se vuelve frágil con una facilidad pasmosa.

Aquí te dejo un ejemplo en **Bicep**, centrado solo en la parte relevante del patrón: referenciar IP públicas existentes para el firewall dentro del secured hub. No pretende cubrir todas las opciones del servicio; solo enseñarte la pieza que de verdad cambia el juego.

```bicep
targetScope = 'resourceGroup'

@description('Región del despliegue. Debe coincidir con la de las IP públicas existentes.')
param location string = 'westeurope'
param virtualWanName string = 'vwan-prod-we'
param virtualHubName string = 'vhub-prod-we'
param firewallName string = 'azfw-vhub-prod-we'
param firewallPolicyName string = 'afwp-vhub-prod-we'
param publicIp1Name string = 'pip-vwan-fw-prod-01'
param publicIp2Name string = 'pip-vwan-fw-prod-02'

resource publicIp1 'Microsoft.Network/publicIPAddresses@2023-09-01' existing = {
  name: publicIp1Name
}

resource publicIp2 'Microsoft.Network/publicIPAddresses@2023-09-01' existing = {
  name: publicIp2Name
}

resource virtualWan 'Microsoft.Network/virtualWans@2023-09-01' = {
  name: virtualWanName
  location: location
  properties: {
    type: 'Standard'
    allowBranchToBranchTraffic: true
    disableVpnEncryption: false
  }
}

resource virtualHub 'Microsoft.Network/virtualHubs@2023-09-01' = {
  name: virtualHubName
  location: location
  properties: {
    addressPrefix: '10.100.0.0/23'
    virtualWan: {
      id: virtualWan.id
    }
  }
}

resource firewallPolicy 'Microsoft.Network/firewallPolicies@2023-09-01' = {
  name: firewallPolicyName
  location: location
  sku: {
    tier: 'Standard'
  }
  properties: {}
}

resource firewall 'Microsoft.Network/azureFirewalls@2023-09-01' = {
  name: firewallName
  location: location
  properties: {
    sku: {
      name: 'AZFW_Hub'
      tier: 'Standard'
    }
    hubIPAddresses: {
      publicIPs: {
        addresses: [
          {
            address: publicIp1.id // aquí está la clave: no pido IPs nuevas, enlazo recursos que ya gestiono yo
          }
          {
            address: publicIp2.id
          }
        ]
      }
    }
    virtualHub: {
      id: virtualHub.id
    }
    firewallPolicy: {
      id: firewallPolicy.id
    }
  }
}

output firewallId string = firewall.id
output publicIpResourceIds array = [
  publicIp1.id
  publicIp2.id
]
```

Y este sería el despliegue desde Azure CLI:

```bash
cat > main.bicep <<'BICEP'
// ...contenido Bicep del bloque anterior...
BICEP

az deployment group create \
  --resource-group "$RG" \
  --template-file main.bicep \
  --parameters location="$LOC"
```

Si todo va bien, verás un despliegue con `provisioningState` en `Succeeded`. Yo suelo comprobar además que el firewall realmente ha quedado desplegado como `AZFW_Hub` y asociado al Virtual Hub esperado:

```bash
az network firewall show \
  --resource-group "$RG" \
  --name "azfw-vhub-prod-we" \
  --query "{name:name,sku:sku.name,tier:sku.tier,hub:virtualHub.id}" \
  -o json
```

Salida esperada:

```json
{
  "hub": "/subscriptions/.../resourceGroups/rg-vwan-fw-prod-we/providers/Microsoft.Network/virtualHubs/vhub-prod-we",
  "name": "azfw-vhub-prod-we",
  "sku": "AZFW_Hub",
  "tier": "Standard"
}
```

### Paso 3: verificar que el firewall usa tus IP públicas

Esta es, para mí, la comprobación que de verdad importa. No basta con que el firewall exista; quiero verificar que las IP asociadas son precisamente las que yo he creado.

```bash
az network firewall show \
  --resource-group "$RG" \
  --name "azfw-vhub-prod-we" \
  --query "hubIPAddresses.publicIPs.addresses[].address" \
  -o tsv
```

Lo esperable aquí es ver dos *resource IDs* de IP pública dentro de tu grupo de recursos, apuntando a `pip-vwan-fw-prod-01` y `pip-vwan-fw-prod-02`.

Para cerrar la validación, yo suelo resolver además cada identificador y contrastar nombre, IP efectiva y SKU. Así me aseguro de que no he enlazado “algo parecido”, sino exactamente los recursos correctos:

```bash
FW_IP_IDS=$(az network firewall show \
  --resource-group "$RG" \
  --name "azfw-vhub-prod-we" \
  --query "hubIPAddresses.publicIPs.addresses[].address" \
  -o tsv)

while IFS= read -r id; do
  [ -n "$id" ] || continue
  az resource show \
    --ids "$id" \
    --query "{name:name,ip:properties.ipAddress,sku:sku.name}" \
    -o json
done <<< "$FW_IP_IDS"
```

Aquí deberías ver exactamente las dos IP públicas estáticas que creaste antes, con SKU `Standard`. Si aparece otra cosa, yo lo tomaría como una señal clara de que el patrón no se ha aplicado como esperabas.

{{< figure src="/images/como-llevar-tus-propias-ip-publicas-a-azure-firewall-en-un-virtual-wan-secured-h/body-3.png" alt="Infografía de verificación de asociación entre Azure Firewall e IP públicas existentes" caption="La validación clave tras el despliegue: confirmar que el firewall referencia exactamente los recursos de IP pública que has creado tú." >}}{{< /figure >}}

### Qué debes vigilar: restricciones y decisiones de diseño

Hay varios matices que conviene no perder de vista.

Primero, esto **no es equivalente** a desplegar Azure Firewall en una VNet propia con *peering* hacia *spokes*. En el modelo clásico, apoyado en capacidades como las que describe [Azure Virtual Network Peering](https://learn.microsoft.com/en-us/azure/virtual-network/virtual-network-peering-overview), tú defines subredes específicas, propagación de rutas y *service chaining* con mucha más granularidad. En secured hub, el servicio encapsula parte de esa complejidad.

Segundo, la SKU y el tipo de firewall importan muchísimo. El patrón del que estoy hablando se refiere al firewall de hub gestionado dentro de Virtual WAN, no al firewall VNet tradicional. Si mezclas mentalmente ambos modelos, te vas a llevar sorpresas con propiedades, asociaciones y límites. Y sí, este es uno de esos casos en los que Azure no perdona una confusión conceptual por muy razonable que te pareciera a las ocho de la mañana.

Tercero, las IP públicas deben estar preparadas para ese papel. Mi regla aquí es bastante simple: **si una IP no la has tratado como identidad estable del perímetro, no la promociones a ese rol “porque ya la tienes por ahí”**. Merece la pena considerar esas IP como activos de plataforma, con *naming*, *ownership* y trazabilidad claros.

### Cuándo lo elegiría yo y cuándo no

Yo elegiría este enfoque cuando ya tengo Virtual WAN como apuesta de conectividad y necesito estabilidad pública para salida a Internet, DNAT o dependencias con terceros. También lo elegiría cuando quiero separar responsabilidades: la plataforma despliega el secured hub, pero red conserva el control explícito de las IP públicas y de su ciclo de vida.

No lo elegiría si todavía estás en una topología pequeña, totalmente basada en hub-and-spoke clásico, y no tienes una razón operativa fuerte para asumir el modelo de Virtual WAN. En ese escenario, quizá te compense más seguir con una arquitectura tradicional y aprovechar el [*peering* de VNets](https://learn.microsoft.com/en-us/azure/virtual-network/virtual-network-peering-overview) con un control más directo del hub.

En el fondo, la decisión no va solo de red. Va de **qué piezas quieres gestionar tú y cuáles prefieres delegar al servicio**. Y esa frontera, cuando está bien elegida, simplifica mucho más que cualquier diagrama bonito.

### Mi conclusión

La posibilidad de usar *customer-owned public IPs* en Azure Firewall dentro de un Virtual WAN secured hub me parece una mejora pequeña en apariencia, pero grande en impacto. Resuelve un punto de fricción muy frecuente entre arquitectura de red, seguridad y operación: mantener una identidad pública estable sin renunciar a un hub gestionado.

Si me preguntas por una hoja de ruta sensata, yo lo haría así: primero estandarizaría el secured hub, después separaría el ciclo de vida de las IP públicas y, por último, automatizaría la asociación con un patrón AVM o con Bicep bien cerrado. Cuando haces eso, el diseño deja de ser una suma de excepciones y empieza a parecerse a una plataforma de verdad.

Y eso, en Azure, vale bastante más que una IP bonita.
