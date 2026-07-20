---
title: 'Microsoft Foundry se pone serio con la observabilidad: trazas de agentes y
  telemetría sensible bajo control'
date: '2026-07-20T16:14:09+00:00'
draft: true
slug: microsoft-foundry-da-un-paso-serio-en-observabilidad-trazas-de-agentes-y-telemet
description: Microsoft Foundry mejora el trazado de agentes y separa el contenido
  GenAI sensible en Application Insights. Te cuento qué cambia y cómo lo aterrizaría
  yo.
categories:
- Inteligencia Artificial
- Azure
- Arquitectura de Software
tags:
- Microsoft Foundry
- Observabilidad
- Application Insights
- GenAI
- Telemetría
- Azure Monitor
image: /images/microsoft-foundry-da-un-paso-serio-en-observabilidad-trazas-de-agentes-y-telemet/cover.png
comments: true
ai:
  assisted: true
  model: gpt-5.4
  prompt_version: 2026-07-20.1
  generated_at: '2026-07-20T16:14:09+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://azure.microsoft.com/updates?id=567594
    title: '[In preview] Public Preview: Protect sensitive generative AI telemetry
      in Application Insights and Microsoft Foundry'
    published_date: '2026-07-20'
  - url: https://learn.microsoft.com/en-us/azure/azure-monitor/app/data-model-complete
    title: Application Insights telemetry data model - Azure Monitor
    published_date: null
  - url: https://learn.microsoft.com/en-us/semantic-kernel/concepts/enterprise-readiness/observability/telemetry-with-azure-ai-foundry-tracing
    title: Visualize traces on Microsoft Foundry Tracing UI | Microsoft Learn
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/foundry/observability/concepts/trace-agent-concept
    title: Agent tracing in Microsoft Foundry (preview)
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/appgenaicontent
    title: Azure Monitor Logs reference - AppGenAIContent - Azure Monitor
    published_date: null
---

Si estás construyendo agentes con Microsoft Foundry, hay una pregunta que tarde o temprano acaba encima de la mesa: **¿cómo observo de verdad lo que hace el sistema sin convertir la telemetría en otro problema de seguridad?** Justo ahí encaja el movimiento reciente de Microsoft. Por un lado, Foundry refuerza el *tracing* de agentes conectándolo con Application Insights; por otro, separa el contenido generativo sensible en una tabla específica para poder aplicarle controles de acceso más finos. Para mí, estas dos piezas no son un detalle operativo ni una mejora cosmética: juntas empiezan a contar una historia de observabilidad bastante más madura para escenarios GenAI.

### La idea importante: trazas útiles, pero con límites claros

