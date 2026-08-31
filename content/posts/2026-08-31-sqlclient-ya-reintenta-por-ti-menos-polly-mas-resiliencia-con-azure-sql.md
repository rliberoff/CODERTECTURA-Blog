---
title: 'SqlClient ya reintenta por ti: menos Polly, más resiliencia con Azure SQL'
date: '2026-08-31T12:57:48+00:00'
draft: true
slug: sqlclient-ya-reintenta-por-ti-menos-polly-mas-resiliencia-con-azure-sql
description: Microsoft.Data.SqlClient ya incorpora reintentos nativos para fallos
  transitorios con Azure SQL. Te enseño por qué simplifica la arquitectura y cómo
  validarlo sin autoengaños.
categories:
- .NET
- Azure
- Arquitectura de Software
tags:
- Azure SQL
- .NET
- SqlClient
- Resiliencia
- Arquitectura
- ASP.NET Core
image: /images/sqlclient-ya-reintenta-por-ti-menos-polly-mas-resiliencia-con-azure-sql/cover.png
comments: true
ai:
  assisted: true
  article_type: technical
  model: gpt-5.4
  prompt_version: 2026-08-21.1
  generated_at: '2026-08-31T12:57:48+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://devblogs.microsoft.com/azure-sql/sqlclient-retry/
    title: Try the new SqlClient and Retry connections natively
    published_date: '2026-08-29'
  - url: https://github.com/microsoft/aspire/wiki/13.5-Change-log
    title: 13.5 Change log · microsoft/aspire Wiki
    published_date: null
---

