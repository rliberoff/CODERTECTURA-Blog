---
title: 'Event Hubs y Azure Functions: lo que cambia cuando te tomas en serio la resiliencia'
date: '2026-07-13T09:26:58+00:00'
draft: true
slug: event-hubs-y-azure-functions-lo-que-cambia-cuando-te-tomas-en-serio-la-resilienc
description: Repaso las guías más recientes de Azure para diseñar con Event Hubs y
  Functions pensando en duplicados, reintentos, picos de carga y reprocesado seguro.
categories:
- Azure
- Arquitectura de Software
- .NET
tags:
- Azure Event Hubs
- Azure Functions
- Resiliencia
- Arquitectura de Software
- Idempotencia
- Serverless
image: /images/event-hubs-y-azure-functions-lo-que-cambia-cuando-te-tomas-en-serio-la-resilienc/cover.png
comments: true
ai:
  assisted: true
  model: gpt-5.4
  prompt_version: 2026-06-30.5
  generated_at: '2026-07-13T09:26:58+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://learn.microsoft.com/en-us/azure/well-architected/whats-new
    title: What's New in the Azure Well-Architected Framework - Microsoft Azure Well-Architected
      Framework | Microsoft Learn
    published_date: '2026-06-18'
  - url: https://learn.microsoft.com/en-us/azure/architecture/integration/integration-get-started
    title: Get Started with Integration Architecture Design - Azure Architecture Center
      | Microsoft Learn
    published_date: '2026-07-02'
  - url: https://learn.microsoft.com/en-us/azure/architecture/serverless/event-hubs-functions/resilient-design
    title: Resilient design guidance for Event Hubs and Functions - Azure Architecture
      Center | Microsoft Learn
    published_date: '2026-04-22'
  - url: https://learn.microsoft.com/en-us/azure/well-architected/sustainability/overview
    title: Sustainable workloads on Azure - Microsoft Azure Well-Architected Framework
      | Microsoft Learn
    published_date: '2026-06-26'
---

Si trabajas con sistemas dirigidos por eventos, tarde o temprano te topas con una verdad bastante incómoda: que algo “funcione” no significa que sea resiliente. En Event Hubs y Azure Functions eso se nota rápido, porque los problemas no siempre llegan en forma de caída aparatosa. A veces aparecen como duplicados, reintentos en cadena, escalado raro o eventos que luego no puedes reprocesar con seguridad.

