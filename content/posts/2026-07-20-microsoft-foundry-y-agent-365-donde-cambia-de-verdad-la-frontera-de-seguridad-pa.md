---
title: 'Microsoft Foundry y Agent 365: dónde cambia de verdad la frontera de seguridad
  para agentes'
date: '2026-07-20T16:17:05+00:00'
draft: true
slug: microsoft-foundry-y-agent-365-donde-cambia-de-verdad-la-frontera-de-seguridad-pa
description: La seguridad de los agentes en Microsoft Foundry ya no depende sólo del
  runtime. Te explico por qué el cambio a Agent 365 afecta a arquitectura, gobierno
  y licencias.
categories:
- Inteligencia Artificial
- Arquitectura de Software
- Azure
tags:
- Microsoft Foundry
- Microsoft Agent 365
- Seguridad
- Gobierno de IA
- Arquitectura
- Microsoft Defender
image: /images/microsoft-foundry-y-agent-365-donde-cambia-de-verdad-la-frontera-de-seguridad-pa/cover.png
comments: true
ai:
  assisted: true
  model: gpt-5.4
  prompt_version: 2026-07-20.1
  generated_at: '2026-07-20T16:17:05+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://www.microsoft.com/en-us/microsoft-cloud/blog/2026/06/29/the-2026-agent-confidence-index-where-300-builders-see-real-momentum
    title: 'The 2026 Agent Confidence Index: Where 300 builders ...'
    published_date: '2026-06-29'
  - url: https://adoption.microsoft.com/en-us/copilot-chat
    title: Microsoft 365 Copilot Chat – Microsoft Adoption
    published_date: null
  - url: https://techcommunity.microsoft.com/blog/azurearchitectureblog/from-policy-to-proof-governing-ai-to-scale-human-ambition-and-machine-intelligen/4535137
    title: 'From Policy to Proof: Governing AI to Scale Human ...'
    published_date: null
  - url: https://learn.microsoft.com/en-us/defender-xdr/security-for-ai/transition-agent-security-to-agent-365
    title: Transition Microsoft Copilot Studio and Microsoft Foundry ...
    published_date: null
---

