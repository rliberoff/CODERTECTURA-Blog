---
title: 'Azure Cosmos DB Emulator: el camino más sensato de local a CI'
date: '2026-10-26T06:38:40+00:00'
draft: false
slug: azure-cosmos-db-emulator-el-camino-mas-sensato-de-local-a-ci
description: Te enseño cómo usar Azure Cosmos DB Emulator en Docker, desde tu portátil
  hasta GitHub Actions, para tener pruebas de integración .NET más fiables.
categories:
- Azure
- .NET
- Arquitectura de Software
tags:
- Azure Cosmos DB
- .NET
- Pruebas de integración
- GitHub Actions
- Docker
image: /images/azure-cosmos-db-emulator-el-camino-mas-sensato-de-local-a-ci/cover.png
comments: true
ai:
  assisted: true
  article_type: technical
  model: gpt-5.4
  prompt_version: 2026-08-21.1
  generated_at: '2026-10-26T06:38:40+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://devblogs.microsoft.com/cosmosdb/from-local-development-to-ci-workflows-with-the-azure-cosmos-db-emulator/
    title: From Local Development to CI Workflows with the Azure Cosmos DB Emulator
    published_date: '2026-10-23'
  - url: https://devblogs.microsoft.com/cosmosdb/code-with-cosmos/
    title: 'Code with Cosmos: Build a Production-Ready AI App in Four Episodes'
    published_date: '2026-10-23'
  - url: https://github.com/Azure/azure-cosmos-db-emulator-docker/issues/347
    title: '[vNext] QueryRequestOptions.MaxItemCount is ignored for partition-scoped
      ordered queries · Issue #347 · Azure/azure-cosmos-db-emulator-docker · GitHub'
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/cosmos-db/emulator-linux
    title: Linux-based emulator - vNext - Azure Cosmos DB | Microsoft Learn
    published_date: null
---

