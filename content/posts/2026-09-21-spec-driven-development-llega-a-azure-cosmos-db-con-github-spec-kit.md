---
title: Spec-Driven Development llega a Azure Cosmos DB con GitHub Spec Kit
date: '2026-09-21T12:06:33+00:00'
draft: true
slug: spec-driven-development-llega-a-azure-cosmos-db-con-github-spec-kit
description: Te muestro cómo convertir decisiones críticas de modelado en un flujo
  guiado por especificaciones, IA y validación real con Azure Cosmos DB.
categories:
- Azure
- .NET
- Arquitectura de Software
tags:
- Azure Cosmos DB
- GitHub Copilot
- Spec-Driven Development
- .NET
- Azure
- Arquitectura de datos
image: /images/spec-driven-development-llega-a-azure-cosmos-db-con-github-spec-kit/cover.png
comments: true
ai:
  assisted: true
  article_type: technical
  model: gpt-5.4
  prompt_version: 2026-08-21.1
  generated_at: '2026-09-21T12:06:33+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://devblogs.microsoft.com/cosmosdb/spec-driven-development-comes-to-azure-cosmos-db-the-first-database-extension-for-github-spec-kit/
    title: 'Spec-Driven Development comes to Azure Cosmos DB: The First Database Extension
      for GitHub Spec Kit'
    published_date: '2026-09-21'
  - url: https://devblogs.microsoft.com/cosmosdb/github-copilot-cli-cosmos-db-agent-kit
    title: Accelerate Your Cosmos DB Infrastructure with GitHub Copilot CLI and Azure
      Cosmos DB Agent Kit - Azure Cosmos DB Blog
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/cosmos-db/github-copilot-visual-studio-code-best-practices
    title: Best practices in GitHub Copilot for Visual Studio Code - Azure Cosmos
      DB | Microsoft Learn
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/cosmos-db/gen-ai/agent-kit
    title: Azure Cosmos DB Agent Kit - Azure Cosmos DB for NoSQL | Microsoft Learn
    published_date: null
---

