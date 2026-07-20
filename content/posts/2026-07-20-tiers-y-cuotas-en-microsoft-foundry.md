---
slug: tiers-y-cuotas-en-microsoft-foundry
title: "Tiers y cuotas en Microsoft Foundry: por qué tu 429 no siempre es culpa tuya"
excerpt: "Foundry ya no reparte cuota en dos niveles: ahora hay tiers que suben solos con tu consumo. Te cuento cómo funcionan, cómo consultarlos y qué haría yo antes de que el primer 429 te pille en producción."
date: 2026-07-20 00:00:00 +0200
lastmod: 2026-07-20 00:00:00 +0200
draft: false
comments: true
url: "/posts/tiers-y-cuotas-en-microsoft-foundry/"
image: /images/2026-07-20-tiers-y-cuotas-en-microsoft-foundry/cover.png
categories:
  - "Inteligencia Artificial"
  - "Azure"
  - "Arquitectura de Software"
tags:
  - "Microsoft Foundry"
  - "Azure OpenAI"
---
Hay un momento muy concreto en la vida de cualquier proyecto de IA en Azure. Llega la demo, sale bien, todo el mundo aplaude… y dos semanas después alguien escribe en el canal del equipo: «*oye, estamos recibiendo 429*». Y ahí empieza la conversación de verdad.

Porque durante mucho tiempo hemos tratado la cuota de Azure OpenAI como un trámite: despliegas, te asignan un número, y si te quedas corto rellenas un formulario. Con la llegada de los **Quota Tiers** en Microsoft Foundry, esa lógica cambia. Y creo que cambia a mejor, aunque también obliga a entender un par de cosas que antes podías ignorar sin consecuencias.

Te cuento cómo lo veo yo.

### Lo primero: la cuota no vive donde tú crees

Antes de hablar de tiers, conviene fijar dos ideas que se malinterpretan constantemente.

**Uno: la cuota no se aplica a nivel de tenant.** El nivel más alto de restricción es la **suscripción de Azure**. Si tienes cinco suscripciones, tienes cinco bolsas de cuota independientes.

**Dos: la cuota es *por región*, *por suscripción* y *por modelo o tipo de despliegue*.** Esto es más importante de lo que parece. Si `gpt-5.1` en Global Standard aparece con 1 millón de TPM y 10.000 RPM, eso significa que **cada región** donde ese modelo está disponible tiene su propia bolsa de ese tamaño, para cada una de tus suscripciones.

O sea: dentro de una misma suscripción puedes consumir bastante más TPM total del que dice la tabla, siempre que repartas recursos y despliegues entre varias regiones.

Yo he visto equipos pelearse durante días con un límite que habrían resuelto simplemente desplegando en una segunda región. No siempre es la respuesta correcta ya que existen hay implicaciones de residencia de datos y latencia, pero merece estar sobre la mesa antes de rellenar un formulario.

### Qué son los Quota Tiers y qué resuelven

Hasta ahora, Foundry ofrecía básicamente dos niveles de cuota para el modelo *pay as you go*: **Default** y **Enterprise**. Con un salto enorme entre ambos y un proceso largo para pedir aumentos. Si estabas en medio, estabas incómodo.

Los Quota Tiers sustituyen ese binario por **siete niveles**: `Free Tier` y `Tiers` del 1 a 6, siendo el `Tier 6` el de mayores cuotas. Y aquí está lo interesante:

- Tu *tier* inicial se asigna según **tu consumo actual de ese modelo** y **tu relación con Microsoft** (si tienes EA o MCA-E, arrancas más arriba).
- Las cuotas **suben automáticamente** conforme crece tu uso. Aunque esto no necesariamente es cierto para las suscripciones patrocinadas.
- Cualquier aumento de cuota que te hubieran aprobado antes **se mantiene**. Nadie baja.

Microsoft lo justifica con dos argumentos que me parecen razonables: reducir la fricción cuando una carga de trabajo escala, y crear un reparto más justo en la capacidad disponible.

Mi lectura práctica: **la cuota deja de ser un evento administrativo y pasa a ser una señal de tu propio comportamiento**. Si consumes de forma sostenida y responsable, el sistema te acompaña. Si pegas un pico brutal el día del lanzamiento, el sistema no adivina.