Si trabajas con una API que persiste datos, hay un momento en el que el test unitario deja de darte paz mental. Puedes comprobar que el controlador devuelve 200, sí, pero eso no te asegura que la escritura haya llegado a almacenamiento, que la lectura posterior recupere el documento correcto o que una actualización concurrente falle exactamente como esperas. Justo por eso me parece tan interesante el enfoque que plantea [Azure Cosmos DB Emulator para pasar de desarrollo local a CI](https://devblogs.microsoft.com/cosmosdb/from-local-development-to-ci-workflows-with-the-azure-cosmos-db-emulator/): usar en local y en pipeline el mismo SDK y una superficie de comportamiento muy parecida a producción, sin depender de una cuenta compartida en la nube para cada ejecución.

Mi tesis aquí es muy simple: para un equipo .NET, el emulador de Azure Cosmos DB en Docker es una de las formas más limpias de tener pruebas de integración reproducibles, rápidas y razonablemente fieles al mundo real. No sustituye a todas las validaciones contra un entorno real en Azure, pero sí elimina una cantidad enorme de fricción en el día a día.

### Antes de empezar

Para reproducir el flujo de este artículo, yo partiría de estos requisitos:

- **.NET 10 SDK** instalado.
- **Docker Desktop** operativo en tu máquina.
- Un proyecto de test con **xUnit**.
- El paquete **Microsoft.Azure.Cosmos 3.61.0** para acceder al SDK de Cosmos DB.
- Si quieres llevarlo a pipeline, un repositorio en **GitHub** con Actions habilitado.

También conviene tener claros los límites desde el principio, para no pedirle al emulador lo que no promete. Según la [documentación oficial del emulador Linux vNext](https://learn.microsoft.com/en-us/azure/cosmos-db/emulator-linux), funciona como contenedor Docker, está centrado en la **API for NoSQL**, usa **gateway mode** y actualmente ofrece un **subconjunto de características**, no todas las capacidades reales. Por ejemplo, la documentación indica que **no aplica autenticación actualmente**.

Esto último simplifica muchísimo las pruebas locales, pero tiene una consecuencia importante: **que tus tests pasen en el emulador no significa que toda tu integración con Cosmos DB en Azure esté validada**. Es decir, te ofrece la capacidad de verificar el correcto funcionamiento de los aspectos de persistencia, particionado y comportamiento del SDK; pero no te garantiza la veracidad en la operatividad de la seguridad, identidad y ciertas capacidades avanzadas.

{{< figure src="/images/azure-cosmos-db-emulator-el-camino-mas-sensato-de-local-a-ci/body-1.png" alt="Diagrama del flujo de desarrollo local a CI con Cosmos DB Emulator" caption="El mismo patrón de pruebas puede vivir en el portátil y en el pipeline con muy pocas diferencias." >}}{{< /figure >}}

### Por qué prefiero el emulador frente a una base compartida en Azure

La alternativa habitual en muchos equipos consiste en mantener una cuenta de desarrollo en Azure Cosmos DB y lanzar allí las pruebas de integración, pero tiene varios costes que se van acumulando sin hacer mucho ruido: dependencia de red, datos sucios entre ejecuciones, credenciales repartidas por demasiados sitios, latencia innecesaria y un coste económico que, aunque no siempre sea dramático, existe. Ciertamente existen casos o proyectos donde es inevitable usar una instancia real de Cosmos DB, pero para en mi experiencia para la gran mayoría de proyectos este emulador es más que suficiente para el día a día.

Con el emulador, el flujo cambia bastante. Levantas un contenedor local, apuntas tu aplicación .NET al endpoint del emulador y ejecutas las mismas operaciones que harías contra Cosmos DB usando el mismo SDK. Tal y como explica [el artículo del equipo de Cosmos DB](https://devblogs.microsoft.com/cosmosdb/from-local-development-to-ci-workflows-with-the-azure-cosmos-db-emulator/), la idea es validar el recorrido real de los datos: escribir, leer y comprobar que la siguiente respuesta refleja el estado persistido.

Como en otros artículos, lo interesante de este enfoque es que minimiza aun más el clásico «funciona en mi máquina», y acerca **mi máquina y la del pipeline mucho más entre sí**. Y ese puente entre portátil y CI vale oro, porque reduce diferencias invisibles, quita excusas y hace que los fallos sean bastante más diagnósticos. A parte de que disminuye la separación entre entornos que muchas veces ensucia el código: el típico flag de si estoy trabajando en local/desarrollo o ya el código debe operar en su formulación para la nube.

### Levantar Azure Cosmos DB Emulator en Docker

La [documentación del emulador Linux](https://learn.microsoft.com/en-us/azure/cosmos-db/emulator-linux) indica la imagen y los puertos principales: `8081` para el gateway, `1234` para Data Explorer y `8080` para las *health probes*.

```bash
docker pull mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:vnext-latest

docker run -d \
  --name cosmosdb-emulator \
  -p 8081:8081 \
  -p 8080:8080 \
  -p 1234:1234 \
  mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:vnext-latest
```

La salida esperada tras `docker run -d` es el **id del contenedor** en una línea, algo parecido a esto:

```text
7f3f6c9d8c2b1a4e5d6f7890abc1234567890def1234567890abcdef12345678
```

A partir de ahí, yo no sigo hasta verificar que realmente está listo. Y aquí merece la pena ser un poco maniático (yo lo soy… bastante 🫣): que el contenedor esté arrancado no significa que ya acepte peticiones correctamente. La propia [documentación de Microsoft Learn](https://learn.microsoft.com/en-us/azure/cosmos-db/emulator-linux) recomienda usar el *health probe* primero para estar seguros.

```bash
curl -s http://localhost:8080/alive
curl -s http://localhost:8080/ready
```

En la práctica, la comprobación que de verdad me importa es `/ready`. Si ese endpoint responde bien, ya tengo una señal razonable de que puedo lanzar pruebas. Y si abres `http://localhost:1234`, deberías poder entrar en Data Explorer unos segundos después del arranque.

### Conectar una app .NET 10 al emulador y preparar el contenedor

Aquí viene la parte interesante de verdad: usar el SDK de Cosmos desde una prueba de integración. Voy a asumir un proyecto de test xUnit en .NET 10 con `Microsoft.Azure.Cosmos` **3.61.0**.

Lo primero que hago es crear un fixture que inicialice la base de datos y el contenedor una sola vez. He endurecido un poco el ejemplo para que falle antes y mejor si algo va mal, y para que el ciclo de vida sea más limpio en ejecución repetida.

```csharp
using Microsoft.Azure.Cosmos;
using Xunit;

public sealed class CosmosFixture : IAsyncLifetime
{
    public CosmosClient Client { get; private set; } = default!;
    public Container Container { get; private set; } = default!;

    private const string Endpoint = "http://localhost:8081";
    private const string DatabaseId = "app-test-db";
    private const string ContainerId = "orders";

    public async Task InitializeAsync()
    {
        var clientOptions = new CosmosClientOptions
        {
            ConnectionMode = ConnectionMode.Gateway // El emulador Linux vNext solo soporta gateway mode
        };

        Client = new CosmosClient(
            accountEndpoint: Endpoint,
            authKeyOrResourceToken: string.Empty, // El emulador vNext no aplica autenticación actualmente
            clientOptions: clientOptions);

        DatabaseResponse databaseResponse = await Client.CreateDatabaseIfNotExistsAsync(DatabaseId);
        ContainerResponse containerResponse = await databaseResponse.Database.CreateContainerIfNotExistsAsync(
            new ContainerProperties(ContainerId, partitionKeyPath: "/customerId"));

        Container = containerResponse.Container;
    }

    public async Task DisposeAsync()
    {
        if (Client is not null)
        {
            await Client.GetDatabase(DatabaseId).DeleteAsync();
            Client.Dispose();
        }
    }
}

[CollectionDefinition("cosmos")]
public sealed class CosmosCollection : ICollectionFixture<CosmosFixture>
{
}
```

Cuando esta inicialización funciona, la señal verificable es bastante sencilla: la prueba no falla al crear la base y el contenedor, y en Data Explorer verás `app-test-db` con el contenedor `orders`.

{{< figure src="/images/azure-cosmos-db-emulator-el-camino-mas-sensato-de-local-a-ci/body-2.png" alt="Secuencia de arranque del emulador y creación de base de datos" caption="Yo siempre verifico primero la disponibilidad del emulador antes de crear base de datos y contenedor." >}}{{< /figure >}}

Como comentaba antes, la [documentación oficial del emulador Linux vNext](https://learn.microsoft.com/en-us/azure/cosmos-db/emulator-linux) deja claro que **no aplica autenticación actualmente**, así que el foco de estas pruebas está en la conectividad y en el comportamiento de datos. Si tú necesitas validar identidad, permisos o secretos, esa parte si te la tienes que llevar a un entorno real de Azure. El emulador no está para eso (por ahora).

### Sembrar datos y probar CRUD real

Una vez tienes el contenedor, lo útil no es hacer una prueba anecdótica, sino comprobar un flujo completo. Yo suelo empezar por un caso de escritura + lectura, porque demuestra persistencia real y además toca varias piezas a la vez: serialización, clave de partición y contrato del SDK.

```csharp
using Microsoft.Azure.Cosmos;
using Xunit;

[Collection("cosmos")]
public sealed class OrderCrudTests
{
    private readonly Container _container;

    public OrderCrudTests(CosmosFixture fixture)
    {
        _container = fixture.Container;
    }

    [Fact]
    public async Task Create_and_read_order_persists_the_document()
    {
        var order = new Order(
            id: "order-1001",
            customerId: "cust-42",
            status: "Pending",
            total: 149.95m);

        ItemResponse<Order> createResponse =
            await _container.CreateItemAsync(order, new PartitionKey(order.customerId));

        ItemResponse<Order> readResponse =
            await _container.ReadItemAsync<Order>(order.id, new PartitionKey(order.customerId));

        Assert.Equal(System.Net.HttpStatusCode.Created, createResponse.StatusCode);
        Assert.Equal("order-1001", readResponse.Resource.id);
        Assert.Equal("Pending", readResponse.Resource.status);
        Assert.Equal(149.95m, readResponse.Resource.total);
        Assert.False(string.IsNullOrWhiteSpace(createResponse.ETag)); // Me lo guardo porque luego sirve para concurrencia optimista
    }
}

public sealed record Order(string id, string customerId, string status, decimal total);
```

Si la prueba pasa, deberías ver una ejecución verde en xUnit. Y si inspeccionas Data Explorer, encontrarás el documento insertado dentro de la partición `cust-42`.

```text
Passed!  Total: 1, Failed: 0, Skipped: 0, Time: 1.2 s
```

Este tipo de prueba ya te da algo que un mock no te da ni de lejos: confirmas serialización, particionado, escritura, lectura y comportamiento real del SDK. **Es una garantía bastante más cercana a la realidad**. No perfecta, pero sí muy útil.

### Verificar concurrencia optimista con ETag

La concurrencia es uno de esos casos habituales que merece la pena automatizar pronto. En aplicaciones con Cosmos DB, las sobrescrituras silenciosas son de esos errores que parecen pequeños… hasta que llegan a producción. Y aquí el emulador también ayuda mucho a detectar fallos de lógica antes de tocar Azure.

```csharp
using Microsoft.Azure.Cosmos;
using Xunit;

[Collection("cosmos")]
public sealed class OrderConcurrencyTests
{
    private readonly Container _container;

    public OrderConcurrencyTests(CosmosFixture fixture)
    {
        _container = fixture.Container;
    }

    [Fact]
    public async Task Replace_with_stale_etag_returns_precondition_failed()
    {
        var original = new Order("order-2001", "cust-77", "Pending", 80m);

        ItemResponse<Order> created =
            await _container.CreateItemAsync(original, new PartitionKey(original.customerId));

        var updated = created.Resource with { status = "Confirmed" };

        ItemResponse<Order> firstReplace = await _container.ReplaceItemAsync(
            updated,
            updated.id,
            new PartitionKey(updated.customerId),
            new ItemRequestOptions { IfMatchEtag = created.ETag });

        var staleUpdate = firstReplace.Resource with { status = "Cancelled" };

        var exception = await Assert.ThrowsAsync<CosmosException>(() =>
            _container.ReplaceItemAsync(
                staleUpdate,
                staleUpdate.id,
                new PartitionKey(staleUpdate.customerId),
                new ItemRequestOptions { IfMatchEtag = created.ETag })); // Fuerzo el conflicto reutilizando un ETag ya invalidado

        Assert.Equal(System.Net.HttpStatusCode.PreconditionFailed, exception.StatusCode);
    }
}
```

Cuando esta prueba se comporta como debe, verás una ejecución verde y sabrás algo muy concreto: que tu aplicación no está ignorando conflictos de actualización y que tu uso de ETags tiene sentido. El resultado esperado sería este:

```text
Passed!  Total: 1, Failed: 0, Skipped: 0, Time: 1.5 s
```

{{< figure src="/images/azure-cosmos-db-emulator-el-camino-mas-sensato-de-local-a-ci/body-3.png" alt="Diagrama de concurrencia optimista con ETag en Cosmos DB" caption="La prueba de ETag detecta sobrescrituras silenciosas antes de que lleguen a producción." >}}{{< /figure >}}

### Llevar exactamente el mismo enfoque a GitHub Actions

Aquí es donde, para mí, el emulador gana de verdad. No quiero una estrategia para local y otra distinta para CI. Ese drifting en el código y en la configuración llega a crecer a niveles insoportables. Quiero el mismo patrón, con el menor número posible de diferencias y con el mismo tipo de señal cuando algo falla.

En GitHub Actions puedes levantar el contenedor del emulador, esperar al probe `/ready` y ejecutar las mismas pruebas .NET. Ese encaje con CI está precisamente en el centro del enfoque descrito por [el equipo de Azure Cosmos DB](https://devblogs.microsoft.com/cosmosdb/from-local-development-to-ci-workflows-with-the-azure-cosmos-db-emulator/).

```yaml
name: integration-tests

on:
  push:
    branches: [ main ]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Configurar .NET 10
        uses: actions/setup-dotnet@v4
        with:
          dotnet-version: '10.0.x'

      - name: Levantar Azure Cosmos DB Emulator
        run: |
          docker run -d \
            --name cosmosdb-emulator \
            -p 8081:8081 \
            -p 8080:8080 \
            -p 1234:1234 \
            mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:vnext-latest

      - name: Esperar a que el emulador esté listo
        run: |
          for i in {1..60}; do
            if curl -fsS http://localhost:8080/ready > /dev/null; then
              echo "Emulador listo"
              exit 0
            fi
            sleep 2
          done
          echo "El emulador no estuvo listo a tiempo"
          docker logs cosmosdb-emulator
          exit 1

      - name: Ejecutar pruebas de integración
        run: dotnet test tests/OrderService.IntegrationTests/OrderService.IntegrationTests.csproj --logger "console;verbosity=minimal"
```

Si todo está correcto, la comprobación clave es que el paso `Esperar a que el emulador esté listo` escriba `Emulador listo` y que después `dotnet test` termine con tests en verde.

```text
Emulador listo
Passed!  Total: 2, Failed: 0, Skipped: 0
```

**Y aquí está la gracia de todo esto:** local y CI hablan el mismo idioma. No el mismo “más o menos”, sino escencialmente el mismo flujo operativo. Cuando consigues eso, las pruebas de integración dejan de ser una ceremonia frágil y pasan a ser una herramienta cotidiana.

### Lo que sí y lo que no validaría con el emulador

Aquí conviene ser muy honesto. El emulador es buenísimo para validar flujos de persistencia, consultas básicas, particiones, contratos del SDK y parte de la concurrencia. Pero la [documentación del emulador Linux vNext](https://learn.microsoft.com/en-us/azure/cosmos-db/emulator-linux) deja claro que hay un subconjunto de funcionalidades y que trabaja en gateway mode. Además, existen incidencias abiertas como [este problema con `QueryRequestOptions.MaxItemCount` en consultas ordenadas y acotadas por partición](https://github.com/Azure/azure-cosmos-db-emulator-docker/issues/347), que sirven como recordatorio bastante sano: **el emulador no es un clon perfecto del servicio administrado**.

Eso no invalida su uso, sino que lo coloca exactamente en el sitio correcto. Yo lo usaría para:

- Pruebas de integración en local y CI,
- Validación de CRUD y consultas representativas,
- Verificación de serialización, particionado y ETags,
- *Feedback* rápido en *pull requests*.

Y dejaría para un entorno real en Azure:

- Pruebas previas a *release* de escenarios críticos,
- Validación de capacidades no soportadas por el emulador,
- Pruebas de seguridad, identidad y configuración de producción,
- Comprobaciones de rendimiento realistas.

### Mi recomendación práctica

Si hoy tu equipo sigue usando mocks para todo lo que toca base de datos, yo no intentaría arreglarlo con una gran migración épica (ya sabes, de esas que acaban en una hoja de cálculo con demasiados colores, o un JIRA desbordado e ingestionable). Empezaría por dos o tres pruebas de integración de mucho valor: una de escritura y lectura, una de actualización con ETag y una consulta relevante por partición. Las ejecutaría primero en local con Docker y después exactamente igual en GitHub Actions.

Ese pequeño cambio ya te obliga a diseñar mejor el acceso a datos, a separar configuración de infraestructura y a pensar en datos de prueba reproducibles. Y, sobre todo, te da una señal que vale bastante más que un test unitario maquillado: que tu código habla de verdad con Cosmos DB a través del mismo SDK que vas a usar en producción.

{{< figure src="/images/azure-cosmos-db-emulator-el-camino-mas-sensato-de-local-a-ci/body-4.png" alt="Comparativa visual entre pruebas frágiles y flujo determinista con emulador" caption="El valor real del emulador aparece cuando el mismo recorrido local también funciona en CI." >}}{{< /figure >}}

Mi conclusión es clara: **Azure Cosmos DB Emulator no sustituye a Azure Cosmos DB, pero sí allana muchísimo el camino entre desarrollar y confiar**. Si puedo reproducir en mi portátil lo mismo que va a ejecutar el pipeline, reduzco sorpresas, acelero el *feedback* y convierto las pruebas de integración en una herramienta diaria, no en una ceremonia esporádica.

No se tu, pero cuando eso pasa, duermo muchísimo mejor.
