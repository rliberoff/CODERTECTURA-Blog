---
title: 'Microsoft Agent Framework en Build 2026: cómo pasar de un prototipo a un agente
  listo para producción'
date: '2026-07-01T10:07:38+00:00'
draft: true
slug: microsoft-agent-framework-en-build-2026-como-pasar-de-un-prototipo-a-un-agente-l
description: 'En Build 2026, Microsoft Agent Framework pone el foco donde de verdad
  importa: harnesses, aprobaciones, memoria, observabilidad y flujos multiagente en
  .NET.'
categories:
- Inteligencia Artificial
- .NET
- Arquitectura de Software
tags:
- Microsoft Agent Framework
- .NET
- Agentes de IA
- Observabilidad
- Arquitectura de Software
- Build 2026
image: /images/microsoft-agent-framework-en-build-2026-como-pasar-de-un-prototipo-a-un-agente-l/cover.png
comments: true
ai:
  assisted: true
  model: gpt-5.4
  prompt_version: 2026-06-30.5
  generated_at: '2026-07-01T10:07:38+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://developer.microsoft.com/blog/build-recap
    title: 'Microsoft Build 2026 recap: vision, launches, and top sessions'
    published_date: '2026-06-02'
  - url: https://devblogs.microsoft.com/dotnet/dotnet-at-microsoft-build-2026
    title: '.NET at Microsoft Build 2026: Must watch sessions'
    published_date: null
  - url: https://devblogs.microsoft.com/foundry/agent-service-build2026
    title: Build and run agents at scale with Microsoft Foundry at Build 2026
    published_date: null
  - url: https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-at-build-2026-announce
    title: 'Microsoft Agent Framework at BUILD 2026: Agent Harness, ...'
    published_date: null
  - url: https://devblogs.microsoft.com/agent-framework/agent-harness-working-with-your-data-safely/
    title: 'Agent Harness: Working with your data, safely'
    published_date: null
---

Si me preguntas qué ha cambiado de verdad en la conversación sobre agentes en Build 2026, yo lo resumiría así: hemos dejado de hablar solo de demos vistosas y hemos empezado a hablar de sistemas que tienen que sobrevivir al mundo real. Y ahí es donde, para mí, **Microsoft Agent Framework** se vuelve interesante de verdad.

Ya no basta con que un agente responda “más o menos bien” en una demo. Ahora importa cómo restringes herramientas, cómo introduces aprobación humana, qué memoria conservas, cómo observas su comportamiento y cómo coordinas varios agentes sin convertir tu arquitectura en una ceremonia esotérica (que también pasa).