Cuando trabajo con agentes, casi nunca me basta con saber que una petición ha tardado 2,3 segundos o que un endpoint ha devuelto un 200. Eso puede servir para una API clásica, pero se queda corto en cuanto quieres entender por qué un agente ha llamado a la herramienta equivocada, ha reintentado tres veces, ha gastado más tokens de la cuenta o ha terminado generando una respuesta dudosa. Según la documentación de [agent tracing en Microsoft Foundry](https://learn.microsoft.com/en-us/azure/foundry/observability/concepts/trace-agent-concept), el sistema captura entradas, salidas, uso de herramientas, reintentos, latencias y costes durante la ejecución del agente. Y esa es la materia prima que yo realmente necesito cuando estoy depurando comportamiento, no solo infraestructura.

Lo interesante es que Microsoft no plantea esto como un visor aislado o como otro panel más que añadir a la colección. La base sigue siendo [Application Insights dentro del modelo de telemetría de Azure Monitor](https://learn.microsoft.com/en-us/azure/azure-monitor/app/data-model-complete). Es decir, las trazas del agente no viven en un universo paralelo ni en una experiencia separada que luego nadie gobierna. Se apoyan en el *stack* de observabilidad que muchos equipos ya conocen, con sus consultas, sus permisos y sus hábitos operativos. Para mí, eso reduce mucho la fricción de adopción, porque no obliga a inventar una práctica nueva desde cero solo porque ahora haya un LLM por medio.

{{< figure src="/images/microsoft-foundry-da-un-paso-serio-en-observabilidad-trazas-de-agentes-y-telemet/source-1.png" alt="Diagrama del modelo de datos y flujo de telemetría de Application Insights" caption="El valor de Foundry está en apoyarse sobre el flujo de telemetría de Application Insights, no en crear una observabilidad aislada. Fuente: [learn.microsoft.com](https://learn.microsoft.com/en-us/azure/azure-monitor/app/data-model-complete)" >}}{{< /figure >}}

### Cómo fluye la traza desde el agente hasta Application Insights

La guía de [visualización de trazas en la interfaz de Foundry](https://learn.microsoft.com/en-us/semantic-kernel/concepts/enterprise-readiness/observability/telemetry-with-azure-ai-foundry-tracing) deja bastante claro el recorrido operativo. Primero conectas un recurso de Application Insights al proyecto de Foundry desde la pestaña de Tracing. Después ejecutas tu aplicación o tu agente, y la traza termina apareciendo tanto en la base de telemetría como en la interfaz de tracing de Foundry, aunque puede tardar unos minutos en materializarse.

Ese detalle arquitectónico me parece más importante de lo que sugiere a primera vista. Cambia por completo la conversación con operaciones y con seguridad. Ya no estás diciendo “tenemos un panel nuevo para IA”, sino “estamos integrando la observabilidad de agentes en una canalización que ya sabemos gobernar”. Y eso, en un equipo real, importa muchísimo más que la demo bonita. Te permite consultar datos, crear alertas, cruzar señales con otras dependencias y, sobre todo, no perder el hilo entre la experiencia de depuración y el gobierno del dato.

Yo lo resumiría así: Foundry te da la experiencia centrada en el agente, mientras que Application Insights te da persistencia, consulta y explotación operativa. **Una interfaz sin telemetría gobernable se queda corta; una telemetría gobernable sin contexto de agente también.** La gracia está precisamente en la unión de ambas.

{{< figure src="/images/microsoft-foundry-da-un-paso-serio-en-observabilidad-trazas-de-agentes-y-telemet/source-2.png" alt="Panel de Application Insights asociado a un proyecto de Foundry" caption="La experiencia visual de Foundry se apoya en un recurso de Application Insights conectado al proyecto. Fuente: [learn.microsoft.com](https://learn.microsoft.com/en-us/semantic-kernel/concepts/enterprise-readiness/observability/telemetry-with-azure-ai-foundry-tracing)" >}}{{< /figure >}}

### Qué significa de verdad que esté en preview

Aquí conviene bajar un poco el entusiasmo (sí, ya sé que cuesta cuando algo encaja bien sobre el papel). La propia documentación de [agent tracing en Foundry](https://learn.microsoft.com/en-us/azure/foundry/observability/concepts/trace-agent-concept) indica que los elementos marcados como *preview* están en vista previa pública, sin SLA, y que no se recomiendan para cargas de producción. Además, especifica que el *tracing* está generalmente disponible para *prompt agents* y *hosted agents*, mientras que *workflow agents* y *external agents* siguen en *preview*.

Yo esto lo traduzco a una decisión arquitectónica muy concreta: si tu operación depende de esa señal para diagnosticar incidentes con garantías, **no deberías asumir todavía que todos los tipos de agentes te van a dar el mismo nivel de fiabilidad o soporte**. Puedes adoptarlo ya para aprender, instrumentar y mejorar diagnósticos, sí. De hecho, yo lo haría. Pero no basaría un proceso crítico únicamente en una capacidad *preview* sin plan B, porque luego vienen los disgustos y nadie quiere una post-mortem con cara de sorpresa.

Dicho de otra forma: *preview* no significa “ni tocarlo”, pero sí significa “úsalo con intención”. En un equipo sensato, yo separaría tres escenarios. Primero, desarrollo y pruebas, donde quieres máxima visibilidad y toleras cierta inestabilidad. Segundo, preproducción, donde validas coste, volumen y calidad real de la señal. Y tercero, producción, donde activas solo lo que puedes gobernar de verdad y donde aceptas conscientemente las limitaciones de la funcionalidad según el tipo de agente que estés utilizando.

### El cambio más relevante: tratar el contenido GenAI como dato sensible por diseño

La novedad que a mí me parece más significativa no está solo en ver mejor la ejecución, sino en cómo se almacena el contenido generado. Según el anuncio de [protección de telemetría generativa sensible en Application Insights y Microsoft Foundry](https://azure.microsoft.com/updates?id=567594), Azure Monitor Application Insights ahora guarda el contenido generativo en una tabla dedicada llamada GenAIContent, que en Log Analytics aparece como [AppGenAIContent](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/appgenaicontent). Eso permite aplicar nuevos controles de acceso sobre telemetría sensible de IA.

Para mí, aquí está el verdadero cambio conceptual. Durante bastante tiempo, muchas conversaciones sobre observabilidad de LLMs se han quedado en algo así como “quiero ver prompts y respuestas para depurar”. Y sí, claro, eso es útil. Pero en cuanto metes usuarios reales, documentos internos, historiales de conversación o datos de negocio, esa visibilidad deja de ser un lujo inocente. Pasa a ser un riesgo. Separar ese contenido en una tabla específica implica reconocer, por fin, que no toda telemetría merece el mismo tratamiento ni debería heredarlo por inercia de las prácticas que ya tenías en *App Insights*.

{{< figure src="/images/microsoft-foundry-da-un-paso-serio-en-observabilidad-trazas-de-agentes-y-telemet/body-3.png" alt="Esquema de separación entre telemetría operativa y contenido GenAI sensible" caption="Separar métricas operativas del contenido GenAI sensible es la decisión de diseño clave en esta nueva historia de observabilidad." >}}{{< /figure >}}

Además, la referencia de [AppGenAIContent en Azure Monitor Logs](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/appgenaicontent) ya deja ver columnas muy orientadas al dominio GenAI, como `AgentId` y `AgentName`. No parece una adaptación genérica hecha a posteriori para salir del paso. Se nota que Microsoft está modelando la telemetría con semántica de agente, y eso es una buena noticia porque facilita consultas más útiles y diagnósticos más precisos. Pero también te obliga a tomarte en serio la clasificación del dato que envías. Y ahí, como casi siempre, la tecnología ayuda, pero la disciplina la pones tú.

### Mi recomendación: separar observabilidad operativa de observabilidad de contenido

Si me preguntas cómo lo aterrizaría yo en una arquitectura real, haría una separación mental muy estricta entre dos capas. La primera es la observabilidad operativa: latencia, errores, reintentos, *tool calls*, consumo, correlaciones y dependencias. La segunda es la observabilidad de contenido: prompts, respuestas, fragmentos recuperados, argumentos de herramientas o contexto conversacional. La primera suele ser necesaria para casi todo el equipo técnico. La segunda, en cambio, debería estar mucho más restringida.

El hecho de que [Application Insights almacene el contenido GenAI en una tabla dedicada](https://azure.microsoft.com/updates?id=567594) me parece precisamente una invitación a diseñar permisos distintos. No todo desarrollador necesita ver el texto completo de un prompt de cliente para diagnosticar una subida de latencia. No todo analista necesita acceder a respuestas literales del modelo para evaluar la salud del sistema. Y no todo incidente justifica abrir el acceso a datos conversacionales sin control, porque eso es una pendiente resbaladiza bastante clásica (y bastante evitable).

Mi regla práctica sería esta:

- Acceso amplio a métricas y trazas operativas no sensibles;
- Acceso restringido y justificado al contenido GenAI;
- Revisión explícita de quién puede consultar `AppGenAIContent`;
- Retención y exportación evaluadas con criterios de privacidad, no solo de coste;
- Entornos de prueba con datos sintéticos siempre que sea posible.

**Observar mejor no significa mirar más cosas, sino mirar las correctas con el nivel correcto de permiso.** Y en GenAI ese matiz deja de ser burocracia para convertirse en diseño técnico puro.

### Qué puedes consultar y por qué importa

Una ventaja de que todo esto termine en Log Analytics es que puedes trabajar con consultas sobre tablas concretas. No hace falta inventar nada raro ni montar una capa paralela para empezar a extraer valor. Basta con ir a la tabla específica del contenido GenAI cuando realmente necesites analizar ese material.

Por ejemplo, una consulta inicial y deliberadamente simple para inspeccionar las últimas entradas podría ser esta:

```kusto
AppGenAIContent
| where TimeGenerated > ago(1h)
| where isnotempty(AgentId) // Evito ruido de filas incompletas al revisar actividad reciente por agente
| project TimeGenerated, AgentName, AgentId
| top 50 by TimeGenerated desc
```

No tiene misterio. Y precisamente por eso me parece un buen ejemplo. La parte interesante no está en la sintaxis, sino en el cambio de hábito: ya no asumes que el contenido de IA está desperdigado entre tablas genéricas o mezclado con telemetría que no toca. Ahora puedes localizarlo en [la tabla AppGenAIContent documentada por Azure Monitor](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/appgenaicontent) y decidir quién accede a ella, cuándo y para qué.

{{< figure src="/images/microsoft-foundry-da-un-paso-serio-en-observabilidad-trazas-de-agentes-y-telemet/source-4.png" alt="Vista de consulta y exploración de telemetría en Application Insights" caption="Cuando la telemetría llega a Log Analytics, puedes consultarla y convertirla en alertas o diagnósticos útiles. Fuente: [learn.microsoft.com](https://learn.microsoft.com/en-us/azure/foundry/observability/concepts/trace-agent-concept)" >}}{{< /figure >}}

A partir de ahí, lo razonable es cruzar esta información con otras señales de Application Insights para responder preguntas de diagnóstico reales. Qué agente falla más. Cuál consume más. Qué patrones de reintento preceden respuestas anómalas. O en qué momentos el coste sube sin una mejora clara del resultado. Esa es la parte que convierte la telemetría en capacidad operativa y no en simple acumulación de logs “por si acaso”, que es una tentación muy humana y muy cara.

### Lo que yo vigilaría antes de activarlo a lo grande

Hay tres riesgos que veo con bastante claridad. El primero es el de sobreinstrumentar: si capturas demasiado contenido demasiado pronto, te puedes meter en un problema de privacidad y de coste antes siquiera de haber demostrado valor. El segundo es el de permisos heredados: equipos acostumbrados a Application Insights como espacio relativamente abierto pueden descubrir demasiado tarde que GenAI introduce datos mucho más delicados. El tercero es el de falsa confianza por estar “integrado”: que algo acabe en Azure Monitor no significa automáticamente que tu gobierno del dato ya esté resuelto.

Por eso, antes de extender esta capacidad a todos los agentes, yo revisaría cuatro cosas. Quién tiene acceso hoy al recurso de Application Insights y al *workspace*. Qué tipos de prompts o respuestas podrían contener datos sensibles. Qué entornos necesitan contenido completo y cuáles pueden vivir con trazas parciales. Y qué procedimiento seguirás cuando alguien necesite acceso excepcional para investigar un incidente. Parece obvio, lo sé, pero muchas veces lo obvio solo parece obvio después de que algo falle.

### Mi lectura final

Creo que Microsoft Foundry está empezando a dar con el tono correcto en observabilidad para agentes. La combinación de [*tracing* de agentes en Foundry](https://learn.microsoft.com/en-us/azure/foundry/observability/concepts/trace-agent-concept), [visualización apoyada en Application Insights](https://learn.microsoft.com/en-us/semantic-kernel/concepts/enterprise-readiness/observability/telemetry-with-azure-ai-foundry-tracing) y [separación del contenido sensible en AppGenAIContent](https://azure.microsoft.com/updates?id=567594) va en la dirección adecuada. No porque te dé más paneles, ni porque añada otra palabra de moda al catálogo, sino porque empieza a asumir una realidad incómoda: en GenAI, depurar y proteger el dato tienen que diseñarse juntos.

Si tuviera que resumírtelo en una sola idea, sería esta: **la observabilidad útil para agentes no consiste solo en ver la ejecución, sino en decidir quién puede ver el contenido de esa ejecución**. Y ese matiz, que parece de gobierno, en realidad es arquitectura en estado puro.
