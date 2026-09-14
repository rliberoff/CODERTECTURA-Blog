---
title: 'Azure App Service ya puede recibir triggers de Managed Connectors: así lo
  montaría yo'
date: '2026-09-14T11:55:45+00:00'
draft: true
slug: azure-app-service-ya-puede-recibir-triggers-de-managed-connectors-asi-montaria-y
description: Azure App Service ya aparece como destino nativo de trigger para Azure
  Managed Connectors. Te enseño cómo aprovecharlo con ASP.NET Core sin meter infraestructura
  accidental.
categories:
- Azure
- .NET
- Arquitectura de Software
tags:
- Azure App Service
- Managed Connectors
- ASP.NET Core
- Integración SaaS
- Arquitectura dirigida por eventos
image: /images/azure-app-service-ya-puede-recibir-triggers-de-managed-connectors-asi-montaria-y/cover.png
comments: true
ai:
  assisted: true
  article_type: technical
  model: gpt-5.4
  prompt_version: 2026-08-21.1
  generated_at: '2026-09-14T11:55:45+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://techcommunity.microsoft.com/t5/apps-on-azure-blog/azure-app-service-is-now-a-trigger-destination-for-azure-managed/ba-p/4555785
    title: Azure App Service is now a trigger destination for Azure Managed Connectors
    published_date: '2026-09-11'
  - url: https://learn.microsoft.com/en-us/azure/azure-functions/functions-connectors-overview
    title: Use managed connectors in Azure Functions | Microsoft Learn
    published_date: null
---

