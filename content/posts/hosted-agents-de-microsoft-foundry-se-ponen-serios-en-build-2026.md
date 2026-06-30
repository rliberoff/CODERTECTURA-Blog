---
title: Hosted Agents de Microsoft Foundry se pone serio en Build 2026
date: '2026-06-30T13:22:31+00:00'
draft: true
slug: hosted-agents-de-microsoft-foundry-se-ponen-serios-en-build-2026
description: Analizo qué cambia en Hosted Agents tras Build 2026 y por qué el foco
  ya no está solo en crear agentes, sino en operarlos de verdad en producción.
categories:
- Inteligencia Artificial
- Azure
- Arquitectura de Software
tags:
- Microsoft Foundry
- Hosted Agents
- Agentes IA
- Azure
- Arquitectura de Software
image: /images/hosted-agents-de-microsoft-foundry-se-ponen-serios-en-build-2026/cover.png
comments: true
ai:
  assisted: true
  model: gpt-5.4
  prompt_version: 2026-06-30.4
  generated_at: '2026-06-30T13:22:31+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://devblogs.microsoft.com/foundry/hosted-agents-build26
    title: What's New in Hosted Agents in Foundry Agent Service | Microsoft Foundry
      Blog
    published_date: '2026-06-06'
  - url: https://azure.microsoft.com/en-us/blog/microsoft-build-2026-building-agentic-apps-with-microsoft-fabric-and-microsoft-databases
    title: 'Microsoft Build 2026: Building agentic apps with Microsoft Fabric and
      Microsoft Databases | Microsoft Azure Blog'
    published_date: null
  - url: https://devblogs.microsoft.com/foundry/agent-service-build2026
    title: Build and run agents at scale with Microsoft Foundry at Build 2026
    published_date: null
---

Si trabajas en una plataforma de IA, hay un momento bastante revelador en el que dejas de preguntarte si un agente «funciona» y empiezas a hacerte la pregunta incómoda de verdad: **¿esto se puede operar en serio?**

Es decir: con aislamiento, con observabilidad, con gobierno y con un runtime que no cambie de humor de un martes a un miércoles. Y justo ahí es donde, en mi opinión, está lo más interesante de la actualización de **Hosted Agents** en Microsoft Foundry presentada en Build 2026.

Yo no lo veo como un simple retoque cosmético del servicio. Lo que veo es un paso bastante claro hacia despliegues de agentes más serios, más gobernables y bastante más cercanos a lo que cualquiera esperaría de una plataforma de producción.

