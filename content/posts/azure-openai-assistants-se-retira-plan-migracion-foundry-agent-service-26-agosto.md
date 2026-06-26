---
title: 'Azure OpenAI Assistants se retira: plan de migración al Foundry Agent Service
  antes del 26 de agosto de 2026'
date: '2026-06-26T10:41:02+00:00'
draft: true
slug: azure-openai-assistants-se-retira-plan-migracion-foundry-agent-service-26-agosto
description: Qué cambia con la retirada de Assistants API y cómo preparar la migración
  al Foundry Agent Service sin parar tus entregas.
categories:
- Inteligencia Artificial
- Azure
- .NET
tags:
- Azure OpenAI
- Foundry Agent Service
- Migración
- .NET
- IA generativa
image: /images/azure-openai-assistants-se-retira-plan-migracion-foundry-agent-service-26-agosto/cover.png
comments: true
ai:
  assisted: true
  model: gpt-5.4-mini
  prompt_version: 2026-06-24.2
  generated_at: '2026-06-26T10:41:02+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://learn.microsoft.com/en-in/answers/questions/5928817/retirement-notice-lz-6-y1z-(azure-openai-assistant
    title: Retirement notice LZ_6-Y1Z (Azure OpenAI Assistants) shows no ...
    published_date: '2026-06-24'
  - url: https://devblogs.microsoft.com/foundry/whats-new-in-microsoft-foundry-may-2026
    title: What's new in Microsoft Foundry | May 2026 | Microsoft Foundry Blog
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/foundry/concepts/general-availability
    title: New Microsoft Foundry portal general availability overview
    published_date: '2026-06-19'
---

Azure OpenAI Assistants tiene fecha de retirada y eso obliga a muchos equipos a mover ficha antes de que el calendario les alcance. Si hoy tenéis flujos en producción con Assistants API, este no es un cambio cosmético: afecta al contrato con el SDK, al modelo operativo y, en muchos casos, a la forma en que organizáis conversaciones, herramientas y observabilidad.