En los resúmenes de Build 2026 y en las sesiones destacadas de .NET se ve bastante clara esa dirección: agentes más prácticos, más integrables con el ecosistema y más preparados para escenarios serios de empresa, no solo para pruebas rápidas ([Build recap](https://developer.microsoft.com/blog/build-recap), [.NET at Microsoft Build 2026](https://devblogs.microsoft.com/dotnet/dotnet-at-microsoft-build-2026)). Y en los anuncios específicos de Agent Framework el mensaje ya es directo: **Agent Harness**, estrategias de aprobación, múltiples tipos de memoria y flujos duraderos pasan al centro de la conversación ([Microsoft Agent Framework at BUILD 2026](https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-at-build-2026-announce), [Agent Harness: Working with your data, safely](https://devblogs.microsoft.com/agent-framework/agent-harness-working-with-your-data-safely/)).

### El salto importante no es “hacer un agente”, sino gobernarlo

Yo veo a muchos equipos atrapados en el mismo patrón. Montan un agente que llama a un modelo, le añaden dos o tres *tools* y, durante unos días, parece magia.

El problema llega cuando ese agente toca datos reales, ejecuta acciones con coste o se conecta a sistemas corporativos.

Ahí se acaba la magia y empieza la ingeniería.

Un agente listo para producción necesita, como mínimo:

- **Un perímetro operativo claro**, para saber qué puede y qué no puede hacer;
- **Aprobaciones explícitas**, cuando una acción es sensible;
- **Memoria controlada**, para no mezclar contexto útil con retención peligrosa;
- **Observabilidad**, para entender decisiones, herramientas y errores;
- **Orquestación duradera**, si el flujo tarda, espera entradas humanas o coordina varios agentes.

Eso encaja muy bien con lo que Microsoft ha ido presentando alrededor de Agent Framework y de Microsoft Foundry: la idea de que el valor ya no está solo en el modelo, sino en la plataforma operativa que envuelve al agente ([Microsoft Agent Framework at BUILD 2026](https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-at-build-2026-announce), [Build and run agents at scale with Microsoft Foundry at Build 2026](https://devblogs.microsoft.com/foundry/agent-service-build2026)).

{{< figure src="/images/microsoft-agent-framework-en-build-2026-como-pasar-de-un-prototipo-a-un-agente-l/body-1.png" alt="Diagrama del Agent Harness como capa de control" caption="El Agent Harness actúa como perímetro operativo entre el modelo, las herramientas, la memoria y las aprobaciones." >}}{{< /figure >}}

### Qué aporta Agent Harness y por qué me parece la pieza clave

De todo lo anunciado, **Agent Harness** me parece la pieza más relevante desde el punto de vista arquitectónico. La razón es bastante simple: un prototipo suele asumir que el agente tiene acceso libre a herramientas, archivos y contexto. En producción, eso es precisamente lo que yo no quiero.

El artículo sobre trabajo seguro con tus datos lo deja bastante claro: el harness es el punto en el que habilitas acceso a archivos, defines estrategias de aprobación para herramientas y eliges tipos de memoria ([Agent Harness: Working with your data, safely](https://devblogs.microsoft.com/agent-framework/agent-harness-working-with-your-data-safely/)). Dicho en lenguaje menos marketiniano: es la capa donde conviertes un agente “capaz” en un agente **gobernable**.

Yo lo resumiría con una regla muy sencilla:

> El modelo razona, pero el harness manda.

Y esa separación me parece sanísima. Evita que toda la seguridad dependa del prompt, que es una forma elegante de decir “estoy cruzando los dedos”. Si trabajas en .NET, esta idea probablemente ya te suena: se parece mucho a separar lógica de negocio de políticas de infraestructura. No le pides al modelo que “por favor se porte bien”; diseñas un contenedor operativo donde solo puede actuar dentro de límites explícitos.

### Aprobaciones: el detalle que separa confianza de pánico

En mi experiencia, el punto donde más rápido se rompe la confianza en un agente es este: **ejecuta una acción irreversible sin control humano**.

Y no hace falta pensar en escenarios exóticos. Piensa en cosas muy normales:

- Enviar un correo a un cliente;
- Modificar un pedido;
- Borrar un archivo;
- Publicar una incidencia;
- Ejecutar una operación costosa en una API externa.

Si el agente puede hacer eso directamente, el riesgo no es teórico. Es operativo, inmediato y bastante antipático.

Por eso me parece importante que Microsoft esté poniendo el foco en las **tool approval strategies** dentro del harness ([Agent Harness: Working with your data, safely](https://devblogs.microsoft.com/agent-framework/agent-harness-working-with-your-data-safely/)). No lo veo como un extra bonito; lo veo como una frontera de seguridad.

Yo suelo pensar en tres niveles de aprobación:

1. **Autoaprobado**: acciones de bajo riesgo, como consultar catálogos o recuperar documentación.
2. **Aprobación condicional**: acciones que pueden ejecutarse si cumplen reglas claras, por ejemplo importes bajos o entornos no productivos.
3. **Aprobación humana obligatoria**: acciones con impacto externo, económico o regulatorio.

Si diseñas esto bien, el agente sigue siendo útil sin ser temerario. Que ya es bastante.

### Memoria: útil, sí; infinita, mejor no

Otro mensaje interesante de Build 2026 es que la memoria deja de tratarse como un concepto abstracto y empieza a presentarse como una decisión de arquitectura. El artículo del harness habla de **multiple memory types** ([Agent Harness: Working with your data, safely](https://devblogs.microsoft.com/agent-framework/agent-harness-working-with-your-data-safely/)), y para mí ese es exactamente el enfoque correcto.

Porque “dar memoria al agente” no significa guardar todo sin pensar.

Yo separaría, como mínimo, estas capas:

- **Memoria de sesión**: lo que solo tiene sentido dentro de la conversación actual;
- **Memoria operativa**: estado necesario para completar un flujo en curso;
- **Memoria de preferencias**: datos persistentes del usuario, con reglas claras de retención;
- **Memoria recuperable desde conocimiento externo**: documentación, tickets, catálogos o políticas.

La trampa habitual es mezclarlo todo y acabar con un agente que recuerda demasiado, recuerda mal o recuerda cosas que no debería recordar. Y cuando eso ocurre, el problema no es solo de calidad. También puede ser de cumplimiento, privacidad y trazabilidad.

{{< figure src="/images/microsoft-agent-framework-en-build-2026-como-pasar-de-un-prototipo-a-un-agente-l/body-2.png" alt="Capas de memoria de un sistema de agentes" caption="No toda la memoria cumple la misma función: separar sesión, estado operativo, preferencias y conocimiento recuperable evita muchos problemas." >}}{{< /figure >}}

### Observabilidad: si no ves por qué actuó, no puedes operarlo

Aquí es donde muchos proyectos de IA siguen bastante verdes. Hay *logs* de aplicación, sí, pero faltan respuestas a las preguntas que de verdad importan:

- ¿Qué *tool* intentó usar el agente?
- ¿Por qué eligió esa acción?
- ¿Qué contexto recuperó?
- ¿Cuánto tardó cada paso?
- ¿Dónde falló: modelo, herramienta, red, política o dato?

La línea que Microsoft está empujando con Foundry en Build 2026 va justo hacia **observabilidad y ROI para agentes en cualquier framework**, además de la operación a escala ([Build and run agents at scale with Microsoft Foundry at Build 2026](https://devblogs.microsoft.com/foundry/agent-service-build2026)). Y yo aquí no tengo muchas dudas: este punto es crítico.

Sin telemetría útil, cualquier incidente acaba derivando en una discusión casi filosófica sobre “lo que quiso hacer el modelo”.

Y en producción, sinceramente, no te puedes permitir eso.

Necesitas trazas que te permitan reconstruir:

- La entrada del usuario;
- La recuperación de contexto;
- La selección de *tools*;
- La aprobación o el rechazo;
- La salida final;
- Las métricas de coste, latencia y error.

Si además trabajas con varios agentes, esta necesidad se multiplica. Ya no quieres solo *logs* aislados, sino una visión de extremo a extremo de todo el flujo.

{{< figure src="/images/microsoft-agent-framework-en-build-2026-como-pasar-de-un-prototipo-a-un-agente-l/source-3.webp" alt="Panel de Microsoft Foundry para operar agentes" caption="La operación real de agentes exige paneles, logs y trazabilidad; justo donde la observabilidad deja de ser opcional. Fuente: [devblogs.microsoft.com](https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-at-build-2026-announce)" >}}{{< /figure >}}

### Multiagente: útil cuando divide responsabilidades, peligroso cuando solo añade complejidad

Build 2026 también ha reforzado la conversación sobre arquitecturas con varios agentes y flujos distribuidos. En las fuentes aparece incluso un diagrama con múltiples agentes especializados colaborando dentro de un sistema más amplio ([Microsoft Agent Framework at BUILD 2026](https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-at-build-2026-announce)).

Yo aquí soy bastante conservador: **no montaría una arquitectura multiagente solo porque suena avanzada**.

Tiene sentido cuando hay una separación clara de responsabilidades, por ejemplo:

- Un agente de recepción interpreta la intención;
- Un agente de políticas valida restricciones;
- Un agente de datos consulta sistemas empresariales;
- Un agente resumidor genera una respuesta final;
- Un coordinador gestiona reintentos, esperas y aprobaciones.

Eso puede funcionar muy bien si cada agente tiene un contrato nítido. Pero si todos “hacen un poco de todo”, el sistema se vuelve opaco a una velocidad francamente admirable.

Mi criterio aquí es muy simple: si no puedes describir la responsabilidad de cada agente en una sola frase, probablemente todavía no necesitas varios.

### Workflows duraderos: donde realmente empieza la producción

Un detalle muy relevante de las fuentes es la referencia a **durable workflows** dentro del ecosistema de Agent Framework ([Agent Harness: Working with your data, safely](https://devblogs.microsoft.com/agent-framework/agent-harness-working-with-your-data-safely/)). A mí esto me parece fundamental, porque muchos procesos *agentic* no son síncronos ni instantáneos.

Piensa en un caso real:

1. El usuario pide tramitar una excepción;
2. El agente reúne contexto y propone una acción;
3. El sistema espera aprobación humana;
4. Después llama a un sistema externo;
5. Si falla, reintenta o deriva a otro camino;
6. Finalmente deja trazabilidad y notifica al usuario.

Eso ya no es “un prompt con *tools*”. Eso es un **workflow**.

Y cuando aceptas esa idea, el diseño mejora muchísimo. Dejas de meter toda la inteligencia en una sola llamada al modelo y empiezas a separar:

- Razonamiento;
- Políticas;
- Estado;
- Compensaciones;
- Observabilidad;
- Intervención humana.

{{< figure src="/images/microsoft-agent-framework-en-build-2026-como-pasar-de-un-prototipo-a-un-agente-l/source-4.webp" alt="Arquitectura con varios agentes especializados" caption="Una arquitectura multiagente tiene sentido cuando cada agente asume una responsabilidad concreta y observable. Fuente: [devblogs.microsoft.com](https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-at-build-2026-announce)" >}}{{< /figure >}}

### Un ejemplo sencillo de política de aprobación en .NET

No voy a inventarme APIs que no aparecen detalladas en las fuentes, pero sí puedo enseñarte el patrón que yo aplicaría en una aplicación .NET al integrar un agente con acciones sensibles: **ninguna *tool* crítica se ejecuta sin pasar antes por una política explícita**.

```csharp
public static class ToolApprovalPolicy
{
    private static readonly HashSet<string> AutoApprovedTools = new(StringComparer.Ordinal)
    {
        "SendCustomerEmail",
        "CreateSupportDraft"
    };

    private static readonly HashSet<string> HumanApprovalTools = new(StringComparer.Ordinal)
    {
        "RefundOrder",
        "DeleteCustomerFile",
        "CloseBillingCase"
    };

    public static ApprovalDecision Evaluate(string toolName, decimal? amount, bool isProduction)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(toolName);

        if (AutoApprovedTools.Contains(toolName))
            return ApprovalDecision.AutoApproved();

        if (toolName == "RefundOrder" && amount is <= 50m && !isProduction)
            return ApprovalDecision.AutoApproved(); // Limito el riesgo a importes bajos y fuera de producción

        if (HumanApprovalTools.Contains(toolName))
            return ApprovalDecision.RequiresHuman("Acción sensible o irreversible");

        return ApprovalDecision.Denied("Tool no autorizada por política");
    }
}

public sealed record ApprovalDecision(bool Allowed, bool RequiresHuman, string? Reason)
{
    public static ApprovalDecision AutoApproved() => new(true, false, null);
    public static ApprovalDecision RequiresHuman(string reason) => new(true, true, reason);
    public static ApprovalDecision Denied(string reason) => new(false, false, reason);
}
```

El código es deliberadamente simple, pero la idea importante es otra: la decisión no depende del entusiasmo del modelo, sino de una **política evaluable, auditable y testeable**.

Y sí, dicho así suena menos espectacular que “agente autónomo”, pero también suena bastante más parecido a producción.

### Mi hoja de ruta sensata para pasar a producción

Si hoy estuviera arrancando con Microsoft Agent Framework en .NET, yo no intentaría construir un sistema multiagente completo el primer día. Iría por fases.

**Fase 1: un agente, una tarea, pocas tools**

Primero validaría una capacidad concreta: por ejemplo, triado de incidencias internas o preparación de borradores.

**Fase 2: harness y límites operativos**

Después incorporaría acceso controlado a archivos, memoria mínima y reglas de aprobación desde el principio, siguiendo la dirección marcada por Agent Harness ([Agent Harness: Working with your data, safely](https://devblogs.microsoft.com/agent-framework/agent-harness-working-with-your-data-safely/)).

**Fase 3: observabilidad seria**

Antes de ampliar casos de uso, conectaría telemetría, trazas y paneles operativos. Si no puedes observarlo, no escales.

**Fase 4: workflows duraderos**

Cuando aparezcan esperas humanas, reintentos o integraciones lentas, modelaría el proceso como *workflow*, no como una única conversación larga.

**Fase 5: especialización multiagente**

Solo cuando haya cuellos de botella reales o dominios claramente distintos separaría agentes por responsabilidad.

### La idea de fondo que me deja Build 2026

Lo que más me gusta de la dirección que está tomando Microsoft aquí es que empieza a tratar los agentes como lo que son: **software con riesgos operativos**, no solo una capa simpática encima de un LLM.

Entre los anuncios de Build, el foco en Agent Framework, el papel del harness y el énfasis de Foundry en observabilidad y operación a escala, yo veo una narrativa bastante más madura que hace un año ([Build recap](https://developer.microsoft.com/blog/build-recap), [Microsoft Agent Framework at BUILD 2026](https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-at-build-2026-announce), [Build and run agents at scale with Microsoft Foundry at Build 2026](https://devblogs.microsoft.com/foundry/agent-service-build2026)).

Y si tú estás en .NET, aquí hay una puerta muy interesante: ya no se trata solo de “probar algo con IA”, sino de diseñar sistemas *agentic* con las mismas obsesiones sanas que aplicarías en cualquier *backend* serio — límites, trazabilidad, seguridad, estado y operaciones.

Para mí, ese es el verdadero titular: en Build 2026, Microsoft Agent Framework empieza a sonar menos a experimento y bastante más a plataforma sobre la que sí me plantearía construir producción.