Si llevas tiempo integrando SaaS con aplicaciones propias en Azure, seguramente te has pegado con el mismo problema con el que me he pegado yo más de una vez: la lógica de negocio suele ser razonable, pero **la fontanería de autenticación, webhooks y callbacks acaba robándose el protagonismo**. Por eso me parece bastante relevante que, tal y como cuenta [el anuncio del equipo de Apps on Azure](https://techcommunity.microsoft.com/t5/apps-on-azure-blog/azure-app-service-is-now-a-trigger-destination-for-azure-managed/ba-p/4555785), Azure App Service ya pueda actuar como destino de trigger para Azure Managed Connectors.

No lo veo como una simple casilla nueva en el portal. Yo lo leo más bien como un ajuste de diseño que encaja muy bien con aplicaciones reales: APIs, backoffices y servicios internos que ya viven en App Service y que ahora pueden recibir eventos sin obligarme a montar una pieza intermedia solo para escuchar. Y eso, cuando mantienes software empresarial de verdad, importa más de lo que parece.

### Por qué creo que esto sí cambia el diseño

Hasta ahora, cuando una aplicación web quería reaccionar a eventos de Outlook, SharePoint, Teams, Dataverse o Salesforce, yo veía dos caminos típicos. El primero era meter Azure Functions como intermediario. El segundo, exponer un endpoint HTTP y resolver a mano URL, autenticación, validación y contrato de entrada. Los dos funcionan, sí, pero ninguno sale gratis.

Con Functions añades otro runtime, otra topología y otra superficie operativa. Con el endpoint HTTP genérico, en cambio, lo que añades es trabajo repetitivo: piezas de seguridad y plumbing que no aportan valor de negocio. Según [la explicación oficial de esta novedad](https://techcommunity.microsoft.com/t5/apps-on-azure-blog/azure-app-service-is-now-a-trigger-destination-for-azure-managed/ba-p/4555785), ahora App Service aparece como destino de primera clase junto a Azure Functions y al endpoint HTTP genérico. Y ahí está la gracia: ya no tengo que “simular” una integración de plataforma a base de URL pegada a mano.

**App Service deja de ser solo donde publico mi API y pasa a ser también un receptor natural de eventos SaaS.** Para una aplicación que ya está desplegada, securizada y monitorizada ahí, esto encaja francamente bien. Si además después del evento quieres invocar acciones del propio ecosistema de conectores, el patrón queda bastante limpio: entra el evento, ejecuto mi lógica y, si toca, salgo otra vez al sistema externo con una acción administrada.

{{< figure src="/images/azure-app-service-ya-puede-recibir-triggers-de-managed-connectors-asi-montaria-y/body-1.png" alt="Diagrama de arquitectura con Managed Connectors enviando eventos a Azure App Service" caption="Flujo base: el conector genera el evento, Managed Connectors lo entrega autenticado y App Service lo expone a la aplicación." >}}{{< /figure >}}

Y hay otro detalle que para mí pesa mucho: la modernización incremental. En lugar de reescribir o trocear una aplicación solo para escuchar eventos externos, puedo conservar la arquitectura que ya tengo y añadir una ruta autenticada —por ejemplo `/api/webhook`, que es justo la ruta por defecto que menciona [el anuncio](https://techcommunity.microsoft.com/t5/apps-on-azure-blog/azure-app-service-is-now-a-trigger-destination-for-azure-managed/ba-p/4555785)—. A mí esa continuidad me gusta especialmente, porque modernizar no siempre significa desmontarlo todo y empezar otra vez.

### Qué necesitas antes de tocar nada

Si yo quisiera reproducir este enfoque, partiría de algo bastante sencillo:

- Una suscripción de Azure con permisos para crear o administrar App Service y aplicaciones en Microsoft Entra.
- Una Web App existente o nueva en Azure App Service.
- [.NET 8 SDK](https://dotnet.microsoft.com/) instalado para crear la aplicación receptora.
- [Azure CLI 2.75 o superior](https://learn.microsoft.com/en-us/cli/azure/) para desplegar y consultar la Web App.
- Acceso al portal de Azure, porque el flujo descrito en el anuncio se apoya en la experiencia del portal para crear el trigger.
- Tener presente que [Managed Connectors sigue en public preview](https://techcommunity.microsoft.com/t5/apps-on-azure-blog/azure-app-service-is-now-a-trigger-destination-for-azure-managed/ba-p/4555785), así que conviene validar región, disponibilidad del conector y cualquier cambio antes de pensar en producción.

También hay un matiz importante que no conviene perder de vista. El destino en App Service simplifica la parte del callback del lado de Managed Connectors, pero **la aplicación receptora sigue necesitando una configuración explícita de autenticación**. Dicho de otro modo: la plataforma te quita bastante trabajo, pero no te exime de diseñar bien la confianza en Microsoft Entra.

### Paso 1: crear un receptor mínimo en ASP.NET Core

Yo empezaría con una API mínima, casi espartana. No hace falta levantar una aplicación enorme para validar el flujo: basta con un endpoint autenticado que reciba el `POST`, lea el payload y deje alguna traza útil para verificar que todo funciona.

```bash
dotnet new web -n ConnectorWebhookReceiver --framework net8.0
cd ConnectorWebhookReceiver
dotnet add package Microsoft.AspNetCore.Authentication.JwtBearer --version 8.0.8
```

A partir de ahí, sustituiría `Program.cs` por algo como esto:

```csharp
using System.Security.Claims;
using Microsoft.AspNetCore.Authentication.JwtBearer;

var builder = WebApplication.CreateBuilder(args);

builder.Services
    .AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.Authority = "https://login.microsoftonline.com/contoso.onmicrosoft.com/v2.0";
        options.Audience = "api://connector-webhook-receiver"; // Debe coincidir exactamente con la audiencia configurada en el trigger
        options.TokenValidationParameters.ValidTypes = new[] { "JWT", "at+jwt" };
    });

builder.Services.AddAuthorization();

var app = builder.Build();

app.UseAuthentication();
app.UseAuthorization();

app.MapPost("/api/webhook", async (HttpContext httpContext) =>
{
    using var reader = new StreamReader(httpContext.Request.Body);
    var body = await reader.ReadToEndAsync();

    var caller = httpContext.User.FindFirstValue("azp")
        ?? httpContext.User.FindFirstValue(ClaimTypes.NameIdentifier)
        ?? "unknown-caller";

    app.Logger.LogInformation(
        "Evento recibido de {Caller}. ContentType: {ContentType}. Payload: {Payload}",
        caller,
        httpContext.Request.ContentType ?? "unknown",
        body);

    return Results.Ok(new
    {
        accepted = true,
        receivedAtUtc = DateTime.UtcNow,
        caller,
        bytes = System.Text.Encoding.UTF8.GetByteCount(body)
    });
}).RequireAuthorization(); // Quiero que el código solo vea peticiones ya autenticadas

app.Run();
```

Si lo arrancas con `dotnet run`, deberías ver el típico mensaje indicando que la aplicación está escuchando en local. No tiene más misterio.

Ahora bien, aquí hay una matización importante. En [el artículo del equipo de App Service](https://techcommunity.microsoft.com/t5/apps-on-azure-blog/azure-app-service-is-now-a-trigger-destination-for-azure-managed/ba-p/4555785) recomiendan usar la autenticación integrada de App Service, la conocida *Easy Auth*, para que la validación del token ocurra en la propia plataforma antes de que la petición llegue a tu código. Yo estoy enseñando `JwtBearer` porque me parece la forma más directa de entender el contrato de extremo a extremo y de probarlo localmente sin demasiada ceremonia. **En producción, si ya usas Easy Auth, yo dejaría que App Service haga ese trabajo.**

{{< figure src="/images/azure-app-service-ya-puede-recibir-triggers-de-managed-connectors-asi-montaria-y/body-2.png" alt="Secuencia de validación del webhook autenticado en App Service" caption="La validación del token antes de entrar en el código es la pieza que hace este patrón mucho más sólido." >}}{{< /figure >}}

### Paso 2: publicar la aplicación en Azure App Service

Una vez tengas el receptor, toca desplegarlo. Si no tienes todavía la infraestructura creada, con Azure CLI puedes levantar algo básico con bastante rapidez.

```bash
az group create --name rg-connectors-demo --location westeurope
az appservice plan create --name plan-connectors-demo --resource-group rg-connectors-demo --sku B1 --is-linux
az webapp create --name app-connectors-demo-2026 --resource-group rg-connectors-demo --plan plan-connectors-demo --runtime "DOTNETCORE:8.0"
dotnet publish -c Release -o ./publish
cd publish && zip -r ../app.zip . && cd ..  # Empaqueto solo el artefacto publicado, no toda la carpeta del proyecto
az webapp deployment source config-zip --resource-group rg-connectors-demo --name app-connectors-demo-2026 --src app.zip
```

He endurecido un poco este paso respecto al “zip de todo el directorio”, porque para un despliegue reproducible yo prefiero publicar primero y comprimir después únicamente la salida final. Parece un detalle menor, pero evita subir binarios antiguos, carpetas locales o cualquier resto que no debería terminar en la Web App.

Cuando acabe el despliegue, puedes abrir `https://app-connectors-demo-2026.azurewebsites.net`. Si no has definido una ruta raíz, no esperes una home bonita (ni falta que hace). Lo importante aquí es que `/api/webhook` ya exista en App Service y esté listo para recibir tráfico autenticado.

### Paso 3: preparar la autenticación de la aplicación receptora

Según [la descripción oficial del flujo](https://techcommunity.microsoft.com/t5/apps-on-azure-blog/azure-app-service-is-now-a-trigger-destination-for-azure-managed/ba-p/4555785), al crear el trigger debes indicar cuatro elementos: la Web App de destino, la ruta del callback, la identidad administrada del Connector Namespace y la audiencia de Microsoft Entra que espera tu aplicación. Ese último punto es el que suele separar una demo feliz de un sistema que realmente funciona.

En la práctica, yo configuraría App Service Authentication para exigir autenticación con Microsoft Entra y aceptaría tokens dirigidos a la audiencia de mi API. La idea del modelo es precisamente esa: Managed Connectors obtiene un token usando la managed identity seleccionada, lo envía al callback y App Service valida la llamada antes de cederte el control.

Si quieres comprobar el estado de la autenticación de tu Web App, puedes inspeccionarlo con Azure CLI:

```bash
az webapp auth show \
  --resource-group rg-connectors-demo \
  --name app-connectors-demo-2026
```

Si ahí ves que la autenticación no está habilitada o está incompleta, todavía te falta trabajo antes de conectar el trigger. Y sí, merece la pena hacerlo bien desde el principio. Luego llegan los falsos 401, las audiencias que no coinciden y las tardes entretenidas (por llamarlas de alguna manera).

### Paso 4: crear el trigger con App Service como destino

Aquí está la novedad de verdad. En el flujo del portal, App Service ya aparece como destino nativo del trigger. Eso evita tener que usar el endpoint HTTP genérico y montar manualmente la URL del callback. Pero, sobre todo, formaliza mejor el contrato de entrega y seguridad.

Yo lo haría así:

1. Ir al portal de Managed Connectors.
2. Crear un trigger con el conector que te interese, por ejemplo Outlook o SharePoint.
3. Elegir **App Service** como destino.
4. Seleccionar la Web App `app-connectors-demo-2026`.
5. Configurar la ruta `/api/webhook`.
6. Elegir la managed identity del Connector Namespace.
7. Indicar la audiencia de Microsoft Entra que espera la aplicación.

Lo relevante no es solo que el asistente te deje guardar la configuración. Lo relevante es que, como explica [el anuncio](https://techcommunity.microsoft.com/t5/apps-on-azure-blog/azure-app-service-is-now-a-trigger-destination-for-azure-managed/ba-p/4555785), Managed Connectors persiste esos valores como parte de la definición del trigger. Ya no estoy “pegando un webhook” a mano: estoy declarando un destino de aplicación con identidad, ruta y audiencia conocidas.

{{< figure src="/images/azure-app-service-ya-puede-recibir-triggers-de-managed-connectors-asi-montaria-y/body-3.png" alt="Esquema de los campos necesarios al configurar App Service como destino del trigger" caption="Los cuatro datos clave del destino dejan de ser implícitos y pasan a formar parte de la configuración del trigger." >}}{{< /figure >}}

Y ese cambio mental me parece importante. **Esto se parece mucho más a una integración de plataforma que a un apaño HTTP bien vestido.**

### Paso 5: verificar el flujo de extremo a extremo

Cuando el trigger ya está creado, toca comprobar que el evento llega y que tu aplicación realmente lo procesa. Yo aquí no me quedaría solo con el portal. Prefiero ver trazas en App Service, porque es la forma más clara de confirmar que la llamada ha pasado por la validación y ha aterrizado en mi código.

Si has dejado el `LogInformation` del ejemplo, cuando se dispare el evento deberías encontrarte algo parecido a esto en el log stream:

```text
info: ConnectorWebhookReceiver[0]
      Evento recibido de 3d5c2f8e-9a1b-4d6f-a4c2-7d4f9a1cbb21. ContentType: application/json. Payload: {"id":"AAMk...","subject":"Pedido aprobado","from":"alerts@contoso.com"}
```

Y, si el `POST` llega correctamente al endpoint, la respuesta será un `200 OK` con un cuerpo similar a este:

```json
{
  "accepted": true,
  "receivedAtUtc": "2026-09-14T10:42:17.164Z",
  "caller": "3d5c2f8e-9a1b-4d6f-a4c2-7d4f9a1cbb21",
  "bytes": 86
}
```

Para mí, ese es el punto de validación bueno: el conector genera el evento, Managed Connectors lo entrega usando identidad administrada, App Service valida el token y la aplicación procesa la carga sin necesidad de infraestructura intermedia adicional. **Y como puedes apreciar, no hay magia.** Hay un contrato claro y una plataforma haciendo parte del trabajo pesado.

### Dónde creo que encaja mejor este patrón

Si tu aplicación ya vive en App Service y quieres reaccionar a eventos SaaS, este enfoque me parece especialmente atractivo. Lo veo muy natural en APIs de negocio, backoffices, portales internos o servicios B2B que ya están consolidados y donde meter un componente extra solo por el trigger sería arquitectura accidental. También me gusta cuando quieres centralizar despliegue, observabilidad y gobierno en una única aplicación.

Eso no significa que Azure Functions desaparezca de la conversación, ni mucho menos. La [visión general de managed connectors para Azure Functions](https://learn.microsoft.com/en-us/azure/azure-functions/functions-connectors-overview) sigue teniendo todo el sentido cuando el patrón dominante es puramente reactivo y la unidad natural de trabajo es una función. Si tu escenario es más de composición ligera y menos de aplicación web existente, yo seguiría mirando Functions con total normalidad.

{{< figure src="/images/azure-app-service-ya-puede-recibir-triggers-de-managed-connectors-asi-montaria-y/body-4.png" alt="Comparativa visual entre usar App Service y Azure Functions con Managed Connectors" caption="No es una sustitución total: App Service encaja mejor cuando la aplicación ya existe; Functions sigue brillando en escenarios muy reactivos." >}}{{< /figure >}}

Para mí, la decisión correcta no va de qué servicio “gana”. Va de evitar piezas innecesarias. Si ya tienes una aplicación robusta en App Service, poder recibir triggers ahí mismo reduce fricción, simplifica operación y te permite modernizar sin romper el paisaje técnico que ya funciona.

### Mi conclusión

Yo interpreto esta novedad como una señal de madurez en el modelo de integración de Azure. [Managed Connectors](https://techcommunity.microsoft.com/t5/apps-on-azure-blog/azure-app-service-is-now-a-trigger-destination-for-azure-managed/ba-p/4555785) deja de sentirse como algo orientado solo a Functions y pasa a encajar también con aplicaciones web reales desplegadas en App Service. Y eso, para quienes pasamos más tiempo manteniendo sistemas que dibujando arquitecturas ideales, es una mejora muy práctica.

Si me preguntas si lo usaría, mi respuesta es sí, con una condición muy simple: diseñaría bien el endpoint, la autenticación con Entra y la observabilidad desde el primer día. Porque la gran ventaja de este enfoque es que **te deja concentrarte en la lógica de negocio**, pero solo si aprovechas de verdad que la plataforma ya está resolviendo el resto.