Por eso me ha parecido especialmente valiosa la guía de diseño resiliente para Event Hubs y Functions del Azure Architecture Center. Me gusta porque aterriza principios muy abstractos en decisiones bastante concretas de arquitectura, [como explica Microsoft aquí](https://learn.microsoft.com/en-us/azure/architecture/serverless/event-hubs-functions/resilient-design).

Y no me interesa solo la guía aislada, sino el contexto en el que aparece. Microsoft sigue ampliando el Azure Well-Architected Framework con material más accionable, por ejemplo con nuevas guías alrededor de la fiabilidad y el *throttling*, [según las novedades publicadas](https://learn.microsoft.com/en-us/azure/well-architected/whats-new). Eso encaja muy bien con cómo entiendo yo la integración moderna en Azure: no todo debe resolverse con APIs síncronas, y hay escenarios donde el desacoplamiento y el *streaming* son justo lo que toca, [como recuerda la guía de integración](https://learn.microsoft.com/en-us/azure/architecture/integration/integration-get-started).

### El primer cambio mental: un stream no es una cola

La idea más importante de toda esta conversación, para mí, es esta: Event Hubs no se comporta como una cola tradicional.

Microsoft lo deja bastante claro: en el modelo particionado, las lecturas son no destructivas y los eventos siguen estando disponibles para otros consumidores, o incluso para el mismo consumidor más adelante, [en la guía de diseño resiliente](https://learn.microsoft.com/en-us/azure/architecture/serverless/event-hubs-functions/resilient-design).

Y eso tiene consecuencias arquitectónicas muy poco decorativas:

- No debes asumir consumo *exactly once* por defecto;
- No tienes *dead-letter* nativo como en un broker clásico;
- El reprocesado forma parte natural del modelo;
- La idempotencia deja de ser una mejora elegante y pasa a ser un requisito de verdad.

{{< figure src="/images/event-hubs-y-azure-functions-lo-que-cambia-cuando-te-tomas-en-serio-la-resilienc/body-1.png" alt="Diagrama comparando stream y cola" caption="Event Hubs funciona como stream particionado, no como cola tradicional; esa diferencia cambia por completo la estrategia de resiliencia." >}}{{< /figure >}}

Si tu caso de uso necesita semánticas muy cercanas a cola, competición agresiva entre consumidores o *dead-lettering* intrínseco, yo revisaría seriamente si Event Hubs es la pieza adecuada o si Service Bus encaja mejor. No es una guerra absurda entre servicios. Es, simplemente, respetar el patrón para el que fue diseñado cada uno.

### La resiliencia aquí no empieza en los reintentos, empieza en la idempotencia

Cuando alguien me dice “ya tenemos retries”, mi siguiente pregunta suele ser bastante directa: “¿y si el mismo evento se procesa dos veces?”. Si no hay una respuesta sólida, todavía no hay resiliencia.

Con Event Hubs y Functions, los duplicados pueden aparecer por motivos totalmente razonables: reinicios del host, fallos transitorios, reintentos, reprocesado deliberado o recuperación tras una incidencia. La guía de Microsoft insiste precisamente en diseñar para idempotencia, [aquí](https://learn.microsoft.com/en-us/azure/architecture/serverless/event-hubs-functions/resilient-design).

En mi experiencia, la idempotencia útil suele apoyarse en una de estas estrategias:

- **Clave de operación de negocio**: por ejemplo `OrderId + EventType`.
- **Event ID único** generado por el productor.
- **Control de versión o de estado esperado** en el destino.
- **Registro de procesamiento** con caducidad si el volumen es muy alto.

Lo importante no es solo detectar duplicados. Lo importante es detectarlos en el sitio correcto. Si el efecto real ocurre en una base de datos, en una API externa o en un agregado de dominio, la protección debería vivir pegada a esa frontera. No antes. No en una capa “bonita” pero irrelevante.

Un ejemplo sencillo en .NET sería persistir el identificador del evento antes de volver a aplicar el efecto. Aquí el orden importa muchísimo: si primero ejecutas el efecto y luego marcas el evento como procesado, te dejas abierta una ventana de duplicación en caso de fallo entre ambas operaciones.

```csharp
public async Task ProcessOrderSubmittedAsync(
    string eventId,
    string orderId,
    CancellationToken cancellationToken)
{
    if (await _processedEvents.ExistsAsync(eventId, cancellationToken))
    {
        return; // Si ya lo vi antes, salir aquí evita repetir el efecto.
    }

    await _processedEvents.StoreAsync(eventId, cancellationToken);

    try
    {
        await _orders.MarkAsSubmittedAsync(orderId, cancellationToken);
    }
    catch
    {
        await _processedEvents.RemoveAsync(eventId, cancellationToken); // Revierte la marca si el efecto no llegó a completarse.
        throw;
    }
}
```

No, este patrón no resuelve todos los casos (ojalá). Pero cambia por completo la conversación: pasas de “espero que no llegue duplicado” a “aunque llegue, el sistema se comporta bien”. Y ese cambio mental vale oro.

### Reintentar sí, pero con intención

Otra idea que me parece acertada en las guías recientes de Azure es que la fiabilidad ya no se trata como una lista de *checks*, sino como una disciplina de control de presión. Se ve, por ejemplo, en la nueva guía de *throttling* anunciada en Well-Architected, [en las novedades del framework](https://learn.microsoft.com/en-us/azure/well-architected/whats-new).

En un flujo Event Hubs → Functions, reintentar sin pensar puede empeorar el problema bastante deprisa:

- Si el destino ya está saturado, más reintentos significan más presión;
- Si el error no es transitorio, solo retrasas lo inevitable;
- Si no separas errores recuperables de errores permanentes, conviertes una incidencia pequeña en ruido masivo.

Yo intento distinguir tres categorías muy simples:

1. **Error transitorio**: *timeouts*, 429, microcortes de red.
2. **Error funcional recuperable**: la dependencia responde, pero el dato todavía no está en un estado coherente.
3. **Error permanente**: contrato inválido, evento corrupto o regla de negocio imposible.

Solo los dos primeros deberían aspirar a reintento, y aun así con límites. Para lo permanente, lo razonable es apartar el evento del flujo principal y enviarlo a una vía de análisis o compensación.

Como Event Hubs no ofrece *dead-letter* nativo, esa salida de cuarentena la tienes que diseñar tú: otro hub, una cola, almacenamiento o incluso un registro operacional, según el caso, [tal como explica Microsoft](https://learn.microsoft.com/en-us/azure/architecture/serverless/event-hubs-functions/resilient-design).

{{< figure src="/images/event-hubs-y-azure-functions-lo-que-cambia-cuando-te-tomas-en-serio-la-resilienc/body-2.png" alt="Flujo de reintentos y eventos problemáticos" caption="No todos los errores merecen el mismo tratamiento: reintento para lo transitorio, cuarentena para lo permanente." >}}{{< /figure >}}

### El patrón que más echo en falta: separar ingestión de procesamiento frágil

Un error bastante habitual es acoplar demasiado la función disparada por Event Hubs con llamadas lentas o frágiles a sistemas externos. Si cada evento dispara lógica pesada en línea, el *throughput* real deja de depender de Event Hubs y pasa a depender del eslabón más débil de la cadena.

Aquí yo suelo pensar en dos etapas muy distintas:

- **Ingestión rápida y robusta**: validar lo mínimo, enriquecer lo justo, persistir o reenrutar.
- **Procesamiento posterior**: operaciones lentas, integraciones externas, reglas complejas.

Este enfoque encaja muy bien con la visión general de integración en Azure, donde cada tecnología tiene su papel y no todo debe resolverse en un único salto, [según la guía de arquitectura de integración](https://learn.microsoft.com/en-us/azure/architecture/integration/integration-get-started).

Dicho de otra forma: la función de entrada debería hacer poco, pero hacerlo de forma predecible. Si conviertes esa primera función en un embudo cargado de dependencias, pierdes elasticidad y amplías el radio de fallo. Y luego llegan las sorpresas, claro.

### Escalar no es solo “poner más instancias”

Con Event Hubs, el paralelismo está íntimamente ligado a las particiones. Esa relación importa porque condiciona cuánto trabajo puedes procesar a la vez y cómo se distribuye la carga.

Si ignoras esto, luego aparecen los clásicos síntomas que nadie quiere mirar de frente: una clave muy caliente, una partición retrasada o una función aparentemente escalada pero con un *throughput* muy desigual.

{{< figure src="/images/event-hubs-y-azure-functions-lo-que-cambia-cuando-te-tomas-en-serio-la-resilienc/body-3.png" alt="Diagrama de particiones y escalado" caption="El escalado efectivo depende de cómo repartes la carga entre particiones y de dónde está realmente el cuello de botella." >}}{{< /figure >}}

Yo me fijaría, como mínimo, en cuatro decisiones:

- **Número de particiones**: no lo elijas solo por el volumen de hoy.
- **Clave de particionado**: una mala elección crea *hotspots* enseguida.
- **Duración y peso del handler**: cuanto más tiempo bloquea cada evento, peor aprovechas el paralelismo.
- **Checkpointing y reproceso**: conviene entender qué pasa si una instancia cae a mitad del trabajo.

La guía resiliente insiste en manejar grandes volúmenes con un diseño consciente del comportamiento del *stream* y de Functions, [aquí](https://learn.microsoft.com/en-us/azure/architecture/serverless/event-hubs-functions/resilient-design). Y yo lo resumiría con una regla muy simple: **escala por partición, pero diseña por cuello de botella**.

Si el cuello está en una API externa con límites estrictos, da igual que Event Hubs pueda tragarse muchísimo más. Tu arquitectura necesita incorporar *backpressure*, limitación de concurrencia y degradación controlada. Si no, el escalado solo te ayuda a fallar más deprisa. Que también es una forma de escalar, supongo, pero no de las buenas.

### Qué haría yo como baseline arquitectónico

Si me preguntas por una hoja de ruta razonable para un sistema nuevo con Event Hubs y Azure Functions, yo empezaría por aquí:

- Usaría **identificadores de evento estables** desde el productor;
- Haría el consumidor **idempotente por diseño**;
- Distinguiría explícitamente **errores transitorios y permanentes**;
- Implementaría una **ruta de cuarentena** para eventos no procesables;
- Mantendría la función de entrada **ligera y rápida**;
- Mediría **lag por partición**, tasa de error, duplicados detectados y tiempo de procesamiento;
- Revisaría los límites de dependencias externas para no convertir el escalado en una tormenta de 429.

Y añadiría una idea que me parece muy alineada con la evolución reciente de Well-Architected: la resiliencia también tiene coste energético y operativo. La nueva documentación de sostenibilidad recuerda que el sobredimensionamiento, la telemetría excesiva y la infraestructura siempre encendida generan desperdicio, [como recoge esta guía](https://learn.microsoft.com/en-us/azure/well-architected/sustainability/overview).

En sistemas *event-driven*, eso significa algo bastante práctico: reintentar de más, reprocesar sin control o mantener lógica ineficiente no solo encarece. También hace el sistema menos sostenible.

{{< figure src="/images/event-hubs-y-azure-functions-lo-que-cambia-cuando-te-tomas-en-serio-la-resilienc/body-4.png" alt="Relación entre resiliencia, coste y sostenibilidad" caption="Una arquitectura resiliente no solo evita fallos: también reduce reprocesos inútiles, coste operativo y desperdicio." >}}{{< /figure >}}

### Mi conclusión

Lo que más me gusta de estas actualizaciones de Azure es que aterrizan una idea clave: la fiabilidad real en sistemas de eventos no se compra con un *checkbox*. Se diseña. Y se diseña aceptando que habrá duplicados, fallos transitorios, consumidores lentos, picos de carga y dependencias que no siempre cooperan.

Si trabajas con Event Hubs y Azure Functions, yo no empezaría preguntándome “cómo proceso más rápido”, sino “cómo fallo bien”. A partir de ahí, la arquitectura mejora casi sola: aparecen la idempotencia, la separación de responsabilidades, los reintentos con criterio y una estrategia de escala que no confunde volumen con resiliencia.

En mi experiencia, ese cambio de enfoque es justo el que separa una demo que impresiona de un sistema que aguanta producción de verdad.