Microsoft ha presentado estas novedades en el anuncio específico de Hosted Agents dentro de Foundry Agent Service, y además las ha encajado en una visión más amplia de plataforma para agentes y aplicaciones *agentic* en Build 2026 ([Hosted Agents en Foundry Agent Service](https://devblogs.microsoft.com/foundry/hosted-agents-build26), [Build and run agents at scale with Microsoft Foundry at Build 2026](https://devblogs.microsoft.com/foundry/agent-service-build2026), [Building agentic apps with Microsoft Fabric and Microsoft Databases](https://azure.microsoft.com/en-us/blog/microsoft-build-2026-building-agentic-apps-with-microsoft-fabric-and-microsoft-databases)).

### La idea clave: menos «demo con tools», más runtime operable

Cuando un proveedor habla de agentes, muchas veces la conversación gira alrededor del modelo, del framework o de las *tool calls*. Está bien, claro. Pero si tú estás en el lado de plataforma, sabes que el cuello de botella real suele estar en otro sitio.

Normalmente está aquí:

- En cómo se hospeda el agente,
- En cómo evoluciona su runtime,
- En cómo controlo dependencias y herramientas,
- En cómo observo ejecuciones y fallos,
- Y en cómo separo entornos sin convertir el sistema en una caja negra con logo bonito.

Eso es lo que yo extraigo de los anuncios de Build 2026: **Hosted Agents madura como capa de ejecución**, no solo como una abstracción cómoda para levantar un agente deprisa y salir a hacer una demo.

{{< figure src="/images/hosted-agents-de-microsoft-foundry-se-ponen-serios-en-build-2026/body-1.png" alt="Diagrama del runtime de un hosted agent en producción" caption="Una forma útil de pensar Hosted Agents: identidad, herramientas, observabilidad y datos alrededor del runtime de ejecución." >}}{{< /figure >}}

### Qué cambia en Hosted Agents

Aunque el material público de Build 2026 mete estas novedades dentro de una narrativa de plataforma más amplia, el mensaje específico sobre Hosted Agents me parece bastante claro. Yo lo resumiría en tres frentes.

### 1) El hosting deja de ser «infra invisible» y pasa a formar parte del contrato operativo

Este punto me parece especialmente importante.

En una primera etapa, muchos servicios administrados venden la idea de «olvídate de la infraestructura». Y oye, para arrancar está fenomenal. El problema aparece cuando necesitas pasar una revisión de seguridad, justificar latencias, aislar cargas o explicar qué versión del runtime está ejecutando una capacidad crítica.

Ahí ya no te basta con que la infraestructura sea invisible. Lo que necesitas es que sea **gobernable**.

Con el refresh de Build 2026, Hosted Agents se presenta más alineado con esa realidad: el hosting no desaparece mágicamente, sino que se convierte en una capa operable dentro de Foundry Agent Service ([Hosted Agents en Foundry Agent Service](https://devblogs.microsoft.com/foundry/hosted-agents-build26)).

Dicho de otra forma: el servicio sigue abstrayendo complejidad, sí, pero ahora el valor no está solo en ocultarla, sino en hacerla **gestionable**.

### 2) El runtime evoluciona hacia una plataforma más estable y componible

La segunda idea fuerte es el **runtime**. Y aquí yo haría una distinción que, sinceramente, muchas veces se mezcla demasiado.

- Una cosa es el **modelo** que razona o genera.
- Otra muy distinta es el **runtime** que coordina herramientas, estado, ejecución, políticas y observabilidad.

El refresh de Hosted Agents refuerza precisamente esa segunda capa. A mí me sugiere una transición desde un enfoque centrado en «invocar un agente con herramientas» hacia otro más parecido a un **entorno de ejecución duradero**, donde importan de verdad la consistencia del comportamiento, el aislamiento y la trazabilidad.

Y eso encaja muy bien con la visión más amplia de Microsoft Foundry como plataforma para construir y ejecutar agentes a escala, conectados con datos empresariales, herramientas y capacidades de observabilidad ([Build and run agents at scale with Microsoft Foundry at Build 2026](https://devblogs.microsoft.com/foundry/agent-service-build2026)).

### 3) La conversación ya no va de agentes aislados, sino de sistemas conectados con datos y contexto empresarial

El tercer cambio no afecta solo al hosting, pero sí cambia por completo cómo conviene diseñarlo.

Microsoft está empujando una historia en la que los agentes ya no viven aislados. Se apoyan en capas de datos, en contexto semántico y en sistemas empresariales, incluyendo Fabric y bases de datos de Microsoft ([Building agentic apps with Microsoft Fabric and Microsoft Databases](https://azure.microsoft.com/en-us/blog/microsoft-build-2026-building-agentic-apps-with-microsoft-fabric-and-microsoft-databases)).

Para mí, eso cambia la pregunta importante.

Ya no basta con decir: **«¿dónde corre el agente?»**

La pregunta buena ahora es esta:

**¿cómo corre ese agente dentro de un sistema con contexto, herramientas, memoria operativa, límites de seguridad y observabilidad extremo a extremo?**

Y no, no es una diferencia semántica. Es una diferencia arquitectónica.

### Cómo está evolucionando el runtime, de verdad

Si bajo todo esto a arquitectura, yo resumiría la evolución del runtime en cinco movimientos bastante claros.

### Aislamiento más explícito

En producción, un agente no es solo una función con un prompt más o menos adornado. Puede ejecutar herramientas, conectarse a datos, llamar a APIs internas, manipular credenciales y provocar efectos laterales. Eso exige fronteras claras.

Cuanto más madura una plataforma de hosted agents, más necesitas:

- Identidad por agente o por *workload*,
- Límites de red y acceso a recursos,
- Separación entre desarrollo, validación y producción,
- Y control real sobre qué herramientas están disponibles en ejecución.

Mi lectura del refresh es que Foundry quiere empujar Hosted Agents justo en esa dirección: una ejecución más apta para escenarios empresariales y menos pensada solo para prototipos aparentes.

### Ciclo de vida del runtime más visible

Uno de los grandes problemas en plataformas de agentes es el clásico «funcionaba ayer». Cambia una dependencia, cambia una herramienta, cambia un comportamiento del modelo o del runtime… y de repente tu agente ya no responde igual.

Por eso yo me fijo mucho en si el proveedor trata el runtime como un elemento con ciclo de vida propio. Cuando eso pasa, ya puedes empezar a hablar con más seriedad de:

- Versionado,
- Validación antes de promover cambios,
- Compatibilidad entre capacidades,
- Y *rollout* controlado.

Yo no necesito que el proveedor me enseñe cada tripa interna del sistema. Lo que necesito es que el runtime deje de comportarse como magia. Y Build 2026 apunta justo en esa dirección: un Foundry Agent Service más preparado para operar agentes a escala y con más disciplina de plataforma ([Build and run agents at scale with Microsoft Foundry at Build 2026](https://devblogs.microsoft.com/foundry/agent-service-build2026)).

### Observabilidad como parte del producto, no como parche tardío

Si me obligaras a elegir una sola diferencia entre una demo y producción, yo elegiría esta sin dudar: **en producción necesito entender qué ha hecho el agente y por qué**.

Eso implica capturar, como mínimo:

- Entradas y contexto relevante,
- Llamadas a herramientas,
- Dependencias externas,
- Resultados intermedios,
- Errores y *timeouts*,
- Coste y latencia por ejecución.

Foundry ya venía posicionando Agent Service con foco en seguridad y observabilidad, y el refresh de Hosted Agents refuerza precisamente el valor de esa capa operativa ([Hosted Agents en Foundry Agent Service](https://devblogs.microsoft.com/foundry/hosted-agents-build26)).

{{< figure src="/images/hosted-agents-de-microsoft-foundry-se-ponen-serios-en-build-2026/source-2.webp" alt="Vista de la plataforma de agentes de Microsoft" caption="La visión de plataforma importa: Hosted Agents gana sentido cuando lo sitúo dentro de una arquitectura de agentes más amplia. Fuente: [devblogs.microsoft.com](https://devblogs.microsoft.com/foundry/hosted-agents-build26)" >}}{{< /figure >}}

### Más composición con la plataforma Foundry

Otra señal bastante clara es que Hosted Agents no se vende como una pieza aislada, sino dentro de una **Agent Platform** más grande, donde aparecen GitHub, Azure, capacidades de distribución, optimización y contexto empresarial alrededor de Microsoft Agent Platform / Foundry ([Hosted Agents en Foundry Agent Service](https://devblogs.microsoft.com/foundry/hosted-agents-build26), [Build and run agents at scale with Microsoft Foundry at Build 2026](https://devblogs.microsoft.com/foundry/agent-service-build2026)).

Arquitectónicamente, esto importa mucho. Significa que el runtime del agente deja de ser un endpoint suelto y pasa a ser una pieza dentro de una cadena bastante más amplia:

- Desarrollo,
- Despliegue,
- Conexión con herramientas,
- *Grounding* con datos,
- Observación,
- Y mejora continua.

### Qué cambia para un despliegue serio en producción

Aquí está la parte práctica. Si ya tienes agentes corriendo, o estás a punto de llevarlos a producción, estas novedades cambian varias decisiones.

### 1) Diseña el agente como un workload, no como un prompt vitaminado

Yo evitaría pensar en Hosted Agents como «un sitio donde ejecutar prompts con tools». Me parece mucho más sano tratarlos como **workloads de plataforma** con sus propias SLO, dependencias, políticas y telemetría.

Eso te obliga a hacerte preguntas mejores:

- ¿Qué identidad usa este agente?
- ¿Qué recursos puede tocar?
- ¿Qué herramientas están permitidas en cada entorno?
- ¿Qué *timeout* máximo acepto por tipo de tarea?
- ¿Qué hago si falla una herramienta externa?
- ¿Qué señales recojo para auditar decisiones?

### 2) Separa mentalmente control plane y data plane

Aunque el marketing muchas veces mezcle todo en una misma diapositiva (esto tampoco es nuevo), a mí me ayuda muchísimo separar estas dos capas:

- **Control plane**: configuración, despliegue, políticas, observabilidad, gestión;
- **Data plane**: ejecución real de prompts, tools, contexto y llamadas.

Con la evolución de Hosted Agents, esta distinción gana todavía más valor porque el servicio parece avanzar hacia una operación más rica y más gobernable. Si no separas mentalmente ambas capas, acabarás mezclando configuración con ejecución y luego vendrán los incidentes raros, la auditoría dolorosa y el *troubleshooting* infinito.

### 3) Trata el runtime como una dependencia crítica

Igual que controlas una versión de .NET, de un contenedor base o de una librería de inferencia, yo creo que deberías tratar el runtime del agente como una dependencia crítica de plataforma.

Mi recomendación práctica sería:

- Tener un entorno de preproducción que replique herramientas y políticas reales;
- Validar agentes con casos de regresión antes de promover cambios;
- Observar cambios de latencia y comportamiento, no solo errores duros;
- Y documentar explícitamente qué capacidades del runtime asume cada agente.

### 4) Revisa tus patrones de tool calling

Cuanto más sólido es el runtime, menos sentido tiene diseñar *tool calling* caótico. Yo revisaría especialmente:

- Herramientas con efectos laterales fuertes,
- Cadenas largas de herramientas dependientes entre sí,
- Herramientas con contratos poco tipados,
- Y conectores que devuelven datos ambiguos o excesivos.

En una plataforma más madura, el runtime te ayudará, sí. Pero si el diseño del agente es débil, el resultado seguirá siendo frágil. **Y aquí no hay magia.**

### 5) Observa por conversación, pero también por operación de negocio

Este punto conecta muy bien con la visión de datos y contexto empresarial que Microsoft está reforzando con Fabric y bases de datos. A mí no me basta con saber que «la conversación fue bien». Necesito saber si el agente **resolvió la operación** que realmente importaba al negocio ([Building agentic apps with Microsoft Fabric and Microsoft Databases](https://azure.microsoft.com/en-us/blog/microsoft-build-2026-building-agentic-apps-with-microsoft-fabric-and-microsoft-databases)).

Por ejemplo:

- ¿Consiguió cerrar una incidencia?,
- ¿Recuperó correctamente el dato autorizado?,
- ¿Generó una acción válida en el sistema?,
- ¿Escaló cuando debía?

Si solo mides tokens, latencia y una satisfacción superficial, te vas a quedar corto.

### Un ejemplo sencillo de contrato operativo

No tengo en las fuentes un SDK o una API concreta suficientemente detallada como para inventarme código de despliegue sin correr el riesgo de alucinar nombres. Y prefiero no rellenar por rellenar (para eso ya está medio internet).

Pero sí puedo dejarte un artefacto realista y útil: un **contrato operativo mínimo** que yo exigiría a cualquier hosted agent antes de pasar a producción.

```yaml
agent: customer-support-triage
runtime:
  environment: prod
  max_turn_duration_seconds: 25   # Limito la duración del turno para que una conversación no degrade la cola completa
  tool_call_timeout_seconds: 8
security:
  identity: managed
  allowed_tools:
    - search-kb
    - create-ticket
    - get-customer-profile
observability:
  trace_conversation: true
  trace_tool_calls: true
  capture_latency_ms: true
  capture_failure_reason: true
resilience:
  retry_on_tool_timeout: 1
  fallback_action: escalate-to-human
```

No es un manifiesto oficial de Foundry. Es, más bien, una forma de aterrizar el cambio mental que yo creo que Build 2026 está empujando: un hosted agent debería tener un **contrato de operación explícito**.

### Mi lectura final

Si me preguntas qué aporta realmente este refresh de Hosted Agents, yo lo resumiría así: Microsoft Foundry está intentando cerrar la distancia entre **agentes que impresionan en una demo** y **agentes que puedes operar con cierta tranquilidad en producción**.

Eso se nota en el énfasis sobre runtime, escala, integración con la plataforma más amplia de agentes y conexión con capas de datos y contexto empresarial. Y, sinceramente, a mí me parece el camino correcto.

El reto ya no es solo construir agentes capaces. El reto es construir agentes que:

- Se desplieguen con control,
- Evolucionen sin sorpresas,
- Se puedan observar,
- Respeten límites de seguridad,
- Y encajen en una arquitectura empresarial real.

Ahí es donde Hosted Agents empieza a ponerse interesante de verdad.

Si yo estuviera revisando una plataforma de IA hoy, después de Build 2026 haría tres cosas de inmediato:

1. Inventariar qué agentes siguen todavía en modo «demo evolucionada»;
2. Definir un contrato operativo por agente;
3. Separar claramente runtime, herramientas, identidad y observabilidad en el diseño.

Porque el mensaje de fondo, al menos como yo lo leo, es bastante claro: en Foundry los agentes ya no se están presentando solo como una capacidad de IA, sino como una **unidad de ejecución de plataforma**.

Y eso, para bien, cambia bastante las reglas del juego.