Cuando una aplicación con Azure Cosmos DB sale mal, casi nunca falla por el `await` que faltaba. Suele romperse mucho antes: en la clave de partición, en cómo he modelado los documentos, en los patrones de acceso que nadie dejó por escrito o en esa consulta que parecía inocente hasta que empezó a quemar RUs como si no hubiera mañana. Por eso me parece especialmente interesante que [Spec-Driven Development llegue a Azure Cosmos DB con GitHub Spec Kit](https://devblogs.microsoft.com/cosmosdb/spec-driven-development-comes-to-azure-cosmos-db-the-first-database-extension-for-github-spec-kit/): desplaza el foco desde “que la IA escriba código” hacia **“que la IA me ayude a tomar decisiones de diseño revisables”**.

Si tú trabajas en .NET y Azure, este enfoque encaja sorprendentemente bien. Según la documentación de [Azure Cosmos DB Agent Kit](https://learn.microsoft.com/en-us/azure/cosmos-db/gen-ai/agent-kit), el valor real está en dar al asistente contexto experto sobre modelado, particionado, optimización de consultas, uso del SDK e incluso búsqueda vectorial y *full-text*. Y según las [buenas prácticas de GitHub Copilot para Azure Cosmos DB en Visual Studio Code](https://learn.microsoft.com/en-us/azure/cosmos-db/github-copilot-visual-studio-code-best-practices), ese contexto se integra directamente en el flujo del editor. En este artículo te voy a enseñar una forma bastante práctica de aterrizar todo eso: instalar el kit, redactar una especificación útil, obtener una propuesta inicial de diseño y validarla en local con el emulador y una pequeña aplicación en .NET.

### Qué cambia de verdad con este enfoque

La idea importante aquí no es “usar IA”. Eso, a estas alturas, ya lo hace medio mundo. La diferencia está en que la decisión arquitectónica deja de vivir en una conversación efímera con un chat y pasa a quedar expresada en una especificación: requisitos, operaciones principales, volumen esperado, restricciones de consistencia y límites operativos. En Cosmos DB esto importa muchísimo porque, como recuerda [el anuncio del soporte para Spec-Driven Development](https://devblogs.microsoft.com/cosmosdb/spec-driven-development-comes-to-azure-cosmos-db-the-first-database-extension-for-github-spec-kit/), elegir mal la `partition key` o ignorar los patrones de acceso afecta al coste, al rendimiento y a la fiabilidad mucho después de que el código compile sin protestar.

A mí lo que me convence es esto: **la IA deja de improvisar y empieza a razonar sobre un contrato de diseño**. Eso no elimina la revisión humana (ni debería), pero sí mejora bastante la primera propuesta y, sobre todo, convierte las decisiones en algo discutible, documentado y auditable. Y en datos, eso vale oro.

{{< figure src="/images/spec-driven-development-llega-a-azure-cosmos-db-con-github-spec-kit/body-1.png" alt="Diagrama del flujo spec-driven para Cosmos DB" caption="De la especificación al diseño y a la validación: el valor del enfoque está en cerrar el ciclo." >}}{{< /figure >}}

### Antes de empezar

Para reproducir el flujo de este artículo, yo partiría de esta base:

- **Visual Studio Code** instalado.
- **GitHub Copilot** activo en tu cuenta.
- La extensión **Azure Cosmos DB para Visual Studio Code**, que según [la documentación de buenas prácticas](https://learn.microsoft.com/en-us/azure/cosmos-db/github-copilot-visual-studio-code-best-practices) instala automáticamente el Agent Kit al conectarte a una cuenta de Cosmos DB.
- **.NET 8 SDK** instalado.
- **Azure Cosmos DB Emulator** instalado en Windows, o acceso a un entorno donde ya lo tengas disponible.
- Un conocimiento básico de Azure Cosmos DB for NoSQL.
- Si prefieres conectar contra Azure real en lugar del emulador, permisos sobre una cuenta de Cosmos DB en tu suscripción.

El resultado final que quiero que compruebes es bastante concreto:

1. Tienes una especificación funcional para una carga de trabajo real.
2. La IA te devuelve una propuesta de contenedor y `partition key` razonada.
3. Creas el contenedor en el emulador.
4. Ejecutas una aplicación .NET 8 que inserta datos y lanza consultas representativas.
5. Verificas si el modelo responde de verdad a los patrones de acceso que definiste.

### Paso 1: instalar el contexto experto para Copilot

La pieza base de todo esto es [Azure Cosmos DB Agent Kit](https://learn.microsoft.com/en-us/azure/cosmos-db/gen-ai/agent-kit), que Microsoft describe como una colección abierta de *skills* para asistentes de código compatibles con Agent Skills. Además, la documentación de [buenas prácticas en Visual Studio Code](https://learn.microsoft.com/en-us/azure/cosmos-db/github-copilot-visual-studio-code-best-practices) indica que, al conectarte a Cosmos DB mediante la extensión oficial, el kit se instala automáticamente para alimentar a GitHub Copilot con recomendaciones específicas de Cosmos DB.

Yo empezaría por asegurarme de dos cosas: que las extensiones están instaladas y que el emulador está listo para responder. Lo primero lo puedes dejar hecho desde terminal:

```bash
code --install-extension ms-azuretools.vscode-cosmosdb
code --install-extension GitHub.copilot
```

Si todo va bien, verás una salida similar a esta:

```text
Installing extensions...
Extension 'ms-azuretools.vscode-cosmosdb' was successfully installed.
Extension 'GitHub.copilot' was successfully installed.
```

Si ya las tenías instaladas, no pasa nada: VS Code te lo dirá y seguirás con tu vida. Después abre el editor, inicia sesión con tu cuenta de GitHub para Copilot y, si vas contra Azure real, con tu cuenta de Azure. Si prefieres el emulador, puedes completar toda la validación local sin depender de recursos en la nube.

### Paso 2: escribir una especificación que la IA pueda discutir

Aquí está, para mí, el paso que más diferencia marca. En vez de pedir “créame un esquema para pedidos”, yo prefiero dejar por escrito el contexto operativo. Voy a usar un ejemplo sencillo de comercio electrónico, pero lo bastante realista como para obligarnos a pensar en particionado y en lecturas por varios ejes.

Crea un archivo `specs/order-workload.md` con este contenido:

```markdown
# Especificación: carga de trabajo de pedidos

## Objetivo
Persistir pedidos de una plataforma B2C con lectura operativa en tiempo real.

## Entidad principal
Order

## Operaciones principales
1. Crear pedido desde checkout.
2. Obtener un pedido por orderId y customerId.
3. Listar últimos 20 pedidos de un cliente.
4. Listar pedidos por estado de procesamiento para un tenant.
5. Actualizar estado del pedido durante fulfillment.

## Volumen esperado
- 2 millones de pedidos al mes.
- 500 tenants.
- Picos de escritura durante campañas.

## Restricciones
- Baja latencia en lecturas del cliente.
- Evitar particiones calientes.
- Soportar crecimiento por tenant.
- El estado cambia varias veces tras la creación.

## Campos candidatos
- orderId
- tenantId
- customerId
- status
- createdAt
- totalAmount
```

Lo importante no es que el documento sea largo. Lo importante es que sea específico. Operaciones, escala, restricciones y señales claras de qué duele de verdad. **Eso le da a la IA algo que analizar; una lista de campos, por sí sola, no le da casi nada**.

Después, en el chat de Copilot dentro de VS Code, yo lanzaría un prompt deliberadamente estrecho. Nada de pedir código todavía; primero quiero decisiones de diseño:

```text
Analiza el archivo specs/order-workload.md y propón un diseño para Azure Cosmos DB for NoSQL.
Quiero:
1) documento JSON de ejemplo,
2) partition key recomendada con justificación,
3) consultas principales alineadas con las operaciones,
4) riesgos del diseño y alternativas.
No te centres en código todavía; céntrate en decisiones de modelado y coste.
```

Lo esperable es una respuesta razonada sobre modelado, `partition key`, consultas y compromisos. Y eso cuadra bastante bien con lo que [Azure Cosmos DB Agent Kit dice cubrir](https://learn.microsoft.com/en-us/azure/cosmos-db/gen-ai/agent-kit): *data modeling*, diseño de particionado, optimización de consultas y buenas prácticas del SDK.

{{< figure src="/images/spec-driven-development-llega-a-azure-cosmos-db-con-github-spec-kit/body-2.png" alt="Comparativa de claves de partición candidatas" caption="La IA puede proponer opciones, pero la elección de partition key hay que contrastarla con patrones de acceso reales." >}}{{< /figure >}}

### Mi lectura de la propuesta: qué revisaría sí o sí

Con una carga como esta, yo esperaría que la IA descarte bastante rápido `/status` o `/createdAt` como `partition key` principal, porque su cardinalidad o su distribución pueden salir mal para el patrón global. También miraría con recelo `/customerId` si un mismo cliente puede concentrar mucha actividad o si `tenantId` importa para el aislamiento lógico. Una propuesta razonable suele girar alrededor de `/tenantId` o de una clave compuesta lógica basada en el tenant y otro eje, según el patrón de acceso dominante.

Aquí entra el criterio humano, claro. La IA puede ayudarte mucho, pero **la `partition key` no se aprueba por lo bien que suene una explicación, sino por cómo encaja con tus consultas reales**. Si una de tus operaciones críticas es listar los últimos pedidos de un cliente, ya puedes ir pensando si necesitas un modelo complementario, una vista materializada o asumir el coste de determinadas consultas cruzadas. De hecho, [el anuncio de esta integración](https://devblogs.microsoft.com/cosmosdb/spec-driven-development-comes-to-azure-cosmos-db-the-first-database-extension-for-github-spec-kit/) insiste precisamente en eso: estas decisiones sobreviven muchísimo más que el código generado.

### Paso 3: levantar el emulador y crear la base de datos desde .NET 8

Ahora toca dejar de opinar y empezar a comprobar. Para la parte reproducible voy a usar **.NET 8** y el paquete **Azure.Cosmos 3.36.0 o superior** en una aplicación de consola muy pequeña.

Primero crea el proyecto e instala el SDK:

```bash
dotnet new console -n CosmosSpecDemo
dotnet add CosmosSpecDemo package Azure.Cosmos --version 3.36.0
```

Si todo va bien, verás algo parecido a esto:

```text
The template "Console App" was created successfully.
info : PackageReference for package 'Azure.Cosmos' version '3.36.0' added.
info : Restored CosmosSpecDemo.csproj.
```

Con el emulador arrancado, normalmente lo tendrás respondiendo en `https://localhost:8081/`. Sustituye `Program.cs` por este código:

```csharp
using Azure.Cosmos;

var endpoint = "https://localhost:8081/";
var key = "C2y6yDjf5/R+ob0N8A7Cgv30VRDj5Qkb+...==";

var client = new CosmosClient(endpoint, key, new CosmosClientOptions
{
    ConnectionMode = ConnectionMode.Gateway // En el emulador suele evitar problemas de conectividad local.
});

Database database = await client.CreateDatabaseIfNotExistsAsync("CommerceDb");
Container container = await database.CreateContainerIfNotExistsAsync(
    id: "Orders",
    partitionKeyPath: "/tenantId",
    throughput: 400);

var order = new
{
    id = "order-1001",
    orderId = "order-1001",
    tenantId = "tenant-es-01",
    customerId = "customer-42",
    status = "Pending",
    createdAt = DateTime.UtcNow,
    totalAmount = 149.95,
    items = new[]
    {
        new { sku = "surface-keyboard", quantity = 1, price = 149.95 }
    }
};

ItemResponse<dynamic> response = await container.UpsertItemAsync(
    item: order,
    partitionKey: new PartitionKey(order.tenantId)); // Fuerzo la PK explícitamente para validar el diseño elegido.

Console.WriteLine($"Status: {(int)response.StatusCode}");
Console.WriteLine($"RU: {response.RequestCharge:F2}");
Console.WriteLine($"ActivityId: {response.ActivityId}");
```

La salida esperada será algo de este estilo:

```text
Status: 200
RU: 5.XX
ActivityId: 00000000-0000-0000-0000-000000000000
```

El `ActivityId` será distinto en tu ejecución y el consumo exacto de RUs puede variar. Lo importante aquí es que el contenedor se cree y que el documento entre correctamente con la clave de partición que has decidido validar.

### Paso 4: validar los patrones de acceso con consultas reales

Crear el contenedor demuestra muy poco. Lo que de verdad valida el diseño es ejecutar las consultas que prometiste en la especificación. Añade este bloque al mismo `Program.cs`, justo después del `UpsertItemAsync`:

```csharp
var additionalOrders = new[]
{
    new { id = "order-1002", orderId = "order-1002", tenantId = "tenant-es-01", customerId = "customer-42", status = "Processing", createdAt = DateTime.UtcNow.AddMinutes(-10), totalAmount = 89.50 },
    new { id = "order-1003", orderId = "order-1003", tenantId = "tenant-es-01", customerId = "customer-77", status = "Pending", createdAt = DateTime.UtcNow.AddMinutes(-5), totalAmount = 210.00 },
    new { id = "order-1004", orderId = "order-1004", tenantId = "tenant-pt-02", customerId = "customer-42", status = "Shipped", createdAt = DateTime.UtcNow.AddMinutes(-2), totalAmount = 45.00 }
};

foreach (var item in additionalOrders)
{
    await container.UpsertItemAsync(item, new PartitionKey(item.tenantId));
}

var query = new QueryDefinition(
    "SELECT TOP 20 * FROM c WHERE c.tenantId = @tenantId AND c.customerId = @customerId ORDER BY c.createdAt DESC")
    .WithParameter("@tenantId", "tenant-es-01")
    .WithParameter("@customerId", "customer-42");

using FeedIterator<dynamic> iterator = container.GetItemQueryIterator<dynamic>(
    queryDefinition: query,
    requestOptions: new QueryRequestOptions
    {
        PartitionKey = new PartitionKey("tenant-es-01") // Limito la consulta a una sola partición lógica para comprobar el patrón real.
    });

while (iterator.HasMoreResults)
{
    FeedResponse<dynamic> page = await iterator.ReadNextAsync();
    Console.WriteLine($"Page RU: {page.RequestCharge:F2}");

    foreach (var item in page)
    {
        Console.WriteLine($"{item.orderId} | {item.customerId} | {item.status}");
    }
}
```

La salida esperada será parecida a esta:

```text
Page RU: X.XX
order-1001 | customer-42 | Pending
order-1002 | customer-42 | Processing
```

Aquí estás comprobando algo bastante importante: una consulta alineada con `tenantId` como `partition key` fluye de manera natural cuando el patrón de acceso está bien restringido. Si en tu especificación hubieras dejado claro que la operación crítica era “buscar pedidos por `status` en todos los tenants”, este diseño empezaría a oler regular. Y cuanto antes detectes ese olor, mejor.

{{< figure src="/images/spec-driven-development-llega-a-azure-cosmos-db-con-github-spec-kit/body-3.png" alt="Diagrama de validación con emulador y consultas .NET" caption="Validar el diseño con el emulador y consultas representativas es lo que convierte la propuesta en una decisión técnica defendible." >}}{{< /figure >}}

### Qué me llevo de esta validación

Lo interesante del flujo no es solo que Copilot ayude a redactar o a generar ejemplos. Lo potente es el ciclo completo: especifico, genero una propuesta, la discuto y la valido con datos y consultas reales. Ahí es donde un enfoque *spec-driven* encaja especialmente bien con Cosmos DB, porque te obliga a hacer explícitas decisiones que demasiadas veces se quedan implícitas hasta que ya es caro cambiarlas.

También me parece importante recordar que [Azure Cosmos DB Agent Kit](https://learn.microsoft.com/en-us/azure/cosmos-db/gen-ai/agent-kit) no sustituye la responsabilidad arquitectónica. Te da reglas, contexto experto y un punto de partida mucho mejor. Pero no conoce por arte de magia tus picos de tráfico, tus restricciones regulatorias o cómo va a crecer de verdad tu negocio. Aun así, está a años luz de pedirle a una IA generalista “hazme un modelo NoSQL” y cruzar los dedos.

### Dónde le veo el valor en equipos .NET y Azure

Si ya trabajas con GitHub Copilot en tu equipo, este enfoque puede entrar sin obligarte a cambiar media plataforma. La propia guía de [buenas prácticas para Visual Studio Code](https://learn.microsoft.com/en-us/azure/cosmos-db/github-copilot-visual-studio-code-best-practices) va exactamente en esa dirección: conectar el asistente al contexto de tu base de datos para que las sugerencias dejen de ser genéricas. Y el artículo sobre [GitHub Copilot CLI y Azure Cosmos DB Agent Kit](https://devblogs.microsoft.com/cosmosdb/github-copilot-cli-cosmos-db-agent-kit) refuerza una idea con la que yo estoy muy de acuerdo: la madurez aparece cuando pasas de generar artefactos sueltos a tener un flujo repetible y guiado.

{{< figure src="/images/spec-driven-development-llega-a-azure-cosmos-db-con-github-spec-kit/body-4.png" alt="Mapa de beneficios del enfoque para equipos" caption="El mayor beneficio para el equipo no es generar más código, sino hacer explícitas y revisables las decisiones de datos." >}}{{< /figure >}}

Además, en equipos con varias personas, la especificación cumple otra función menos vistosa pero igual de útil: ordenar la conversación técnica. En vez de discutir sobre un esquema aislado, discutes sobre requisitos, operaciones, coste esperado y compensaciones. **Eso reduce bastante el riesgo de que el diseño de datos quede secuestrado por el primer prototipo que “funcionó”** (que ya sabes cómo acaba esa película).

### Conclusión

Yo no vendería esto como una varita mágica de IA para bases de datos. Lo veo, más bien, como una mejora de proceso: llevar decisiones críticas de Azure Cosmos DB a un flujo de especificación, revisión asistida y validación ejecutable. Y en un producto donde modelado, particionado y coste están tan estrechamente conectados, eso me parece una evolución muy sensata.

Si tuviera que resumírtelo en una sola frase, sería esta: escribe primero la intención arquitectónica, deja que la IA te ayude a explorar opciones y valida pronto con consultas reales. En Cosmos DB, **ese orden importa bastante más de lo que parece**.
