---
title: 'Azure Managed Redis no va solo de «managed»: así automatizo el despliegue
  cuando la capacidad aprieta'
date: '2026-08-24T07:04:01+00:00'
draft: true
slug: azure-managed-redis-no-va-solo-de-managed-asi-automatizo-el-despliegue-cuando-la
description: Azure Managed Redis obliga a pensar más allá del aprovisionamiento feliz.
  Te muestro cómo automatizar reintentos, variación de SKU y autenticación moderna
  con criterio de plataforma.
categories:
- Azure
- Arquitectura de Software
- Inteligencia Artificial
tags:
- Azure Managed Redis
- Automatización
- Azure CLI
- Bicep
- Microsoft Entra ID
image: /images/azure-managed-redis-no-va-solo-de-managed-asi-automatizo-el-despliegue-cuando-la/cover.png
comments: true
ai:
  assisted: true
  article_type: technical
  model: gpt-5.4
  prompt_version: 2026-08-21.1
  generated_at: '2026-08-24T07:04:01+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://techcommunity.microsoft.com/t5/azure-paas-blog/azure-managed-redis-deployment-automation/ba-p/4547874
    title: Azure Managed Redis Deployment Automation
    published_date: '2026-08-21'
  - url: https://learn.microsoft.com/en-us/azure/redis/entra-for-authentication
    title: Use Microsoft Entra for cache authentication with Azure Managed Redis -
      Azure Managed Redis | Microsoft Learn
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/redis/how-to-scale
    title: Scale an Azure Managed Redis instance - Azure Managed Redis | Microsoft
      Learn
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/redis/overview
    title: What is Azure Managed Redis? - Azure Managed Redis | Microsoft Learn
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/redis/dotnet
    title: 'Quickstart: Use Azure Managed Redis in .NET Core'
    published_date: null
---

Cuando un servicio pasa a ser «managed», hay quien da por hecho que el problema operativo desaparece. Yo no compro esa idea. En **Azure Managed Redis**, lo realmente interesante de la nueva guía no es solo que Microsoft te gestione el motor, sino que pone sobre la mesa una realidad muy de plataforma: **qué hago cuando quiero desplegar de forma automatizada y la región o el SKU no tienen capacidad en ese momento**.

Ahí es donde, para mí, empieza la arquitectura de verdad. Porque dejas de pensar en un recurso aislado y empiezas a pensar en estrategia de aprovisionamiento, reintentos, variación controlada y seguridad desde el minuto uno. Dicho de otra forma: si el despliegue feliz era tu único caso contemplado, no tenías una automatización; tenías una esperanza con sintaxis bonita.