### Los criterios de subida de tier (y por qué importan)

El upgrade automático se basa principalmente en **tendencias de consumo a lo largo del tiempo** across Foundry Models. Si tu uso crece hasta el punto de que tu tier actual te está limitando, el sistema te sube al siguiente.

Pero hay dos factores más que conviene tener claros:

1. **Tu relación con Microsoft.** Clientes con acuerdos Enterprise (EA y MCA-E) reciben tiers más altos respecto a suscripciones patrocinadas (*sponsored*)
2. **Tu historial de pagos.** Microsoft lo considera para determinar elegibilidad de upgrade automático.

Esto último no suele aparecer en las presentaciones bonitas, pero es real. Si tu suscripción tiene historial de impagos o es una free trial, no esperes upgrades agresivos.

### Cómo consultar tu tier actual

Hoy por hoy, esto se hace por la API del plano de control. Nada de portal. Así de simple:

```bash
curl -X GET \
  "https://management.azure.com/subscriptions/00000000-0000-0000-0000-000000000000/providers/Microsoft.CognitiveServices/quotaTiers?api-version=2025-10-01-preview" \
  -H "Authorization: Bearer $(az account get-access-token --resource https://management.azure.com --query accessToken -o tsv)" \
  -H "Content-Type: application/json"
```

Y la respuesta tiene esta pinta:

```json
{
  "value": [
    {
      "id": "/subscriptions/00000000-0000-0000-0000-000000000000/providers/Microsoft.CognitiveServices/quotaTiers/default",
      "name": "default",
      "properties": {
        "assignmentDate": "2026-07-16T18:24:27.5022446Z",
        "currentTierName": "Free Tier",
        "tierUpgradeEligibilityInfo": {
          "nextTierName": "Tier 1",
          "upgradeApplicableDate": "2026-07-21T11:09:22.8500786Z",
          "upgradeAvailabilityStatus": "Available"
        },
        "tierUpgradePolicy": "OnceUpgradeIsAvailable"
      },
      "type": "Microsoft.CognitiveServices/quotaTiers"
    }
  ]
}
```

Y aquí es donde la API se vuelve genuinamente útil, porque no te dice solo dónde estás. Te dice **hacia dónde vas y cuándo**.

Desglosemos los cuatro campos que importan:

- **`currentTierName`**: tu tier actual. En este ejemplo, `Free Tier`, el punto de partida.
- **`assignmentDate`**: cuándo te asignaron ese tier. Útil para entender desde cuándo se está midiendo tu comportamiento.
- **`tierUpgradeEligibilityInfo`**: el bloque interesante. Te dice el siguiente tier (`Tier 1`), si el upgrade está disponible (`Available`) y la **fecha exacta a partir de la cual se aplica** (`upgradeApplicableDate`).
- **`tierUpgradePolicy`**: en `OnceUpgradeIsAvailable`, es decir, subirás en cuanto el upgrade esté disponible.

Fíjate en el detalle temporal de este ejemplo: asignación el 16 de julio, upgrade aplicable el 21. **Tres días** (el upgrade tarda hasta tres días *hábiles*, así que si te toca un viernes tienes que sumarle el fin de semana: en el calendario se te van cinco). No es instantáneo, pero tampoco es el proceso de semanas al que estábamos acostumbrados con el modelo antiguo.

Para mí, `upgradeApplicableDate` es el campo más accionable de toda la respuesta. Te permite planificar: si sabes que el martes que viene pasas de `Free Tier` a `Tier 1`, puedes programar la prueba de carga **después** de esa fecha en lugar de estrellarte contra un límite que estaba a punto de desaparecer solo.

Y en PowerShell, si quieres tenerlo como parte de un script de inventario:

```powershell
function Get-FoundryQuotaTier {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $SubscriptionId
    )

    $token = (az account get-access-token `
                --resource https://management.azure.com `
                --query accessToken -o tsv)

    $uri = "https://management.azure.com/subscriptions/$SubscriptionId/providers/" +
           "Microsoft.CognitiveServices/quotaTiers?api-version=2025-10-01-preview"

    Invoke-RestMethod -Method Get -Uri $uri `
        -Headers @{ Authorization = "Bearer $token" } `
        -ContentType 'application/json'
}

