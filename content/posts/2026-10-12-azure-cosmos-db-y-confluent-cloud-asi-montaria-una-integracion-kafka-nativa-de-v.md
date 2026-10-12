---
title: 'Azure Cosmos DB y Confluent Cloud: así enfocaría una integración Kafka nativa
  de verdad'
date: '2026-10-12T06:34:01+00:00'
draft: true
slug: azure-cosmos-db-y-confluent-cloud-asi-montaria-una-integracion-kafka-nativa-de-v
description: Azure Cosmos DB estrena una experiencia nativa con Confluent Cloud que
  reduce fricción al llevar cambios operacionales a Kafka. Te cuento cómo la probaría
  de extremo a extremo.
categories:
- Azure
- Arquitectura de Software
- Inteligencia Artificial
tags:
- Azure Cosmos DB
- Confluent Cloud
- Kafka
- Arquitectura dirigida por eventos
- Integración de datos
- Change Feed
image: /images/azure-cosmos-db-y-confluent-cloud-asi-montaria-una-integracion-kafka-nativa-de-v/cover.png
comments: true
ai:
  assisted: true
  article_type: technical
  model: gpt-5.4
  prompt_version: 2026-08-21.1
  generated_at: '2026-10-12T06:34:01+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://devblogs.microsoft.com/cosmosdb/introducing-the-native-confluent-cloud-connector-experience-in-azure-cosmos-db/
    title: Introducing the Native Confluent Cloud Connector Experience in Azure Cosmos
      DB!
    published_date: '2026-10-09'
  - url: https://learn.microsoft.com/en-us/fabric/real-time-intelligence/event-streams/add-source-confluent-kafka
    title: Confluent Cloud for Apache Kafka Source in Fabric Eventstream - Microsoft
      Fabric | Microsoft Learn
    published_date: null
---