La referencia más útil que he visto sobre esto es la guía de [automatización de despliegue de Azure Managed Redis](https://techcommunity.microsoft.com/t5/azure-paas-blog/azure-managed-redis-deployment-automation/ba-p/4547874). La idea de fondo me parece muy sensata: si hay restricciones temporales de capacidad, no basta con lanzar una plantilla y esperar magia. A veces conviene reintentar en otra franja horaria; a veces probar otro SKU; a veces, si tu política lo permite, cambiar de región. Y si eso no lo automatizas bien, un servicio gestionado termina convertido en una colección de tickets, scripts de emergencia y despliegues a medio hacer.

### Qué cambia realmente para arquitectura

Según la [visión general de Azure Managed Redis](https://learn.microsoft.com/en-us/azure/redis/overview), estamos ante un servicio administrado basado en Redis Enterprise, pensado para escenarios de caché de baja latencia, mensajería, deduplicación o *leaderboards*. Hasta aquí, nada raro. Lo relevante es asumir que el aprovisionamiento **no siempre es instantáneo ni está garantizado al primer intento** cuando una región concreta va justa de capacidad.

Eso cambia bastante el diseño de tu automatización. Si tú habías modelado Redis como otro recurso determinista dentro del pipeline, ahora tienes que contemplar una excepción operativa perfectamente legítima: el recurso puede fallar por disponibilidad temporal aunque la plantilla, los permisos y la configuración sean correctos. Y no, en mi experiencia esto no se arregla con un `retry` ciego en CI/CD. Se arregla modelando el despliegue como un proceso con política, no como una invocación única.

Eso también obliga a separar bien los tipos de error. No es lo mismo un fallo por capacidad temporal que un error de permisos, una plantilla incorrecta o una configuración inválida. **Mezclarlo todo bajo la etiqueta de “ya reintentará el pipeline” es una receta bastante mala**. Lo razonable es reintentar solo cuando el problema es transitorio, y abortar cuando el error apunta a algo estructural.

{{< figure src="/images/azure-managed-redis-no-va-solo-de-managed-asi-automatizo-el-despliegue-cuando-la/body-1.png" alt="Diagrama de reintentos de despliegue para Azure Managed Redis" caption="Un patrón de aprovisionamiento más realista: región preferida, lista de SKUs, limpieza del intento fallido y espera aleatoria antes de reintentar." >}}{{< /figure >}}

### Antes de empezar

Si quieres reproducir lo que te enseño aquí, yo partiría de estos prerrequisitos:

- **Azure CLI 2.75 o superior** instalada y con sesión iniciada.
- **Bicep CLI** integrada en Azure CLI (`az bicep version`).
- **PowerShell 7.6.5 o superior** si quieres seguir el enfoque del script publicado en la guía de Microsoft.
- Una suscripción de Azure con permisos suficientes para crear recursos en un grupo de recursos.
- Un grupo de recursos ya creado o permisos para crearlo.
- Si vas a probar autenticación sin contraseñas, una identidad que puedas añadir como usuario de Redis, tal y como se describe en la guía de [autenticación con Microsoft Entra en Azure Managed Redis](https://learn.microsoft.com/en-us/azure/redis/entra-for-authentication).
- Si vas a conectar desde .NET, **.NET 8 SDK** y los paquetes que menciona el [quickstart de .NET para Azure Managed Redis](https://learn.microsoft.com/en-us/azure/redis/dotnet).

Yo comprobaría primero el entorno, sin inventarme heroicidades:

```bash
az version
az bicep version
pwsh --version
dotnet --version
```

Si aquí falla algo, párate. Parece obvio, pero no siempre lo hacemos (y luego le echamos la culpa a Azure, que también tiene lo suyo, pero no siempre es el culpable).

### La estrategia que yo aplicaría: región preferida, lista corta de SKUs y reintento con limpieza

La guía de [deployment automation](https://techcommunity.microsoft.com/t5/azure-paas-blog/azure-managed-redis-deployment-automation/ba-p/4547874) deja una idea operativa muy valiosa: cuando el intento falla por capacidad, hay que **eliminar el recurso fallido antes de volver a intentarlo con el mismo nombre**. Parece un detalle menor, pero no lo es en absoluto. Si no limpias ese estado intermedio, el siguiente despliegue puede tropezar con restos del anterior y el diagnóstico se vuelve confuso muy deprisa.

Yo lo traduciría a una política bastante simple:

1. Intentar primero en la región preferida del negocio.
2. Probar una lista corta y razonada de SKUs compatibles con el requisito.
3. Esperar un intervalo variable entre intentos, no un bucle agresivo.
4. Borrar el intento fallido antes de relanzar con el mismo nombre.
5. Parar cuando el recurso quede creado o cuando el error ya no sea de capacidad.

Lo importante aquí no es el *script* en sí, sino la intención. **No estoy automatizando una orden; estoy automatizando un criterio**. Y eso, en plataformas cloud, marca toda la diferencia.

### Ejemplo 1: desplegar con Bicep y dejar preparados región y SKU para la política de reintentos

Primero defino el despliegue declarativo. No voy a pegar aquí una plantilla kilométrica porque no aporta nada. Me interesa enseñarte justo la parte que conecta con el problema: parametrizar región y SKU para que el motor de reintentos pueda variarlos sin tocar el artefacto.

Guarda este archivo como `main.bicep`:

```bicep
@description('Nombre de la instancia de Azure Managed Redis')
param cacheName string = 'amr-prod-cache-01'

@description('Región de despliegue')
param location string = resourceGroup().location

@description('SKU de Azure Managed Redis')
param skuName string

resource managedRedis 'Microsoft.Cache/redisEnterprise@2024-11-01' = {
  name: cacheName
  location: location
  sku: {
    name: skuName
  }
  properties: {
    minimumTlsVersion: '1.2' // Entra solo admite conexiones SSL; fuerzo una base coherente desde el recurso
  }
}

output redisResourceId string = managedRedis.id
output redisName string = managedRedis.name
```

Puedes validarlo con:

```bash
az bicep build --file main.bicep
```

A partir de ahí, el comportamiento interesante está en el *wrapper* de automatización. El siguiente script de PowerShell 7.6.5 prueba varios SKUs, espera entre intentos y limpia el recurso si el despliegue no llega a buen puerto. Está inspirado en el enfoque de la [guía oficial de automatización](https://techcommunity.microsoft.com/t5/azure-paas-blog/azure-managed-redis-deployment-automation/ba-p/4547874), pero lo he dejado en una versión pequeña y reproducible.

```powershell
param(
    [string]$ResourceGroup = 'rg-amr-lab',
    [string]$Location = 'westeurope',
    [string]$CacheName = 'amr-prod-cache-01',
    [string[]]$SkuList = @('Balanced_B0','MemoryOptimized_M0'),
    [int]$MaxRetries = 6,
    [int]$MinWaitSeconds = 45,
    [int]$MaxWaitSeconds = 180
)

for ($attempt = 1; $attempt -le $MaxRetries; $attempt++) {
    foreach ($sku in $SkuList) {
        Write-Host "Intento $attempt con SKU $sku en $Location"

        az deployment group create `
            --resource-group $ResourceGroup `
            --template-file ./main.bicep `
            --parameters cacheName=$CacheName location=$Location skuName=$sku `
            --query properties.provisioningState -o tsv

        $deploymentSucceeded = ($LASTEXITCODE -eq 0)
        if ($deploymentSucceeded) {
            Write-Host "Despliegue completado con éxito usando SKU $sku"
            return
        }

        Write-Warning "El despliegue no se completó. Elimino el recurso para liberar el nombre antes del siguiente intento."
        az resource delete `
            --resource-group $ResourceGroup `
            --name $CacheName `
            --resource-type Microsoft.Cache/redisEnterprise `
            --latest-include-preview | Out-Null

        $wait = Get-Random -Minimum $MinWaitSeconds -Maximum ($MaxWaitSeconds + 1)
        Write-Host "Espero $wait segundos antes del siguiente intento"
        Start-Sleep -Seconds $wait
    }
}

throw 'No se pudo crear Azure Managed Redis tras agotar los reintentos configurados.'
```

Ejecútalo así:

```bash
pwsh ./Deploy-AmrWithRetry.ps1
```

Aquí el matiz importante no es PowerShell (que ya sé que no siempre levanta pasiones), sino el flujo: intento, verificación, limpieza, espera aleatoria y nuevo intento. Ese orden importa. Mucho.

### Por qué probar varios SKUs no es un parche, sino diseño operativo

La documentación sobre [escalado de Azure Managed Redis](https://learn.microsoft.com/en-us/azure/redis/how-to-scale) explica que hay varios tiers con distinto equilibrio entre memoria y vCPU: *Memory Optimized*, *Balanced* y *Compute Optimized*, además de distintos tamaños. Eso no significa que debas cambiar de SKU a la ligera, claro. Significa que, si tu requisito funcional admite varias opciones cercanas, puedes definir una **lista de SKUs aceptables** en lugar de fijarte a un único valor rígido.

A mí esto me parece especialmente útil en entornos de plataforma interna. Si una aplicación necesita una caché con una cierta horquilla de memoria y rendimiento, yo prefiero expresar la intención como política: primero intenta este SKU; si no hay capacidad, prueba este otro dentro del mismo presupuesto o con un impacto controlado. Lo contrario es acoplar tu entrega de plataforma a una decisión excesivamente cerrada, como si el proveedor siempre pudiera servir exactamente lo que pediste en ese instante.

Y aquí aparece una tensión interesante: cuanto más rígida sea tu especificación, menos margen tendrás para automatizar bien. Cuanto más explícita sea tu política de tolerancia —qué puedo variar y qué no—, más robusto será el sistema. **No es rebajar el diseño; es hacerlo más realista**.

{{< figure src="/images/azure-managed-redis-no-va-solo-de-managed-asi-automatizo-el-despliegue-cuando-la/body-2.png" alt="Comparativa visual de tiers y SKUs de Azure Managed Redis" caption="No todos los cambios de SKU son un parche: bien definidos, pueden formar parte de una política de despliegue aceptable." >}}{{< /figure >}}

### Ejemplo 2: verificar el recurso y encaminar la autenticación moderna con Microsoft Entra ID

Una vez creado el recurso, yo no me quedaría en el clásico “ya existe”. Quiero verificarlo y, sobre todo, dejar bien orientada la autenticación moderna. La documentación de [Microsoft Entra para Azure Managed Redis](https://learn.microsoft.com/en-us/azure/redis/entra-for-authentication) deja claro que Azure Managed Redis usa este modelo por defecto y que la autenticación sin contraseñas evita buena parte de los problemas de gestión de claves.

Primero, verifica el estado del recurso con Azure CLI:

```bash
az resource show \
  --resource-group rg-amr-lab \
  --name amr-prod-cache-01 \
  --resource-type Microsoft.Cache/redisEnterprise \
  --query "{name:name, location:location, type:type, id:id}" \
  -o json
```

Con eso deberías obtener un JSON con el nombre, la región, el tipo `Microsoft.Cache/redisEnterprise` y el identificador del recurso. Si además quieres completar la configuración de autenticación, la guía de [uso de Microsoft Entra ID para autenticarse en la caché](https://learn.microsoft.com/en-us/azure/redis/entra-for-authentication) describe el flujo para añadir un usuario o una identidad de servicio en la pestaña **Authentication** del portal.

{{< figure src="/images/azure-managed-redis-no-va-solo-de-managed-asi-automatizo-el-despliegue-cuando-la/source-3.png" alt="Pantalla de autenticación de Microsoft Entra en Azure Managed Redis" caption="La autenticación con Microsoft Entra es el siguiente paso lógico tras crear la instancia: menos secretos, más control operativo. Fuente: [learn.microsoft.com](https://learn.microsoft.com/en-us/azure/redis/entra-for-authentication)" >}}{{< /figure >}}

Si quieres probar una conexión real desde código, el [quickstart de .NET para Azure Managed Redis](https://learn.microsoft.com/en-us/azure/redis/dotnet) marca un camino muy razonable con `Microsoft.Azure.StackExchangeRedis`, `Azure.Identity` y `DefaultAzureCredential`. Este ejemplo está orientado a **.NET 8** y asume que tu identidad ya se ha añadido como usuario de Redis.

```bash
dotnet new console -n AmrEntraDemo
cd AmrEntraDemo
dotnet add package Microsoft.Azure.StackExchangeRedis --version 3.2.0
dotnet add package Azure.Identity --version 1.13.2
dotnet add package Microsoft.Extensions.Logging.Console --version 8.0.0
```

Y este sería el `Program.cs`:

```csharp
using Azure.Identity;
using Microsoft.Azure.StackExchangeRedis;
using Microsoft.Extensions.Logging;
using StackExchange.Redis;

var redisHost = "amr-prod-cache-01.westeurope.redis.azure.net:10000";

using var loggerFactory = LoggerFactory.Create(builder =>
{
    builder.AddSimpleConsole(options =>
    {
        options.SingleLine = true;
        options.TimestampFormat = "HH:mm:ss ";
    });
});

var credential = new DefaultAzureCredential();
var options = await ConfigurationOptions
    .Parse(redisHost)
    .ConfigureForAzureWithTokenCredentialAsync(credential); // La librería resuelve el flujo de token de Entra sin que yo tenga que reinventarlo

options.Ssl = true;
options.AbortOnConnectFail = false;

await using var connection = await ConnectionMultiplexer.ConnectAsync(options, loggerFactory);
var db = connection.GetDatabase();

const string key = "deployment:status";
await db.StringSetAsync(key, "ok");
var value = await db.StringGetAsync(key);

Console.WriteLine($"Valor leído desde Redis: {value}");
```

Ejecuta la prueba con:

```bash
dotnet run
```

Si todo está bien, deberías ver `Valor leído desde Redis: ok`. Y aquí hay un matiz importante: la guía de [autenticación con Entra](https://learn.microsoft.com/en-us/azure/redis/entra-for-authentication) recuerda que los clientes deben refrescar el token antes de que expire y reenviar `AUTH` para no romper la conexión. Justo por eso me gusta que el ejemplo de .NET apoye una librería específica para este escenario, en lugar de improvisar el flujo a mano. **Con seguridad y conectividad, improvisar suele salir caro**.

### Lo que yo no haría en un pipeline serio

Yo no dejaría toda la responsabilidad en un único paso de IaC dentro de CI/CD sin ningún contexto. Tampoco metería reintentos infinitos ni bucles cada pocos segundos. Y desde luego no asumiría que «managed» equivale a «siempre provisionable a la primera». Ese, para mí, es el error conceptual que esta guía ayuda a corregir.

Si tu organización tiene políticas estrictas de residencia de datos, quizá no puedas moverte de región, y entonces la estrategia correcta será reintentar dentro de la misma región con ventanas temporales y SKUs alternativos. Si sí puedes contemplar una región secundaria, el script puede ampliarse para incluir esa opción. Pero la clave sigue siendo la misma: la política debe estar codificada, no viviendo en la cabeza de la persona de guardia.

Y también evitaría otra tentación muy habitual: convertir el *fallback* en norma. Si siempre acabas en el SKU alternativo o siempre despliegas en una región secundaria, entonces ya no estás gestionando una excepción; estás ocultando un problema de planificación o de capacidad recurrente. Automatizar no consiste en tapar síntomas con elegancia.

{{< figure src="/images/azure-managed-redis-no-va-solo-de-managed-asi-automatizo-el-despliegue-cuando-la/body-4.png" alt="Flujo seguro de conexión desde .NET a Azure Managed Redis con Entra ID" caption="Después del aprovisionamiento, la conexión desde .NET encaja mejor con identidad moderna que con claves estáticas." >}}{{< /figure >}}

### Mi conclusión

Yo me quedo con una idea muy práctica: Azure Managed Redis no solo pide una buena decisión de servicio, sino una **buena decisión de automatización**. Lo realmente valioso de esta guía no es “Redis ahora lo lleva Azure”, sino que Microsoft reconoce abiertamente un problema real de capacidad temporal y propone una respuesta operativa razonable: reintentos controlados, cambio de SKU cuando procede, limpieza de despliegues fallidos y seguridad moderna con Microsoft Entra.

Si tú diseñas plataformas cloud, esto te afecta más de lo que parece. Porque al final el valor no está en poder crear un Redis desde el portal; el valor está en que tu plataforma sea capaz de aprovisionarlo de forma repetible, segura y resiliente incluso cuando la capacidad del proveedor no acompaña en el primer intento.

Y ahí, sinceramente, es donde yo separo el *marketing* de la arquitectura.