La buena noticia es que la ventana de trabajo existe y, si la aprovechamos bien, la migración puede ser una oportunidad para limpiar deuda técnica y aterrizar una base más sólida en Foundry. Microsoft sitúa el nuevo portal de Foundry como una plataforma GA orientada a escenarios empresariales, con gobierno y controles integrados en todo el ciclo de vida de las soluciones de IA ([fuente](https://learn.microsoft.com/en-us/azure/foundry/concepts/general-availability)). Además, la comunidad ya está viendo avisos de retirada relacionados con Azure OpenAI Assistants y la necesidad de planificar la transición ([fuente](https://learn.microsoft.com/en-in/answers/questions/5928817/retirement-notice-lz-6-y1z-(azure-openai-assistant)).

### Qué significa realmente la retirada

Cuando una API entra en retirada, el riesgo no es solo “que deje de funcionar” en una fecha concreta. El problema real empieza antes:

- nuevas funcionalidades ya no llegan a ese camino
- cualquier bug o limitación se convierte en un riesgo operativo
- los equipos dejan de poder asumir que el proveedor les protegerá de cambios futuros
- la deuda técnica se acumula justo donde menos conviene: en IA conversacional y automatización de herramientas

En la práctica, esto significa que si seguís en Assistants API deberíais tratar la migración como un programa de producto, no como una tarea aislada de backend.

### Qué deberíais inventariar esta semana

Antes de escribir una sola línea de código, necesitamos saber qué está en juego. Os proponemos un inventario mínimo:

- **Assistants existentes**: cuántos tenéis, en qué entorno viven y quién los mantiene
- **Threads y runs**: si dependéis de una persistencia concreta de conversación
- **Tools**: funciones, code interpreter, retrieval, function calling y herramientas propias
- **Modelos**: qué modelo usa cada flujo y si hay dependencia de un modelo concreto
- **Guardrails**: moderación, filtros, validaciones de entrada y salida
- **Telemetría**: logs, métricas, trazas y correlación con el sistema principal
- **Seguridad**: secretos, identidades, permisos y acceso a datos
- **Experiencia de usuario**: streaming, latencia percibida y estados intermedios

Si no podéis responder a estas preguntas con precisión, la migración va a ser más difícil de lo que parece.

### Riesgos habituales que hemos visto en este tipo de migraciones

No todos los equipos fallan por el mismo motivo, pero sí se repiten varias trampas:

1. **Acoplar la UI al proveedor**  
   El cliente llama directamente a la API de Assistants y toda la lógica de conversación queda repartida entre frontend y backend.

2. **Persistir el estado fuera de vuestro control**  
   Si el hilo conversacional está demasiado ligado al proveedor, moverlo luego cuesta mucho más.

3. **Meter lógica de negocio dentro del prompt**  
   Funciona al principio, pero después dificulta pruebas, versionado y auditoría.

4. **No tener pruebas de regresión**  
   La migración puede “parecer” correcta y romper matices importantes: tono, enrutado de herramientas, orden de llamadas o contexto.

5. **No medir costes y latencia**  
   Cambiar de plataforma sin comparar comportamiento real os puede dejar peor que antes.

### Qué cambia al pensar en Foundry Agent Service

La dirección recomendada por Microsoft es mover las soluciones hacia Foundry, cuyo portal GA está pensado para producción empresarial y para operar sistemas de IA con controles integrados ([fuente](https://learn.microsoft.com/en-us/azure/foundry/concepts/general-availability)). Eso no significa copiar y pegar Assistants a otro sitio: significa repensar el agente como un componente más explícito de la arquitectura.

En términos prácticos, solemos recomendar este enfoque:

- **separar dominio y orquestación**
- **dejar la conversación en un servicio intermedio**
- **tratar las herramientas como capacidades versionadas**
- **externalizar memoria y contexto relevante**
- **añadir observabilidad desde el primer día**

Es decir: menos magia implícita y más arquitectura trazable.

### Plan de migración en 6 pasos

#### 1. Congelad el alcance

Marcad qué flujos seguirán vivos durante la migración y cuáles se pueden retirar. No intentéis mover todo a la vez si hoy tenéis varios asistentes heterogéneos.

#### 2. Clasificad cada asistente

Agrupad por complejidad:

- chat simple
- asistente con herramientas
- asistente con estado largo
- asistente con integraciones de negocio
- asistente regulado o con datos sensibles

#### 3. Definid el contrato interno

Antes de integrar Foundry, cread una interfaz propia para vuestro dominio. Por ejemplo, un servicio `IAssistantService` o `IAgentOrchestrator` que oculte el proveedor.

#### 4. Implementad un adaptador nuevo

El objetivo no es migrar la UI, sino cambiar la implementación por debajo.

#### 5. Comparad resultados

Medid respuestas, tiempos y uso de herramientas entre el sistema antiguo y el nuevo. Si podéis, ejecutad ambos en paralelo un tiempo limitado.

#### 6. Retirad Assistants por fases

Apagad primero entornos de prueba, luego flujos secundarios y por último los críticos.

### Ejemplo práctico en .NET: abstraer el proveedor

Este patrón os permite desacoplar el dominio del proveedor de IA. La interfaz queda estable aunque cambie la plataforma detrás.

```csharp
public sealed record ChatRequest(string ConversationId, string UserMessage);
public sealed record ChatResponse(string Reply, IReadOnlyList<string> ToolCalls);

public interface IAssistantService
{
    Task<ChatResponse> SendAsync(ChatRequest request, CancellationToken cancellationToken);
}

public sealed class AssistantController
{
    private readonly IAssistantService _assistantService;

    public AssistantController(IAssistantService assistantService)
    {
        _assistantService = assistantService;
    }

    public Task<ChatResponse> PostAsync(ChatRequest request, CancellationToken cancellationToken)
        => _assistantService.SendAsync(request, cancellationToken);
}
```

Con esto, la migración consiste en cambiar la implementación de `IAssistantService`, no toda la aplicación.

### Ejemplo práctico: envolver la llamada al agente

No vamos a inventar un SDK de Foundry que no tengamos delante, así que lo prudente es mostrar el patrón de adaptación HTTP que podéis usar con cualquier backend nuevo:

```csharp
using System.Net.Http.Json;

public sealed class FoundryAgentService : IAssistantService
{
    private readonly HttpClient _httpClient;

    public FoundryAgentService(HttpClient httpClient)
    {
        _httpClient = httpClient;
    }

    public async Task<ChatResponse> SendAsync(ChatRequest request, CancellationToken cancellationToken)
    {
        var response = await _httpClient.PostAsJsonAsync("/api/agent/chat", request, cancellationToken);
        response.EnsureSuccessStatusCode();

        var payload = await response.Content.ReadFromJsonAsync<ChatResponse>(cancellationToken: cancellationToken);
        return payload ?? new ChatResponse(string.Empty, Array.Empty<string>());
    }
}
```

La ventaja de este enfoque es clara: si mañana cambia el endpoint o el proveedor, el impacto queda encapsulado.

### Checklist de impacto antes del 26 de agosto de 2026

Usad esta lista como control de salida:

- [ ] tenemos inventario completo de asistentes y dependencias
- [ ] sabemos qué flujos son críticos para negocio
- [ ] hemos aislado la lógica de acceso a IA tras una interfaz
- [ ] tenemos pruebas de regresión con conversaciones reales anonimizadas
- [ ] hemos medido latencia y coste del flujo actual
- [ ] hemos diseñado el almacenamiento de contexto y memoria
- [ ] hemos revisado secretos, identidades y permisos
- [ ] tenemos plan de rollback
- [ ] hemos definido fechas de apagado por fases
- [ ] hemos comunicado el cambio a producto, soporte y seguridad

### Qué métricas deberíais comparar durante el piloto

No basta con que “responda parecido”. Comparad, al menos:

- tiempo medio de respuesta
- tasa de error
- número de llamadas a herramientas por conversación
- tasa de respuesta útil en casos reales
- tasa de intervención humana
- incidencia de alucinaciones o respuestas fuera de política

Si estas métricas empeoran, la migración todavía no está lista.

### Un consejo práctico: migrad por capacidades, no por pantallas

Es tentador empezar por la interfaz de chat porque es lo que se ve. Pero la forma más segura suele ser la contraria: primero movemos capacidades de fondo —orquestación, herramientas, memoria, observabilidad— y luego la experiencia de usuario.

Eso os permite validar el comportamiento del agente antes de comprometer toda la experiencia final.

### En resumen

La retirada de Azure OpenAI Assistants no es una anécdota de roadmap: es una llamada a revisar cómo estáis construyendo agentes hoy. Si todavía dependéis de Assistants API, lo sensato es empezar ya con un inventario, un contrato interno y un adaptador hacia Foundry Agent Service.

Microsoft está empujando Foundry como plataforma GA para escenarios empresariales, con gobierno y controles integrados ([fuente](https://learn.microsoft.com/en-us/azure/foundry/concepts/general-availability)), y la transición debe entenderse como una oportunidad para profesionalizar vuestra base técnica, no como una simple sustitución de endpoint.

Si queréis reducir riesgo, empezad por lo que más impacto tiene: aislamiento de proveedor, pruebas de regresión y despliegue gradual. El 26 de agosto de 2026 no debería pillaros improvisando.
