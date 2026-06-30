---
title: 'Microsoft Build 2026: así encaja la nueva ola agentic entre .NET, Azure, Visual
  Studio y GitHub'
date: '2026-06-30T12:01:58+00:00'
draft: true
slug: microsoft-build-2026-asi-encaja-la-nueva-ola-agentic-entre-dotnet-azure-visual-s
description: 'Mi lectura de Build 2026: ya no veo piezas sueltas, sino una arquitectura
  coherente para desarrollo agentic sobre .NET, Azure, Visual Studio, Aspire, Foundry
  y GitHub.'
categories:
- Inteligencia Artificial
- .NET
- Arquitectura de Software
tags:
- Microsoft Build
- Desarrollo agentic
- .NET 11
- Azure
- GitHub Copilot
- Visual Studio
image: /images/microsoft-build-2026-asi-encaja-la-nueva-ola-agentic-entre-dotnet-azure-visual-s/cover.png
comments: true
ai:
  assisted: true
  model: gpt-5.4
  prompt_version: 2026-06-30.3
  generated_at: '2026-06-30T12:01:58+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://developer.microsoft.com/blog/build-recap
    title: 'Microsoft Build 2026 recap: vision, launches, and top sessions'
    published_date: '2026-06-02'
  - url: https://devblogs.microsoft.com/visualstudio/whats-coming-next-in-visual-studio-our-microsoft-build-2026-announcements
    title: 'What’s Coming Next in Visual Studio: Our Microsoft Build 2026 Announcements'
    published_date: null
  - url: https://github.blog/news-insights/product-news/github-copilot-app-the-agent-native-desktop-experience/
    title: 'GitHub Copilot app: The agent-native desktop experience'
    published_date: null
  - url: https://devblogs.microsoft.com/dotnet/dotnet-at-microsoft-build-2026
    title: '.NET at Microsoft Build 2026: Must watch sessions'
    published_date: null
  - url: https://azure.microsoft.com/en-us/blog/microsoft-build-2026-building-agentic-apps-with-microsoft-fabric-and-microsoft-databases
    title: 'Microsoft Build 2026: Building agentic apps with Microsoft Fabric and
      Microsoft Databases | Microsoft Azure Blog'
    published_date: null
---

Si me preguntas qué es lo más importante que me llevo de Microsoft Build 2026, yo no te hablaría de un producto concreto ni de la demo más vistosa de la keynote. Me quedo con algo bastante más útil para quienes vivimos metidos en arquitectura de software: por fin veo una historia técnica razonablemente coherente entre **.NET, Visual Studio, GitHub Copilot, Aspire y Azure** para construir software con agentes sin caer en el festival del parche improvisado.

Y sí, para mí eso vale bastante más que cualquier *wow moment* de escenario.