# Recorre todas tus suscripciones y te dice en qué tier está cada una
az account list --query "[].id" -o tsv | ForEach-Object {
    $props = (Get-FoundryQuotaTier -SubscriptionId $_).value[0].properties

    [PSCustomObject]@{
        Subscription  = $_
        TierActual    = $props.currentTierName
        SiguienteTier = $props.tierUpgradeEligibilityInfo.nextTierName
        Disponible    = $props.tierUpgradeEligibilityInfo.upgradeAvailabilityStatus
        AplicableDesde = $props.tierUpgradeEligibilityInfo.upgradeApplicableDate
        Politica      = $props.tierUpgradePolicy
    }
} | Format-Table -AutoSize
```

Ese último bucle es, para mí, el tipo de cosa que debería estar en el repositorio de plataforma desde el día uno. No porque sea sofisticado, sino porque **saber en qué tier estás antes de diseñar la arquitectura te ahorra rediseños**.

### Un vistazo al Tier 1 para calibrar expectativas

No voy a copiar la tabla entera (para eso está [la documentación](https://learn.microsoft.com/en-us/azure/foundry/openai/quotas-limits)) pero sí quiero que veas algunos números del `Tier 1`, porque ayudan a poner los pies en el suelo:

| Modelo | Tipo de despliegue | RPM | TPM |
| --- | --- | --- | --- |
| `gpt-5` | GlobalStandard | 10.000 | 1.000.000 |
| `gpt-5` | DataZoneStandard | 3.000 | 300.000 |
| `gpt-5-mini` | GlobalStandard | 1.000 | 1.000.000 |
| `gpt-5-nano` | GlobalStandard | 5.000 | 2.000.000 |
| `gpt-5.1` | GlobalStandard | 10.000 | 1.000.000 |
| `gpt-5.1` | DataZoneStandard | 3.000 | 300.000 |
| `gpt-5.1-codex` | GlobalStandard | 1.000 | 1.000.000 |
| `gpt-5.1-codex` | DataZoneStandard | 3.000 | 300.000 |
| `model-router` | GlobalStandard | 1.000 | 1.000.000 |
| `model-router` | DataZoneStandard | 300 | 300.000 |
| `gpt-image-2` | GlobalStandard | 6 | — |

Fíjate en dos cosas:

**Primera: la diferencia entre GlobalStandard y DataZoneStandard es brutal.** En `gpt-5.1` hablamos de 10.000 RPM frente a 3.000, y de 1.000.000 de TPM frente a 300.000. Un factor de más de tres en ambos ejes. Si tu requisito de residencia de datos te obliga a Data Zone, tienes que presupuestar cuota con otra cabeza desde el principio. Esto no es un detalle de última hora: es una decisión de arquitectura con impacto directo en capacidad.

**Segunda: los modelos de imagen juegan en otra liga.** `gpt-image-2` en Global Standard son **6 peticiones por minuto**. Seis. Si tu producto genera imágenes bajo demanda de usuario, ese número debería estar en la primera diapositiva de tu diseño, no en la retrospectiva del incidente.

### Los límites que no son cuota (y que también te van a morder)

Aparte de TPM y RPM, hay una lista de límites duros que conviene tener presente. Estos son los que yo veo fallar con más frecuencia en proyectos reales:

- **30 recursos de Azure OpenAI** por región y suscripción.
- **32 despliegues estándar** máximo por recurso.
- **10 despliegues** de modelos fine-tuned.
- **2.048 inputs** máximo en un array de `/embeddings`, con un tope de **300.000 tokens** sumando todos.
- **2.048 mensajes** máximo en `/chat/completions`.
- **128 funciones** y **128 tools** por petición de chat completions.
- **1.048.576 caracteres** de límite por mensaje, y **20 MB** para mensajes con ficheros de audio.
- **10 headers personalizados** por petición.

Ese último merece un comentario aparte, porque es de los que aparecen de la nada. Las APIs actuales permiten hasta 10 headers custom; si te pasas, recibes un **HTTP 431** y no hay solución más allá de reducir headers. Y hay un aviso claro en la documentación: en futuras versiones de la API **dejarán de propagarse los headers personalizados**. Si tu arquitectura de trazabilidad depende de meter contexto en headers hacia Foundry, ve buscando alternativa ahora.

### Los usage tiers son otra cosa (y se confunden constantemente)

Aquí es donde mucha gente se lía, así que lo separo con claridad.

- **Quota tiers** → cuánto puedes pedir (TPM/RPM asignados).
- **Usage tiers** → hasta dónde puedes consumir **manteniendo latencia predecible**.

Los usage tiers definen un volumen mensual por modelo, contando **todos los tokens consumidos en todos los despliegues, en todas las suscripciones, en todas las regiones de un tenant**. Algunos ejemplos:

| Modelo | Usage tier mensual |
| --- | --- |
| `gpt-5` | 32.000 millones de tokens |
| `gpt-5-mini` | 160.000 millones |
| `gpt-5-nano` | 800.000 millones |
| `gpt-5-chat` | 32.000 millones |

Y aquí un apunte que conviene tener presente al leer la documentación: **la tabla oficial de usage tiers todavía no recoge las familias posteriores a `gpt-5`**. Si estás desplegando `gpt-5.1` o superior, no vas a encontrar tu número ahí. Yo asumiría el valor de `gpt-5` como referencia de orden de magnitud mientras Microsoft actualiza la tabla, pero sin tratarlo como un compromiso.

¿Qué pasa si los superas? No te cortan el servicio. Pasa algo más sutil y, en cierto modo, más molesto: **tu latencia se vuelve impredecible**. La documentación es explícita en que puede llegar a ser **más del doble** de lo que ves operando dentro de tu tier, especialmente con tráfico sostenido alto o muy *bursty*.

Y ojo, esto aplica solo a despliegues Standard, Data Zone Standard y Global Standard. **No aplica a global batch ni a provisioned throughput.**

### El 429 que aparece aunque «vas por debajo de la cuota»

Este es de los que generan tickets largos y frustración genuina.

Puedes recibir **429 (Too Many Requests)** aunque tus métricas de tokens parezcan estar por debajo del límite. No es un bug ni una conspiración: tiene que ver con cómo se evalúa el rate limiting en ventanas cortas frente a las métricas agregadas que tú ves.

Si te encuentras en esa situación, lo que yo haría en orden:

1. **Reintentos con backoff exponencial.** No es opcional. Es la línea base.
2. **Subir la carga gradualmente.** Nada de pasar de 0 a producción completa en una tarde.
3. **Probar distintos patrones de subida de carga.** Lo que aguanta a ritmo constante se rompe a picos.
4. **Mover cuota entre despliegues** si tienes bolsas infrautilizadas.
5. **Plantear PTU** si el workload es crítico en latencia o volumen.

Sobre ese último punto quiero ser claro, porque creo que se subestima: **Provisioned Throughput Units no es simplemente «cuota cara»**. Es recursos dedicados, capacidad garantizada y latencia predecible incluso a escala. Si tienes una aplicación de misión crítica donde un pico de latencia es un incidente de negocio, no estás eligiendo entre Standard y PTU por precio. Estás eligiendo entre riesgo y previsibilidad.

### Batch: una bolsa distinta, con reglas distintas

El batch merece su propio párrafo porque **la cuota se mide en tokens encolados**, no en TPM. Cuando envías un fichero, se cuentan sus tokens y esos tokens **siguen contando contra tu límite hasta que el job llega a un estado terminal**.

Esto tiene una consecuencia práctica muy concreta: si encolas varios ficheros grandes y uno se queda atascado, estás bloqueando capacidad que creías tener libre.

Para `gpt-5.1` en global batch los números son: **5B** de tokens encolados con Enterprise/MCA-E, **200M** por defecto, **50M** con suscripción de tarjeta mensual y **90K** con MSDN.

Los límites de fichero:

- **500 ficheros** de entrada sin expiración; **10.000** con expiración configurada.
- **200 MB** por fichero (**1 GB** usando *Bring Your Own Storage*).
- **100.000 peticiones** máximo por fichero.

Y las cuotas de tokens encolados varían muchísimo según tu tipo de acuerdo. Para `gpt-5` en global batch: **5B** con Enterprise/MCA-E, **200M** por defecto, **50M** con tarjeta de crédito mensual, **90K** con MSDN. La diferencia entre Enterprise y una suscripción MSDN es de casi cinco órdenes de magnitud. Vale la pena saberlo **antes** de prometer un procesamiento masivo.

Un truco útil: si los límites de fichero de batch te aprietan, usar **Batch con Azure Blob Storage** los elimina.

### Cómo pedir más cuota sin que te la denieguen

El formulario existe y funciona: [aka.ms/oai/stuquotarequest](https://aka.ms/oai/stuquotarequest). Cubre Foundry Models vendidos por Azure, modelos de Azure OpenAI y modelos de Anthropic. Los modelos de partners y comunidad, salvo Anthropic, **no admiten aumento de cuota**.

Pero hay una frase en la documentación que merece atención especial, porque es la que decide si te aprueban o no:

> Las solicitudes se procesan en el orden en que se reciben, y **la prioridad va a clientes que usan activamente su asignación de cuota actual**. Las peticiones que no cumplan esta condición pueden ser denegadas.

Traducido: si pides diez veces más cuota mientras usas el 8% de la que ya tienes, prepárate para un «no». Y me parece justo, sinceramente. La capacidad es finita y acaparar «por si acaso» es exactamente lo que rompe el sistema para todos.

Mi recomendación: **consume tu cuota actual de forma visible antes de pedir más**. Y cuando pidas, ten a mano el dato de consumo real, no una proyección optimista de comercial.

Si además aprueban tu petición, no cambias de tier: **te mantienes en el mismo tier con más cuota asignada**. Son dos ejes independientes.

### Lo que yo dejaría montado desde el día uno

Si mañana tuviera que arrancar una plataforma de IA sobre Foundry, esto es lo mínimo que dejaría hecho antes de la primera línea de negocio:

1. **Un inventario automatizado de tier y cuota** por suscripción y región. El script de PowerShell de arriba es suficiente para empezar.
2. **Retry con backoff exponencial** en toda llamada, sin excepciones y sin «ya lo añadimos luego».
3. **Métricas de 429 separadas de métricas de error.** Un 429 no es un fallo de la aplicación, es una señal de capacidad. Mezclarlos te ciega.
4. **Revisión periódica de `upgradeApplicableDate`.** Saber cuándo te suben de tier es información de planificación, no un dato de curiosidad.
5. **Un mapa de qué modelo va en qué tipo de despliegue**, con la cuota asociada anotada al lado. Especialmente si hay Data Zone de por medio.
6. **Alertas de Cost Management**, no cuota usada como freno de gasto. Herramienta correcta para el trabajo correcto.

No es glamuroso. Ninguna de estas seis cosas te va a servir para una demo. Pero son exactamente las que separan un proyecto que escala de uno que se pasa el trimestre apagando fuegos.

### Mi conclusión

Los Quota Tiers me parecen un buen cambio. Sustituyen un modelo binario y burocrático por algo progresivo que crece contigo, y eliminan bastante fricción para quien está escalando de verdad. Sin embargo, también me parecen elitistas, y pueden ser restrictivos para personas que están comenzando a usar los modelos de OpenAI en Azure, o para organizaciones que no tienen un historial de facturación importante con Microsoft y son incapaces (en ese momento histórico) de pagar por relaciones que les den acceso a *tiers* más altos.

Pero ojo con la trampa mental: **que la cuota suba sola no significa que puedas dejar de pensar en ella**. Sigues necesitando entender que la cuota es por región y suscripción, que Data Zone cuesta capacidad, que los usage tiers hablan de latencia y no de bloqueo, y que el 429 puede aparecer aunque tus gráficas digan que vas holgado.

Y hay una asimetría que creo que resume todo esto: la subida de tier es automática, pero **el diseño de tu arquitectura no lo es**. Foundry te va a acompañar cuando crezcas. Lo que no va a hacer es rediseñarte la aplicación cuando descubras, en producción, que `gpt-image-2` te daba seis peticiones por minuto.

Eso te toca a ti. Y mejor antes que después.