Si trabajas con arquitecturas dirigidas por eventos, seguramente ya te has encontrado con esta fricción: tus datos operacionales viven en Azure Cosmos DB, varios consumidores y *pipelines* hablan Kafka, y entre medias aparece una capa de pegamento que no aporta negocio pero sí trabajo, riesgo y bastante cansancio operativo. Justo por eso me ha parecido especialmente interesante que Azure Cosmos DB haya presentado una [experiencia nativa de conectores con Confluent Cloud](https://devblogs.microsoft.com/cosmosdb/introducing-the-native-confluent-cloud-connector-experience-in-azure-cosmos-db/). No lo veo como una simple mejora cosmética del portal. Lo veo como una señal bastante clara de hacia dónde quiere ir este tipo de integración.

Lo que realmente me interesa aquí no es el titular, sino la consecuencia práctica. Según explica el propio equipo de Cosmos DB, su [change feed ofrece un registro duradero y ordenado de cambios dentro de cada partición lógica](https://devblogs.microsoft.com/cosmosdb/introducing-the-native-confluent-cloud-connector-experience-in-azure-cosmos-db/), y eso lo convierte en una base muy natural para reaccionar a cambios operacionales, construir proyecciones o disparar flujos. Confluent Cloud, por su parte, pone la capa de *streaming* y desacoplamiento que muchos equipos ya tienen asumida como estándar. Si ambas piezas encajan mejor desde una experiencia de primera clase, tú ganas algo muy concreto: menos integración artesanal y una ruta mucho más limpia para llevar cambios de negocio al bus de eventos.

### Qué cambia de verdad con esta experiencia nativa

Mi lectura es bastante simple: antes conectar Cosmos DB con Kafka era algo “posible”; ahora empieza a parecer algo “esperable” dentro de una arquitectura moderna. Y ese matiz importa más de lo que parece. Cuando una integración pasa a ser de primera clase, normalmente mejora en tres frentes que a mí me importan mucho: descubribilidad, configuración guiada y operabilidad.

Dicho de otra forma, el valor no está solo en “poder publicar eventos”, sino en que el propio producto te acerque al camino correcto. En la publicación oficial de Cosmos DB se insiste justo en esa idea: aprovechar el change feed como base de eventos operacionales y combinarlo con Confluent Cloud como capa complementaria de *streaming*. Ese encaje es especialmente útil cuando quieres que la base de datos siga siendo tu sistema de registro, pero necesitas que los cambios viajen aguas abajo hacia consumidores desacoplados, analítica en tiempo real o procesos asíncronos.

{{< figure src="/images/azure-cosmos-db-y-confluent-cloud-asi-montaria-una-integracion-kafka-nativa-de-v/body-1.png" alt="Diagrama del flujo entre Cosmos DB, change feed y Confluent Cloud" caption="Patrón base: los cambios en Cosmos DB salen por change feed y se publican en un tópico Kafka para ser consumidos por varios servicios." >}}{{< /figure >}}

Para mí, el caso de uso más claro es este: escribes datos de negocio en Cosmos DB, el change feed expone esos cambios, el conector los publica en un tópico de Kafka en Confluent Cloud y, a partir de ahí, varios consumidores construyen vistas materializadas, alertas o automatizaciones. **No estás mezclando responsabilidades: estás separando persistencia operacional y distribución de eventos**. Y esa separación, cuando está bien hecha, suele simplificar bastante más de lo que complica.

### Antes de empezar

Si yo quisiera validar esta integración de extremo a extremo, prepararía primero un entorno mínimo pero realista:

- Una suscripción de Azure con permisos para administrar Azure Cosmos DB.
- Una cuenta de Azure Cosmos DB for NoSQL ya creada, con una base de datos y un contenedor.
- Un clúster de Confluent Cloud y una API Key con permisos sobre el tópico que vayas a usar.
- Azure CLI 2.75 o superior.
- .NET 8 SDK para generar datos de prueba en Cosmos DB.
- Acceso al portal de Azure.
- Si vas a trabajar con redes privadas o con TLS/mTLS, revisaría antes los requisitos prácticos que Microsoft documenta para [Confluent Cloud como origen en Eventstream de Fabric](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/event-streams/add-source-confluent-kafka), porque ahí aparecen restricciones muy reconocibles: accesibilidad pública o configuración adicional de red, y uso de Azure Key Vault para certificados cuando aplique.

Además, conviene no improvisar con el modelo de datos. Para este ejemplo voy a asumir esta base:

- Base de datos: `salesdb`
- Contenedor: `orders`
- Clave de partición: `/customerId`
- Tópico Kafka: `orders-changes`

No es un detalle menor. Si quieres observar bien el comportamiento del change feed, te interesa tener clara la partición lógica desde el principio. Luego vienen las sorpresas (y nadie quiere sorpresas en este tipo de prueba).

### Patrón 1: Cosmos DB como origen de eventos hacia Kafka

La pieza conceptual importante aquí es el change feed. Cada vez que insertas o actualizas un documento en Cosmos DB, ese cambio queda disponible para ser procesado de forma ordenada dentro de su partición lógica. Según la [explicación del equipo de Azure Cosmos DB](https://devblogs.microsoft.com/cosmosdb/introducing-the-native-confluent-cloud-connector-experience-in-azure-cosmos-db/), esa base ya estaba pensada precisamente para reaccionar a cambios operacionales, construir proyecciones y activar flujos directamente desde la base de datos. Lo nuevo no es la idea. Lo nuevo es que la conexión con Confluent Cloud se vuelve mucho más directa.

En la práctica, yo empezaría generando datos reales en el contenedor para tener algo verificable después en Kafka. Este ejemplo en **.NET 8** inserta dos pedidos y actualiza uno de ellos para provocar más de un evento observable en el change feed. He endurecido un poco el código frente al típico ejemplo de demo: saca credenciales de configuración, usa un tipo explícito para evitar errores tontos y fija una serialización consistente.

```csharp
using Microsoft.Azure.Cosmos;
using System.Text.Json.Serialization;

var endpoint = Environment.GetEnvironmentVariable("COSMOS_ENDPOINT")
    ?? throw new InvalidOperationException("Falta COSMOS_ENDPOINT");
var key = Environment.GetEnvironmentVariable("COSMOS_KEY")
    ?? throw new InvalidOperationException("Falta COSMOS_KEY");

var client = new CosmosClient(endpoint, key);
var container = client.GetContainer("salesdb", "orders");

var order1 = new Order(
    "order-1001",
    "cust-iberia-01",
    "Created",
    149.90m,
    "EUR",
    [new OrderItem("KB-ERG-001", 1, 149.90m)]);

var order2 = new Order(
    "order-1002",
    "cust-iberia-02",
    "Created",
    89.50m,
    "EUR",
    [new OrderItem("MS-WL-002", 1, 89.50m)]);

await container.UpsertItemAsync(order1, new PartitionKey(order1.CustomerId));
await container.UpsertItemAsync(order2, new PartitionKey(order2.CustomerId));

var updatedOrder1 = order1 with
{
    Status = "Paid" // Este cambio debería materializar un nuevo evento observable en el change feed
};

await container.UpsertItemAsync(updatedOrder1, new PartitionKey(updatedOrder1.CustomerId));

Console.WriteLine("Pedidos insertados y actualizados correctamente.");

public sealed record Order(
    [property: JsonPropertyName("id")] string Id,
    [property: JsonPropertyName("customerId")] string CustomerId,
    [property: JsonPropertyName("status")] string Status,
    [property: JsonPropertyName("total")] decimal Total,
    [property: JsonPropertyName("currency")] string Currency,
    [property: JsonPropertyName("items")] IReadOnlyList<OrderItem> Items);

public sealed record OrderItem(
    [property: JsonPropertyName("sku")] string Sku,
    [property: JsonPropertyName("quantity")] int Quantity,
    [property: JsonPropertyName("unitPrice")] decimal UnitPrice);
```

La salida esperada es esta:

```text
Pedidos insertados y actualizados correctamente.
```

Con eso ya tienes suficiente actividad como para comprobar si la integración con Kafka está viendo cambios reales y no un caso de laboratorio demasiado bonito para ser verdad.

### Cómo haría la configuración en el portal

Aquí está la novedad central. La [nueva experiencia nativa de conector en Azure Cosmos DB](https://devblogs.microsoft.com/cosmosdb/introducing-the-native-confluent-cloud-connector-experience-in-azure-cosmos-db/) apunta a que la configuración con Confluent Cloud se haga desde una experiencia integrada, reduciendo pasos manuales y mejorando la validación. La publicación no baja al detalle de cada pantalla como si fuera un tutorial paso a paso, pero la intención del producto sí me parece bastante clara.

Yo seguiría una secuencia como esta:

1. Abrir la cuenta de Azure Cosmos DB en el portal.
2. Localizar la experiencia del conector nativo con Confluent Cloud.
3. Seleccionar el contenedor `salesdb.orders` como origen.
4. Proporcionar los datos de Confluent Cloud: clúster, credenciales y tópico `orders-changes`.
5. Ejecutar la validación de conectividad y de configuración si la interfaz la ofrece.
6. Activar el flujo y observar el estado del conector.

Lo importante aquí no es memorizar clics, sino entender qué debería darte una buena experiencia guiada: validación temprana, visibilidad del origen y del destino, y menos margen para errores silenciosos de autenticación o conectividad. **Cuando el portal te ayuda a fallar pronto, te está ahorrando tiempo de diagnóstico después**. Y eso, en integraciones de eventos, vale oro.

{{< figure src="/images/azure-cosmos-db-y-confluent-cloud-asi-montaria-una-integracion-kafka-nativa-de-v/body-2.png" alt="Esquema de la configuración guiada del conector en el portal" caption="La experiencia guiada reduce errores: origen en Cosmos DB, credenciales de Confluent Cloud, validación y activación del flujo." >}}{{< /figure >}}

De hecho, si buscas un paralelo razonable, la documentación de [Confluent Cloud como fuente en Eventstream de Fabric](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/event-streams/add-source-confluent-kafka) enseña un patrón muy reconocible: seleccionar el origen, indicar endpoint y credenciales, y validar la conexión antes de seguir. No es el mismo producto, claro, pero sí me parece una pista útil de diseño. Microsoft lleva tiempo empujando hacia experiencias de *streaming* más guiadas y menos artesanales.

### Verificación: cómo comprobar que los eventos llegan a Kafka

Una vez activado el conector, yo haría una comprobación muy concreta: verificar que en el tópico aparecen los cambios correspondientes a `order-1001` y `order-1002`, y que `order-1001` tiene más de un evento si el conector está publicando tanto la creación como la actualización.

Si ya usas Confluent Cloud, puedes validarlo desde su propia interfaz o desde un consumidor estándar. Como referencia práctica, este comando con **kcat 1.7+** lee mensajes del tópico usando SASL_SSL. Lo importante aquí no es el comando en sí, sino la idea: no confíes solo en que el conector figure como “activo”; **lee el tópico y confirma el payload real**.

```bash
kcat -b pkc-abcd1.westeurope.azure.confluent.cloud:9092 \
  -X security.protocol=SASL_SSL \
  -X sasl.mechanisms=PLAIN \
  -X sasl.username="$KAFKA_API_KEY" \
  -X sasl.password="$KAFKA_API_SECRET" \
  -t orders-changes \
  -C -o beginning -e
```

La salida esperada debería incluir mensajes con los identificadores `order-1001` y `order-1002`, y al menos dos eventos para `order-1001`. Ver algo parecido a esto ya sería una señal bastante buena de que el flujo está funcionando:

```json
{"id":"order-1001","customerId":"cust-iberia-01","status":"Created","total":149.9,"currency":"EUR"}
{"id":"order-1002","customerId":"cust-iberia-02","status":"Created","total":89.5,"currency":"EUR"}
{"id":"order-1001","customerId":"cust-iberia-01","status":"Paid","total":149.9,"currency":"EUR"}
```

### Patrón 2: proyección Kafka a Cosmos DB para vistas materializadas

Aquí es donde, para mí, la historia deja de ser “conectividad” y empieza a ser arquitectura útil. Publicar eventos en Kafka está bien, pero el valor de negocio aparece cuando usas esos eventos para construir algo consumible. Por ejemplo, una vista `order-status-view` optimizada para una API o para un *dashboard*, separada del modelo transaccional original.

Yo plantearía esta proyección así: el tópico `orders-changes` alimenta un consumidor que escribe en otro contenedor de Cosmos DB, por ejemplo `salesdb.order-status-view`, con un documento por pedido. Ese documento se sobrescribe con cada cambio relevante y queda preparado para lecturas rápidas. Es una idea muy simple, pero tremendamente efectiva cuando quieres desacoplar escritura operacional y lectura optimizada.

{{< figure src="/images/azure-cosmos-db-y-confluent-cloud-asi-montaria-una-integracion-kafka-nativa-de-v/body-3.png" alt="Diagrama de una proyección desde Kafka hacia Cosmos DB" caption="Una proyección sencilla convierte eventos de pedidos en una vista materializada lista para consulta." >}}{{< /figure >}}

Este ejemplo en **.NET 8** usa `Confluent.Kafka 2.x` y `Microsoft.Azure.Cosmos 3.x` para consumir eventos y materializar la vista. No pretende sustituir un conector administrado ni convertirse mágicamente en código de producción (ojalá fuera tan fácil), pero sí te deja validar el patrón completo con un mínimo de disciplina: deserialización tipada, confirmación manual de offset y escritura idempotente mediante `UpsertItemAsync`.

```csharp
using Confluent.Kafka;
using Microsoft.Azure.Cosmos;
using System.Text.Json;
using System.Text.Json.Serialization;

var consumerConfig = new ConsumerConfig
{
    BootstrapServers = Environment.GetEnvironmentVariable("KAFKA_BOOTSTRAP_SERVERS"),
    SecurityProtocol = SecurityProtocol.SaslSsl,
    SaslMechanism = SaslMechanism.Plain,
    SaslUsername = Environment.GetEnvironmentVariable("KAFKA_API_KEY"),
    SaslPassword = Environment.GetEnvironmentVariable("KAFKA_API_SECRET"),
    GroupId = "order-status-projector",
    AutoOffsetReset = AutoOffsetReset.Earliest,
    EnableAutoCommit = false // Confirmo solo después de persistir en Cosmos DB
};

var cosmosClient = new CosmosClient(
    Environment.GetEnvironmentVariable("COSMOS_ENDPOINT")
        ?? throw new InvalidOperationException("Falta COSMOS_ENDPOINT"),
    Environment.GetEnvironmentVariable("COSMOS_KEY")
        ?? throw new InvalidOperationException("Falta COSMOS_KEY"));

var projectionContainer = cosmosClient.GetContainer("salesdb", "order-status-view");
var jsonOptions = new JsonSerializerOptions(JsonSerializerDefaults.Web);

using var consumer = new ConsumerBuilder<Ignore, string>(consumerConfig).Build();
consumer.Subscribe("orders-changes");

Console.WriteLine("Escuchando eventos de orders-changes...");

for (var i = 0; i < 3; i++)
{
    var result = consumer.Consume(TimeSpan.FromSeconds(30));
    if (result is null) continue;

    var order = JsonSerializer.Deserialize<OrderChanged>(result.Message.Value, jsonOptions)
        ?? throw new InvalidOperationException("No se pudo deserializar el evento.");

    var projection = new OrderStatusView(
        order.Id,
        order.CustomerId,
        order.Status,
        order.Total,
        result.Topic,
        DateTime.UtcNow);

    await projectionContainer.UpsertItemAsync(projection, new PartitionKey(projection.CustomerId));
    consumer.Commit(result); // Solo avanzo offset cuando la proyección ya está persistida

    Console.WriteLine($"Proyección actualizada para {projection.Id} con estado {projection.CurrentStatus}");
}

consumer.Close();

public sealed record OrderChanged(
    [property: JsonPropertyName("id")] string Id,
    [property: JsonPropertyName("customerId")] string CustomerId,
    [property: JsonPropertyName("status")] string Status,
    [property: JsonPropertyName("total")] decimal Total);

public sealed record OrderStatusView(
    [property: JsonPropertyName("id")] string Id,
    [property: JsonPropertyName("customerId")] string CustomerId,
    [property: JsonPropertyName("currentStatus")] string CurrentStatus,
    [property: JsonPropertyName("total")] decimal Total,
    [property: JsonPropertyName("lastSourceTopic")] string LastSourceTopic,
    [property: JsonPropertyName("projectedAtUtc")] DateTime ProjectedAtUtc);
```

La salida esperada sería algo así:

```text
Escuchando eventos de orders-changes...
Proyección actualizada para order-1001 con estado Created
Proyección actualizada para order-1002 con estado Created
Proyección actualizada para order-1001 con estado Paid
```

Y para comprobar el resultado final en Cosmos DB, yo lanzaría una consulta SQL sobre `order-status-view` desde Data Explorer o desde la herramienta que prefieras:

```sql
SELECT c.id, c.customerId, c.currentStatus, c.total
FROM c
WHERE c.id = "order-1001"
```

Lo que deberías ver es un documento con `currentStatus = "Paid"`. Si aparece así, ya has validado el recorrido completo: escritura operacional en Cosmos DB, publicación en Kafka y materialización de una vista optimizada de nuevo en Cosmos DB.

### Qué gano con esto frente a una integración hecha a mano

La respuesta corta, para mí, es operabilidad. Y sí, suena menos emocionante que “event-driven platform”, pero suele ser mucho más rentable. Cuando la integración está más cerca del producto, reduces scripts *ad hoc*, menos secretos dispersos, menos piezas montadas a pulso y menos puntos oscuros que solo entiende quien montó el invento original un viernes por la tarde.

También mejora la conversación entre equipos. Quien trabaja más cerca de los datos entiende Kafka y tópicos; quien vive en la aplicación entiende Cosmos DB y contenedores; la experiencia nativa ayuda a que ambos hablen sobre un flujo común sin diseñar desde cero un adaptador intermedio. **Eso no borra la complejidad del dominio, pero sí recorta la complejidad accidental**, que es la que más desgasta y menos valor aporta.

{{< figure src="/images/azure-cosmos-db-y-confluent-cloud-asi-montaria-una-integracion-kafka-nativa-de-v/body-4.png" alt="Comparativa visual entre integración manual y experiencia nativa" caption="La diferencia no es solo técnica: una integración nativa reduce complejidad accidental y mejora la operabilidad." >}}{{< /figure >}}

Y aquí está, para mí, el punto clave: una buena integración nativa no sustituye al diseño. No te evita pensar en contratos, idempotencia, evolución de eventos o semántica de consumo. Lo que sí hace es quitarte del medio una parte del trabajo más ingrato: el de construir y mantener infraestructura de transición solo para mover cambios de un sitio a otro.

### Mi conclusión

Yo veo esta novedad como una pieza muy alineada con la evolución natural de las arquitecturas modernas: bases operacionales que emiten cambios de forma fiable y plataformas de eventos que distribuyen esos cambios a muchos consumidores. La [apuesta de Azure Cosmos DB por una experiencia nativa con Confluent Cloud](https://devblogs.microsoft.com/cosmosdb/introducing-the-native-confluent-cloud-connector-experience-in-azure-cosmos-db/) encaja exactamente en ese punto de unión.

Si ya trabajas con Cosmos DB y Kafka, esto te interesa porque puede ahorrarte bastante integración artesanal. Si todavía no estás usando eventos de forma seria, también te interesa, porque te baja la barrera de entrada a un patrón muy potente: usar el dato operacional como origen de eventos y construir proyecciones aguas abajo con mucha menos fricción.

Mi recomendación es muy simple: monta una prueba pequeña, con un contenedor real, un tópico de verdad y una proyección muy concreta. En cuanto veas el flujo funcionando de extremo a extremo, lo entenderás enseguida. Esto no va solo de conectividad. Va de **convertir cambios de datos en capacidades reales de arquitectura**.