La recap oficial de Build deja claro que el mensaje general del evento gira alrededor de visión, lanzamientos y sesiones centradas en esta nueva forma de desarrollar, con los agentes ocupando una posición cada vez más central en el stack ([developer.microsoft.com](https://developer.microsoft.com/blog/build-recap)). A eso se suma el foco específico en **Visual Studio**, en el recorrido de **.NET en Build 2026**, en la evolución de **GitHub Copilot** hacia una experiencia más *agent-native* y en toda la parte de **datos y plataforma** para aplicaciones agentic sobre Azure, Fabric y bases de datos ([Visual Studio](https://devblogs.microsoft.com/visualstudio/whats-coming-next-in-visual-studio-our-microsoft-build-2026-announcements), [.NET](https://devblogs.microsoft.com/dotnet/dotnet-at-microsoft-build-2026), [GitHub](https://github.blog/news-insights/product-news/github-copilot-app-the-agent-native-desktop-experience/), [Azure](https://azure.microsoft.com/en-us/blog/microsoft-build-2026-building-agentic-apps-with-microsoft-fabric-and-microsoft-databases)).

Mi lectura es bastante simple: **ya no estoy viendo solo asistentes de código; estoy viendo el inicio de una arquitectura asistida por agentes**.

### Lo importante no es el agente, sino el sistema que lo rodea

Aquí es donde yo haría una pausa. En cuanto aparece la palabra *agentic*, mucha gente piensa enseguida en un chatbot con acceso a herramientas. Y ya. A mí ese marco se me queda corto.

Para que un sistema agentic tenga sentido en producción, yo necesito al menos cinco cosas:

- un entorno de desarrollo que entienda intención y contexto;
- un runtime y un lenguaje con un buen modelo de composición;
- una forma clara de orquestar servicios distribuidos;
- una plataforma de datos y modelos que pueda gobernar;
- y un flujo de entrega en el que los agentes no destrocen la trazabilidad ni el control.

Eso es justamente lo que me parece interesante de Build 2026: **Microsoft está empezando a conectar esas cinco capas** en lugar de venderlas como piezas aisladas que, supuestamente, ya encajarán solas por arte de magia.

{{< figure src="/images/microsoft-build-2026-asi-encaja-la-nueva-ola-agentic-entre-dotnet-azure-visual-s/body-1.png" alt="Diagrama conceptual del stack agentic de Microsoft" caption="Yo lo veo así: experiencia de desarrollo, runtime, orquestación y plataforma de datos empiezan a formar una sola historia." >}}{{< /figure >}}

### Visual Studio y GitHub Copilot: del autocompletado a la colaboración operativa

La parte de Visual Studio en Build 2026 apunta claramente a ese cambio de etapa ([devblogs.microsoft.com](https://devblogs.microsoft.com/visualstudio/whats-coming-next-in-visual-studio-our-microsoft-build-2026-announcements)). Y GitHub remata la jugada presentando Copilot como una experiencia de escritorio *agent-native*; es decir, no solo como una caja de sugerencias incrustada en el editor, sino como una superficie donde los agentes pueden trabajar “como tú ya trabajas” ([github.blog](https://github.blog/news-insights/product-news/github-copilot-app-the-agent-native-desktop-experience/)).

¿Por qué creo que esto cambia el trabajo diario de arquitectura?

Porque el problema real nunca fue generar una línea de código. El problema de verdad era otro:

- entender el contexto del repositorio;
- relacionar código, incidencias y documentación;
- proponer cambios en varios puntos a la vez;
- y hacerlo sin que tú pierdas el control.

Si esta capa madura de verdad, yo no la usaría solo para “programar más rápido”. La usaría para **subir el nivel de abstracción de las tareas**. Por ejemplo:

- «revisa esta API y detecta contratos inconsistentes»;
- «propón una partición por *bounded contexts*»;
- «encuentra los puntos donde la resiliencia no está alineada»;
- «prepara un cambio transversal y explícame sus riesgos».

Dicho de otra forma: el IDE y Copilot empiezan a parecerse menos a una herramienta de escritura y más a un **entorno de trabajo cognitivo**. Y eso, si sale bien, cambia mucho más que el autocompletado.

### .NET 11 no es solo una versión: es una base para software más componible

La entrada dedicada a .NET en Build 2026 pone el foco en las sesiones clave del ecosistema ([devblogs.microsoft.com](https://devblogs.microsoft.com/dotnet/dotnet-at-microsoft-build-2026)). No pretende documentar cada detalle técnico —ni falta que hace en un resumen de evento—, pero sí refuerza una idea que yo llevo tiempo defendiendo: **.NET está muy bien posicionado para soportar esta ola agentic**.

¿La razón? Cuando construyo sistemas con agentes, necesito varias cualidades que .NET me da bastante bien:

- tipado fuerte para contratos y herramientas;
- buen rendimiento para servicios de backend;
- observabilidad madura;
- integración natural con cloud;
- y una experiencia sólida para aplicaciones distribuidas.

A mí no me interesa vender el relato de “el agente lo hará todo”. De hecho, suelo pensar lo contrario: cuanto más autónomo pretendo que sea un sistema, **más importante se vuelve el contrato explícito**. Y ahí .NET sigue jugando muy bien.

Si tuviera que resumir la relación entre .NET 11 y esta tendencia en una sola frase, sería esta: **menos magia implícita, más composición fiable**.

### Aspire es la pieza que le da forma a la arquitectura

Si hay un componente que, para mí, conecta muy bien todo esto, ese es **.NET Aspire**. No porque sea “la solución definitiva” (ya me gustaría a mí que estas cosas fueran tan fáciles), sino porque aporta algo que echo muchísimo de menos en muchas demos de IA: **estructura operacional**.

En un sistema agentic real, rara vez tengo una sola aplicación. Lo habitual es encontrar algo más parecido a esto:

- una API principal;
- uno o varios *workers*;
- conectores a colas o bases de datos;
- servicios de observabilidad;
- integración con modelos o herramientas externas;
- y políticas de configuración por entorno.

Aspire encaja muy bien en ese escenario porque ayuda a describir y ejecutar el sistema distribuido como una unidad coherente. Y para mí eso es clave. **Si un agente puede actuar sobre varios componentes, yo necesito ver con claridad el mapa del sistema**.

No quiero quedarme en el eslogan, así que te dejo un ejemplo mínimo y concreto de composición con Aspire para una solución donde una API y un *worker* comparten una cola y una base de datos. Aquí la gracia no está en la sintaxis, sino en dejar las dependencias explícitas desde el principio.

```csharp
var builder = DistributedApplication.CreateBuilder(args);

var postgres = builder.AddPostgres("pg")
    .AddDatabase("ordersdb");

var redis = builder.AddRedis("cache");
var serviceBus = builder.AddAzureServiceBus("bus");

var ordersApi = builder.AddProject<Projects.Orders_Api>("orders-api")
    .WithReference(postgres)
    .WithReference(redis)
    .WithReference(serviceBus);

builder.AddProject<Projects.Orders_AgentWorker>("orders-agent-worker")
    .WithReference(postgres)
    .WithReference(serviceBus)
    .WithReference(ordersApi); // Hago explícita la relación porque el worker depende de contratos vivos de la API

builder.Build().Run();
```

Lo importante aquí no es “que Aspire arranque cosas”. Lo importante es el efecto arquitectónico: **declaro dependencias claras entre piezas que un agente podría observar, invocar o afectar**. Y eso me da una base mucho mejor para gobernar comportamiento, telemetría y despliegue.

### Azure, Foundry, Fabric y bases de datos: un agente necesita contexto, no solo modelo

La parte de Azure en Build 2026 me parece especialmente relevante porque aterriza una verdad que a veces se olvida con una facilidad pasmosa: un agente sirve de poco si no tiene **datos, contexto y herramientas fiables**. El artículo sobre aplicaciones agentic con Microsoft Fabric y Microsoft Databases va precisamente por ahí ([azure.microsoft.com](https://azure.microsoft.com/en-us/blog/microsoft-build-2026-building-agentic-apps-with-microsoft-fabric-and-microsoft-databases)).

Yo lo reduzco a un principio muy simple:

> el valor no está en “enchufar un modelo”, sino en conectar el agente con el contexto operacional correcto.

Y eso, llevado a arquitectura, implica varias decisiones nada triviales:

- qué datos puede consultar;
- con qué semántica los interpreta;
- qué herramientas puede ejecutar;
- cómo registro trazas y decisiones;
- y dónde coloco los límites de seguridad.

La mención a **Microsoft Foundry**, **Fabric** y a las capas de datos y analítica me encaja perfectamente aquí. Porque si quiero construir aplicaciones agentic serias, necesito bastante más que inferencia:

- catálogo de capacidades;
- gobierno del acceso;
- observabilidad;
- y una capa de datos preparada para servir contexto útil.

{{< figure src="/images/microsoft-build-2026-asi-encaja-la-nueva-ola-agentic-entre-dotnet-azure-visual-s/source-2.gif" alt="Arquitectura en capas de contexto de datos para aplicaciones agentic" caption="La capa de datos y contexto importa tanto como el modelo: sin semántica y gobierno, el agente se queda corto. Fuente: [azure.microsoft.com](https://azure.microsoft.com/en-us/blog/microsoft-build-2026-building-agentic-apps-with-microsoft-fabric-and-microsoft-databases)" >}}{{< /figure >}}

Dicho sin rodeos: el agente no sustituye la arquitectura de datos. **La vuelve todavía más importante**.

### La historia completa: del desarrollador aumentado al sistema aumentado

Lo más potente de Build 2026, al menos como yo lo veo, es que empieza a dibujarse una transición bastante clara:

1. **Primera fase**: IA para ayudarme a escribir código.
2. **Segunda fase**: IA para colaborar en tareas de desarrollo más complejas.
3. **Tercera fase**: agentes integrados en el ciclo de vida del software y en la operación del sistema.

Mi impresión es que Microsoft está intentando cubrir esas tres fases a la vez:

- **Visual Studio** y **GitHub Copilot** en la experiencia del desarrollador;
- **.NET 11** como base de composición y ejecución;
- **Aspire** como pegamento de la aplicación distribuida;
- **Azure / Foundry / Fabric / Databases** como plataforma de contexto, herramientas y gobierno.

Y eso cambia cómo pienso yo la arquitectura. Ya no diseño solo servicios para usuarios o integraciones entre sistemas. Cada vez más, también voy a tener que diseñar:

- **servicios consumidos por agentes**;
- **herramientas invocables por agentes**;
- **flujos con supervisión humana**;
- **observabilidad orientada a decisiones**;
- y **límites explícitos de autonomía**.

### Qué haría yo mañana en un equipo .NET

Si después de Build 2026 me pidieras una hoja de ruta sensata, yo no empezaría montando un “superagente” que promete resolverlo todo (esas ideas suelen envejecer mal). Haría algo bastante más aburrido. Y bastante más efectivo.

Empezaría por esto:

- identificar un proceso con alto coste cognitivo y bajo riesgo;
- aislar bien sus contratos y sus fuentes de datos;
- montarlo como un flujo observable dentro de una solución distribuida;
- y dejar que el agente actúe solo en un perímetro muy acotado.

Por ejemplo:

- clasificación y enriquecimiento de incidencias;
- análisis de cambios en APIs internas;
- generación guiada de propuestas de refactor;
- o automatización de tareas de soporte sobre datos operacionales.

Lo crítico aquí no es la espectacularidad. Lo crítico es que puedas responder con claridad a estas preguntas:

- ¿qué sabe el agente?
- ¿qué puede hacer?
- ¿qué no puede hacer?
- ¿cómo veo sus decisiones?
- ¿cómo revoco o limito su actuación?

Si no tengo respuestas claras para eso, yo no diría que tengo arquitectura agentic. Diría que tengo una demo bonita. Y ya.

### Mi conclusión: Build 2026 no va de *features*, va de madurez del stack

La recap general de Build 2026 me deja la sensación de que Microsoft quiere articular una plataforma donde los agentes formen parte del trabajo diario del desarrollador y también del propio software ([developer.microsoft.com](https://developer.microsoft.com/blog/build-recap)). Y cuando junto eso con lo anunciado para Visual Studio, la evolución de GitHub Copilot, el recorrido de .NET y el peso creciente de Azure en datos, modelos y herramientas, lo que veo es una dirección bastante consistente.

Mi conclusión personal es esta: **la novedad no es que haya más IA en el stack; la novedad es que el stack empieza a organizarse alrededor de la IA con criterio arquitectónico**.

Eso no elimina los riesgos. Tampoco garantiza el éxito. Pero sí cambia el terreno de juego.

Y, sinceramente, hacía tiempo que no veía un Build en el que la conversación entre herramientas, runtime, plataforma y arquitectura tuviera tanto sentido de conjunto.