Si estás diseñando una plataforma de agentes con Microsoft Foundry, yo creo que ya no basta con pensar en modelos, herramientas y runtime. El cambio importante está en otro sitio: **la frontera real de seguridad y gobierno se está moviendo al plano de control**. Y, según la documentación sobre la [transición de las capacidades de seguridad a Microsoft Agent 365](https://learn.microsoft.com/en-us/defender-xdr/security-for-ai/transition-agent-security-to-agent-365), esto deja de ser un matiz comercial para convertirse en una decisión arquitectónica con fecha efectiva.

Hasta hace poco, mucha gente interpretaba la seguridad de agentes como una extensión natural de Defender for Cloud, Defender for Cloud Apps o, en general, del stack donde ejecutabas el agente. Pero desde el 1 de julio de 2026, las capacidades de seguridad para agentes de Microsoft Foundry y Microsoft Copilot Studio pasan a requerir una licencia de [Microsoft Agent 365](https://learn.microsoft.com/en-us/defender-xdr/security-for-ai/transition-agent-security-to-agent-365). Y eso cambia quién ve, quién gobierna, quién investiga y, sobre todo, **qué inventario cuenta como fuente de verdad**.

### El cambio no es sólo de licencia: es de modelo operativo

Lo primero que te diría es que no leas esta noticia como un simple “nuevo SKU”. A mí me parece un error bastante serio. Cuando Microsoft explica que, tras el onboarding a Agent 365, la experiencia sigue en el portal de Microsoft Defender pero pasa a estar alimentada por los logs de observabilidad de Agent 365 y por el registro de agentes como fuente única de inventario, lo que está describiendo no es sólo facturación: está describiendo un cambio de *control plane*.

Eso significa que la pregunta de arquitectura deja de ser “¿dónde se ejecuta mi agente?” y pasa a ser “**¿desde qué plano se descubre, se observa y se protege?**”. Y esa diferencia, aunque suene sutil, no lo es en absoluto. Afecta a los límites entre equipos, a la asignación de responsabilidades y a la forma en la que seguridad, plataforma, cumplimiento y desarrollo comparten contexto.

En otras palabras: ya no hablamos sólo del sitio donde corre el agente, sino del sistema desde el que puedes demostrar que ese agente existe, qué hace y bajo qué controles opera. Y cuando esa capa cambia, cambia también la arquitectura de referencia.

{{< figure src="/images/microsoft-foundry-y-agent-365-donde-cambia-de-verdad-la-frontera-de-seguridad-pa/body-1.png" alt="Diagrama del cambio de plano de control entre Foundry y Agent 365" caption="El cambio relevante no está en el runtime del agente, sino en el plano que concentra inventario, observabilidad y protección." >}}{{< /figure >}}

Si te fijas en el detalle de la documentación, en el caso de Microsoft Foundry había dos bloques que antes se cubrían desde Defender for Cloud: por un lado, la postura de seguridad y el descubrimiento de agentes cloud-hosted, incluido el entorno multicloud dentro del plan de Defender CSPM; por otro, la protección frente a amenazas para agentes, antes asociada a Defender for AI Services. Con el cambio, Defender CSPM puede seguir descubriendo cuentas y proyectos de Foundry, pero el descubrimiento a nivel de agente, su postura y su detección de amenazas requieren Agent 365. Esa frase, por sí sola, ya cambia bastante el tablero.

### Qué pierde exactamente una organización si no hace la transición

Aquí conviene bajar a tierra, porque si no todo esto suena demasiado abstracto. Según la página de [transición a Microsoft Agent 365](https://learn.microsoft.com/en-us/defender-xdr/security-for-ai/transition-agent-security-to-agent-365), los tenants sin una licencia elegible pierden acceso a estas capacidades:

- Descubrimiento de agentes.
- Evaluación de postura de seguridad de agentes.
- Protección frente a amenazas y protección en tiempo real.
- Investigación de actividad de agentes en Advanced Hunting, ahora alimentada por logs de observabilidad de Agent 365.

Dicho sin adornos: puedes seguir teniendo agentes desplegados, incluso cuentas y proyectos visibles desde otras capas, pero **pierdes la vista operativa que convierte un agente en un activo gobernable**. Y para mí ahí está la clave. Un agente que funciona pero no entra en el inventario correcto, no expone una postura consistente y no puede investigarse de forma fiable no está realmente en producción con garantías. Está “encendido”, sí. Gobernado, no necesariamente.

Yo lo comparo mucho con tener contenedores ejecutándose sin telemetría, sin identidad coherente y sin trazabilidad operativa. Técnicamente existen. Operacionalmente, están medio fuera del sistema. Y todos sabemos cómo terminan esas historias cuando llega una incidencia, una auditoría o una investigación forense a las 3 de la mañana.

### El registro de agentes pasa a ser una pieza central

La documentación también deja claro que el registro de agentes actúa como *single source of truth* para inventario. Y esa idea encaja muy bien con algo que Microsoft lleva tiempo empujando en gobierno de IA: pasar de políticas estáticas a un sistema operativo de controles, telemetría y prueba continua. El artículo de Azure Architecture Blog sobre [gobernar IA y agentes como un bucle de política, observabilidad, enforcement y evidencia](https://techcommunity.microsoft.com/blog/azurearchitectureblog/from-policy-to-proof-governing-ai-to-scale-human-ambition-and-machine-intelligen/4535137) va exactamente por ahí.

Mi lectura arquitectónica es bastante directa: si tu catálogo interno de agentes, tus procesos de aprobación y tu modelo de *ownership* no se alinean con ese registro operativo, vas a terminar con dos realidades. Una en tu CMDB, en tu wiki o en tu backlog. Otra en el plano que realmente aplica seguridad, hunting y postura. **Y cuando hay dos inventarios, el auditor, el SOC y el equipo de plataforma nunca están mirando lo mismo**.

{{< figure src="/images/microsoft-foundry-y-agent-365-donde-cambia-de-verdad-la-frontera-de-seguridad-pa/body-2.png" alt="Bucle de gobierno para agentes de IA" caption="Gobernar agentes ya no consiste sólo en definir políticas: hace falta cerrar el bucle entre control, observabilidad y evidencia." >}}{{< /figure >}}

Por eso yo revisaría ya, como mínimo, estas tres cuestiones:

1. Quién es el *owner* de cada agente y dónde queda registrado de forma operativa.
2. Qué agentes cuentan como “corporativos”, aunque hayan nacido en equipos de negocio o en iniciativas departamentales.
3. Cómo conectas el ciclo de despliegue con el ciclo de gobierno, para que no sean dos procesos paralelos que nunca se tocan.

Si no haces ese trabajo, el cambio a Agent 365 no te arregla nada. Lo único que hace es dejar más visible que el problema ya existía.

### Foundry ya no se puede evaluar sólo desde la infraestructura

Este punto me parece especialmente importante si trabajas en arquitectura cloud. Durante años hemos aprendido a modelar la seguridad desde capas bastante conocidas: red, identidad, secretos, compute, datos, postura cloud. Todo eso sigue importando, por supuesto. No desaparece mágicamente porque ahora hablemos de agentes. Pero con este movimiento Microsoft está separando con más nitidez la seguridad de la infraestructura de la seguridad del comportamiento operativo del agente.

Eso se ve en una distinción muy concreta: [Defender CSPM sigue descubriendo cuentas y proyectos de Foundry](https://learn.microsoft.com/en-us/defender-xdr/security-for-ai/transition-agent-security-to-agent-365), pero no sustituye el descubrimiento y la protección a nivel de agente. Es decir, saber que existe un proyecto Foundry no equivale a gobernar los agentes que viven dentro, las acciones que ejecutan ni los eventos que generan. Parece obvio cuando lo lees así. En la práctica, no siempre se modela como tal.

En términos de arquitectura empresarial, esto obliga a tratar los agentes como una clase de activo propia. No son sólo recursos cloud. Tampoco son simplemente aplicaciones con otro nombre. Son entidades con identidad, observabilidad, acciones y riesgo delegado. Y cuando una entidad puede actuar en nombre de un proceso o de una persona, el marco de control también tiene que cambiar.

### Esto también afecta a la conversación de licencias

Ya sé que hablar de licencias no tiene precisamente glamour. Pero aquí tiene consecuencias muy reales. Cuando una capacidad de seguridad se desacopla del producto de ejecución y se recentra en un plano transversal como Agent 365, el presupuesto deja de ser una derivada automática del proyecto técnico y pasa a formar parte del modelo operativo de la organización.

Dicho de otra manera: el equipo que paga Foundry no tiene por qué ser el mismo que debe financiar la seguridad efectiva del estate de agentes. Y si compras la plataforma de construcción sin resolver esa asignación, acabas con una arquitectura aprobada sobre el papel pero una operación incompleta. No es un problema de procurement. Es un problema de diseño organizativo.

La propia documentación de Microsoft Adoption sobre el [ecosistema de agentes en Microsoft 365](https://adoption.microsoft.com/en-us/copilot-chat) ya deja ver esa separación conceptual entre Microsoft Foundry, Microsoft Agent 365, Copilot Studio y los agentes en Microsoft 365. Yo lo interpreto como una pista bastante clara del posicionamiento: Foundry sirve para construir y operar experiencias; Agent 365 concentra capacidades transversales de gobierno, seguridad y observabilidad dentro del universo de agentes.

### Qué haría yo como arquitecto a partir de ahora

Si me preguntas por una hoja de ruta sensata, yo empezaría por algo menos glamuroso de lo que suena en las keynotes: inventario y criterios. Sí, ya sé. Menos épico, más útil.

Primero, inventariaría todos los agentes actuales y previstos en tres grupos: agentes de Copilot Studio, agentes de Foundry y agentes “híbridos” que consumen datos o acciones en Microsoft 365. No por hacer una taxonomía bonita para una diapositiva, sino porque el impacto en control-plane y licenciamiento no es exactamente igual en todos los casos.

Segundo, revisaría qué casos de uso dependen realmente de detección de amenazas, postura o investigación forense. La [encuesta resumida en el Agent Confidence Index 2026](https://www.microsoft.com/en-us/microsoft-cloud/blog/2026/06/29/the-2026-agent-confidence-index-where-300-builders-see-real-momentum) subraya algo que me parece de puro sentido común: la confianza en agentes crece cuando hay humanos en el bucle y más observabilidad. Y eso encaja perfectamente con este movimiento de Microsoft. Puedes escalar agentes, sí, pero sólo cuando la observabilidad deja de ser opcional.

{{< figure src="/images/microsoft-foundry-y-agent-365-donde-cambia-de-verdad-la-frontera-de-seguridad-pa/body-3.png" alt="Mapa de decisión arquitectónica para llevar agentes a producción" caption="Una forma práctica de decidir si un agente está listo para producción es tratar seguridad y gobierno como requisitos de entrada, no como mejoras posteriores." >}}{{< /figure >}}

Tercero, conectaría el alta de un agente con un control explícito de elegibilidad. Sin *owner*, sin clasificación de datos, sin patrón de observabilidad y sin cobertura de Agent 365 cuando aplique, el agente no pasa a producción. Así de simple. No porque yo quiera burocracia por deporte, sino porque prefiero una fricción pequeña al principio antes que una investigación grande al final.

Cuarto, actualizaría la documentación de referencia de arquitectura. Si en tus diagramas todavía representas la seguridad de agentes como una capacidad “colgando” de Defender for Cloud o Defender for Cloud Apps, te has quedado corto. Ahora necesitas reflejar el plano de gobierno de agentes como una capa específica, con su inventario, su telemetría y su dependencia operativa.

### Un ejemplo mínimo de decisión operativa que sí merece automatizarse

No creo que este sea un tema para llenarlo de código por rellenar (de hecho, sería una mala idea). Pero sí veo útil una automatización muy concreta: marcar en tu pipeline o en tu checklist de *release* si un agente requiere controles de Agent 365 antes de promocionarlo.

Por ejemplo, un archivo de metadatos como éste puede servir como contrato entre plataforma, seguridad y desarrollo:

```yaml
agentId: sales-forecast-reviewer
platform: microsoft-foundry
owner: equipo-analitica-comercial
businessCriticality: high
handlesSensitiveData: true
usesActions: true
observabilityProfile: agent365-required
securityReviewStatus: approved
requiresAgent365Security: true # evita promocionar un agente sin el plano de control que necesita
environment: prod
```

No hay magia, claro. Pero me gusta porque fuerza una conversación útil y verificable: este agente no sólo necesita infraestructura y modelo; necesita entrar en el perímetro operativo correcto. Y eso, a estas alturas, ya no debería quedar implícito.

### Mi lectura final: la arquitectura de agentes madura cuando la seguridad deja de ser implícita

Para mí, éste es el mensaje de fondo. Microsoft no está diciendo simplemente “paga otra licencia”. Está diciendo que la seguridad de agentes necesita un plano especializado, con inventario, telemetría, hunting y postura consistentes. Y, honestamente, me parece coherente con una fase más madura del mercado.

Cuando los agentes eran experimentos, muchas organizaciones toleraban controles parciales, inventarios difusos y observabilidad a medio hacer. Cuando esos agentes empiezan a ejecutar acciones, tocar datos sensibles y operar a escala, **la gobernanza deja de ser una capa documental y se convierte en una dependencia de arquitectura**.

Si estás trabajando con Microsoft Foundry, yo no trataría Agent 365 como un detalle de procurement. Lo trataría como parte del diseño base de la plataforma. Porque, al final, la frontera que importa no es dónde corre el agente, sino dónde puedes demostrar que está bajo control.