Si trabajas con Azure SQL desde .NET, seguramente te ha pasado lo mismo que a mí: acabas montando alguna combinación de Polly, utilidades compartidas, lógica en repositorios o pequeños apaños defensivos para sobrevivir a cortes breves, *timeouts* y errores de red intermitentes. La novedad es que [Microsoft.Data.SqlClient añade lógica de reintentos configurable para `SqlConnection` y `SqlCommand`](https://devblogs.microsoft.com/azure-sql/sqlclient-retry/), y a mí esto me parece relevante por una razón muy concreta: **la resiliencia baja al sitio correcto**, mucho más cerca del cliente de base de datos. Y eso, en arquitectura, no es un matiz; es una simplificación real.

En este artículo te voy a enseñar cómo aterrizar esa mejora en una aplicación .NET de verdad, cómo comprobar que está funcionando y en qué escenarios yo seguiría manteniendo una política externa además del *retry* nativo. Porque sí, mejora mucho las cosas, pero no convierte el acceso a datos en magia negra benévola (ojalá).

### Antes de empezar

Para reproducir lo que te muestro, yo partiría de un entorno bastante simple:

- **.NET 8 SDK** instalado.
- Un servidor de **Azure SQL Database** accesible desde tu equipo.
- Un usuario con permisos para conectarse y ejecutar consultas sencillas sobre una base ya existente.
- El paquete **Microsoft.Data.SqlClient** en una versión que incluya el soporte de *retry* nativo descrito en [el anuncio oficial del equipo de Azure SQL](https://devblogs.microsoft.com/azure-sql/sqlclient-retry/).
- De forma opcional, una API mínima de ASP.NET Core para observar el comportamiento en un endpoint real.

También necesitas tener permitida tu IP en el *firewall* del servidor de Azure SQL. Esto parece obvio, pero conviene decirlo porque aquí hay una frontera importante: si tu IP está bloqueada, verás un fallo persistente, y **eso no es un error transitorio**. Ningún reintento sensato te lo va a arreglar.

{{< figure src="/images/sqlclient-ya-reintenta-por-ti-menos-polly-mas-resiliencia-con-azure-sql/body-1.png" alt="Diagrama de arquitectura con reintentos nativos en SqlClient" caption="La resiliencia se desplaza hacia el cliente SQL: menos lógica repetida en la aplicación, más consistencia en el acceso a datos." >}}{{< /figure >}}

### Qué cambia realmente con el retry nativo

La idea de fondo es sencilla: en vez de envolver cada acceso a SQL con una política externa, el propio cliente puede encargarse de reintentar cuando detecta fallos transitorios. Según [la explicación del equipo de Azure SQL sobre el nuevo comportamiento de SqlClient](https://devblogs.microsoft.com/azure-sql/sqlclient-retry/), este soporte se aplica a operaciones sobre `SqlConnection` y `SqlCommand`.

A mí esto me gusta especialmente por tres motivos. El primero es la cohesión: los problemas de conectividad, transporte y recuperación breve pertenecen al cliente SQL, no al caso de uso de tu aplicación. El segundo es la consistencia: evitas que un repositorio tenga *retry*, otro no, y un tercero tenga una variante “casi igual” porque alguien copió una política y cambió dos valores. El tercero es el mantenimiento: si lo único que quieres es absorber cortes pequeños de red o *failovers* cortos, puedes eliminar bastante código accidental.

Dicho eso, tampoco conviene venderlo como una solución universal. El *retry* nativo no sustituye todas las estrategias de resiliencia. Si tienes operaciones compuestas, coordinación entre varios recursos, semántica de idempotencia delicada o una transacción que depende de algo más que SQL, seguirás necesitando decisiones por encima del *driver*. **Mover el retry al cliente simplifica mucho, pero no elimina la responsabilidad arquitectónica**.

### Paso 1: crear una consola .NET y añadir SqlClient

Yo empezaría con una aplicación de consola mínima, porque aquí interesa ver el comportamiento sin demasiado ruido alrededor.

```bash
dotnet new console -n SqlClientRetryDemo
cd SqlClientRetryDemo
dotnet add package Microsoft.Data.SqlClient
```

Con eso deberías tener el proyecto creado y el paquete referenciado en el `.csproj`.

Para el ejemplo, voy a evitar credenciales embebidas en código. No solo porque sea mala práctica, sino porque luego acabamos copiando y pegando cosas donde no toca (y todos sabemos cómo termina eso). Este `Program.cs` lee la cadena de conexión desde una variable de entorno, activa el *retry* nativo y ejecuta una consulta trivial:

```csharp
using Microsoft.Data.SqlClient;
using System.Diagnostics;

var baseConnectionString = Environment.GetEnvironmentVariable("SQL_CONNECTION_STRING")
    ?? throw new InvalidOperationException(
        "Define la variable de entorno SQL_CONNECTION_STRING con la conexión a Azure SQL.");

var csb = new SqlConnectionStringBuilder(baseConnectionString)
{
    ConnectTimeout = 5,
    ConnectRetryCount = 5,
    ConnectRetryInterval = 2 // Este es el cambio clave: el cliente absorberá cortes breves al abrir la conexión
};

var stopwatch = Stopwatch.StartNew();

await using var connection = new SqlConnection(csb.ConnectionString);
await connection.OpenAsync();

await using var command = connection.CreateCommand();
command.CommandText = "SELECT TOP (1) name FROM sys.databases ORDER BY name;";
command.CommandTimeout = 5;

var result = await command.ExecuteScalarAsync();

stopwatch.Stop();
Console.WriteLine($"Base de datos leída: {result}");
Console.WriteLine($"Tiempo total: {stopwatch.ElapsedMilliseconds} ms");
```

Si todo está bien configurado, verás una salida parecida a esta:

```text
Base de datos leída: AppDb
Tiempo total: 180 ms
```

Lo importante aquí no es la consulta, que es casi anecdótica. Lo importante es que ya has activado resiliencia en el propio cliente SQL **sin meter Polly ni envolver manualmente cada acceso**. Para muchos servicios internos, solo esto ya reduce bastante el ruido de la solución.

### Paso 2: comparar sin retry y con retry

Ahora viene la parte que a mí más me interesa: comprobar que esto no es solo una casilla bonita en la documentación. En vez de esperar a que se produzca un fallo real, puedes provocar una perturbación breve de conectividad: por ejemplo, deshabilitando temporalmente el acceso de tu IP en el *firewall* del servidor y reactivándolo enseguida, o cortando la red local durante unos segundos. No es una prueba de laboratorio perfecta, pero sirve para observar el patrón.

Este programa compara dos conexiones: una sin *retry* nativo y otra con él. La gracia está en que ambas usan la misma base de configuración y solo cambia la parte que de verdad quieres medir.

```csharp
using Microsoft.Data.SqlClient;
using System.Diagnostics;

var baseConnectionString = Environment.GetEnvironmentVariable("SQL_CONNECTION_STRING")
    ?? throw new InvalidOperationException(
        "Define la variable de entorno SQL_CONNECTION_STRING con la conexión a Azure SQL.");

var withoutRetryBuilder = new SqlConnectionStringBuilder(baseConnectionString)
{
    ConnectTimeout = 5,
    ConnectRetryCount = 0
};

var withRetryBuilder = new SqlConnectionStringBuilder(baseConnectionString)
{
    ConnectTimeout = 5,
    ConnectRetryCount = 5,
    ConnectRetryInterval = 2
};

await TestConnectionAsync("Sin retry nativo", withoutRetryBuilder.ConnectionString);
await TestConnectionAsync("Con retry nativo", withRetryBuilder.ConnectionString);

static async Task TestConnectionAsync(string title, string connectionString)
{
    Console.WriteLine($"\n--- {title} ---");
    var sw = Stopwatch.StartNew();

    try
    {
        await using var connection = new SqlConnection(connectionString);
        await connection.OpenAsync();

        await using var command = connection.CreateCommand();
        command.CommandText = "SELECT 1;";
        command.CommandTimeout = 5;

        var result = await command.ExecuteScalarAsync();

        sw.Stop();
        Console.WriteLine($"Resultado: {result}");
        Console.WriteLine($"Estado: OK en {sw.ElapsedMilliseconds} ms");
    }
    catch (SqlException ex)
    {
        sw.Stop();
        Console.WriteLine($"Estado: ERROR en {sw.ElapsedMilliseconds} ms");
        Console.WriteLine($"Tipo: {ex.GetType().Name}");
        Console.WriteLine($"Mensaje: {ex.Message}");
    }
}
```

En una ejecución normal, los dos casos te devolverán `1`. La diferencia aparece cuando introduces ese corte breve. Lo esperable es algo así:

- **Sin retry nativo**: la apertura de conexión falla bastante rápido.
- **Con retry nativo**: el cliente tarda más, reintenta y puede completar la operación si la conectividad vuelve dentro de la ventana configurada.

Una salida realista podría parecerse a esta:

```text
--- Sin retry nativo ---
Estado: ERROR en 5034 ms
Tipo: SqlException
Mensaje: A network-related or instance-specific error occurred while establishing a connection to SQL Server.

--- Con retry nativo ---
Resultado: 1
Estado: OK en 9312 ms
```

Yo no me obsesionaría con los milisegundos exactos. Lo que importa es el patrón: **el segundo caso absorbe mejor una perturbación corta**. Y esa diferencia, cuando la llevas a un backend con tráfico real, se nota más de lo que parece.

{{< figure src="/images/sqlclient-ya-reintenta-por-ti-menos-polly-mas-resiliencia-con-azure-sql/body-2.png" alt="Comparativa entre conexión sin retry y con retry nativo" caption="Ante un corte breve, el cliente sin retry falla rápido; con retry nativo, la operación puede recuperarse dentro de la ventana configurada." >}}{{< /figure >}}

### Paso 3: llevarlo a una API ASP.NET Core sin Polly

Donde esto gana valor de verdad es en una API sencilla que consulta Azure SQL con frecuencia. Si el propio cliente ya gestiona ciertos fallos transitorios, el endpoint queda más limpio y la capa web deja de cargar con una responsabilidad que realmente no es suya.

Puedes crear una API mínima así:

```bash
dotnet new web -n SqlClientRetryApi
cd SqlClientRetryApi
dotnet add package Microsoft.Data.SqlClient
```

Y este sería un `Program.cs` razonable para una prueba simple. De nuevo, la conexión sale de configuración, no del código fuente.

```csharp
using Microsoft.Data.SqlClient;

var builder = WebApplication.CreateBuilder(args);

var baseConnectionString = builder.Configuration["Sql:ConnectionString"]
    ?? throw new InvalidOperationException(
        "Configura 'Sql:ConnectionString' o la variable de entorno 'Sql__ConnectionString'.");

var sqlConnectionString = new SqlConnectionStringBuilder(baseConnectionString)
{
    ConnectTimeout = 5,
    ConnectRetryCount = 5,
    ConnectRetryInterval = 2 // Centralizo el comportamiento aquí para que todos los endpoints usen el mismo criterio
};

builder.Services.AddSingleton(sqlConnectionString);

var app = builder.Build();

app.MapGet("/db-health", async (SqlConnectionStringBuilder csb, CancellationToken cancellationToken) =>
{
    await using var connection = new SqlConnection(csb.ConnectionString);
    await connection.OpenAsync(cancellationToken);

    await using var command = connection.CreateCommand();
    command.CommandText = "SELECT DB_NAME(), SYSDATETIMEOFFSET();";
    command.CommandTimeout = 5;

    await using var reader = await command.ExecuteReaderAsync(cancellationToken);
    await reader.ReadAsync(cancellationToken);

    return Results.Ok(new
    {
        database = reader.GetString(0),
        checkedAt = reader.GetDateTimeOffset(1),
        retry = new
        {
            connectRetryCount = csb.ConnectRetryCount,
            connectRetryInterval = csb.ConnectRetryInterval
        }
    });
});

app.Run();
```

Si ejecutas la API con `dotnet run`, deberías poder consultar el endpoint y recibir un JSON con el nombre de la base de datos, la fecha de comprobación y la configuración de *retry* que has aplicado. Y si provocas un corte breve mientras haces varias llamadas, verás justo el matiz que a mí me interesa en sistemas reales: algunas peticiones tardarán más, pero no necesariamente fallarán a la primera. **Eso es degradación suave**, no éxito perfecto, y aun así suele ser una mejora excelente.

### Qué simplifica en arquitectura, y qué no

Desde el punto de vista arquitectónico, yo saco tres conclusiones bastante prácticas.

La primera es que esto reduce la necesidad de repetir políticas de reintento en cada repositorio, servicio o adaptador. Si tu problema principal son fallos transitorios de conectividad SQL, el cliente es un lugar mucho mejor para resolverlo. Y la noticia importante no es solo técnica, sino de diseño: [SqlClient incorpora resiliencia nativa para conexiones y comandos](https://devblogs.microsoft.com/azure-sql/sqlclient-retry/), lo que empuja a una arquitectura más coherente y con menos pegamento artesanal.

La segunda es que no todo *retry* debe desaparecer de capas superiores. Si una operación involucra SQL, una cola, una llamada HTTP y quizá una escritura en blob, yo seguiría tratando la resiliencia como una preocupación compuesta. En ese caso, el *driver* cubre una parte del problema, pero no la orquestación completa ni la semántica de la operación.

La tercera es que merece la pena revisar los *timeouts* con cabeza. Si subes demasiado el número de reintentos o el intervalo, puedes ganar tolerancia a fallos breves, sí, pero también alargar la latencia percibida por el usuario o por el sistema que consume tu API. **La resiliencia casi siempre se compra con tiempo, complejidad o ambos**. Aquí compras algo de tiempo para ganar estabilidad, y en muchos backends me parece un intercambio perfectamente razonable.

{{< figure src="/images/sqlclient-ya-reintenta-por-ti-menos-polly-mas-resiliencia-con-azure-sql/body-3.png" alt="Diagrama sobre el límite entre retry del cliente y resiliencia de arquitectura" caption="El retry nativo cubre bien la conectividad SQL, pero las operaciones compuestas siguen necesitando decisiones de arquitectura." >}}{{< /figure >}}

### ¿Y qué pasa con Aspire?

Aquí no conviene mezclar conceptos, pero sí me parece útil mirar el contexto. El ecosistema .NET lleva tiempo empujando mejoras operativas y de plataforma, y en el [changelog de Aspire 13.5](https://github.com/microsoft/aspire/wiki/13.5-Change-log) se ve ese movimiento continuo hacia una mejor experiencia de desarrollo y operación. No lo menciono porque documente el *retry* de SqlClient —no es ese el caso—, sino porque encaja con una tendencia más amplia que a mí me parece clarísima: cada vez hay más capacidades transversales bajando a la infraestructura y a los componentes base, en vez de obligarte a reconstruirlas una y otra vez en código de aplicación.

Para mí, esa es la lectura de fondo. Menos piezas caseras. Más comportamiento fiable en el propio *stack*.

### Mi recomendación práctica

Si hoy tienes una aplicación .NET contra Azure SQL y estás usando Polly solo para reintentos simples de conexión o de comando, yo probaría primero la capacidad nativa de SqlClient. Haría una prueba controlada como la que te he enseñado, mediría la latencia bajo fallo breve y validaría si el resultado es suficiente para tus SLO. No porque Polly sea mala idea —ni mucho menos—, sino porque **no siempre merece la pena resolver arriba lo que ya puedes resolver abajo**.

Si la respuesta es sí, simplificaría sin dudar demasiado: menos código, menos configuraciones dispersas y menos riesgo de inconsistencias entre servicios. Si la respuesta es no, entonces mantendría una política superior, pero con una separación mucho más clara de responsabilidades. Y eso también es una mejora.

Mi conclusión es bastante simple: **este cambio merece atención porque quita complejidad justo donde más suele sobrar**. Y cuando una mejora de resiliencia, además de hacer el sistema más estable, también me permite borrar código accidental… yo compro la idea bastante rápido 😊.
