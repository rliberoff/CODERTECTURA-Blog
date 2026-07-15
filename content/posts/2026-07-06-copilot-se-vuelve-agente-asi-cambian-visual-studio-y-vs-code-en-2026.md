---
title: 'Copilot se vuelve agente: así cambian Visual Studio y VS Code en 2026'
date: '2026-07-06T10:26:15+00:00'
draft: true
slug: copilot-se-vuelve-agente-asi-cambian-visual-studio-y-vs-code-en-2026
description: Repaso las novedades más importantes de GitHub Copilot en Visual Studio
  y VS Code en 2026 y qué significan para tu forma real de desarrollar.
categories:
- Inteligencia Artificial
- .NET
- Arquitectura de Software
tags:
- GitHub Copilot
- Visual Studio Code
- Visual Studio
- Inteligencia Artificial
- Productividad
- Developer Experience
image: /images/copilot-se-vuelve-agente-asi-cambian-visual-studio-y-vs-code-en-2026/cover.png
comments: true
ai:
  assisted: true
  model: gpt-5.4
  prompt_version: 2026-06-30.5
  generated_at: '2026-07-06T10:26:15+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://github.blog/changelog/2026-04-08-github-copilot-in-visual-studio-code-march-releases
    title: GitHub Copilot in Visual Studio Code, March Releases - GitHub Changelog
    published_date: '2026-07-02'
  - url: https://github.blog/changelog/2026-04-30-github-copilot-in-visual-studio-april-update
    title: GitHub Copilot in Visual Studio — April update - GitHub Changelog
    published_date: '2026-07-02'
  - url: https://github.blog/changelog/2026-07-01-kimi-k2-7-is-now-available-in-github-copilot
    title: Kimi K2.7 Code is generally available in GitHub Copilot
    published_date: '2026-07-01'
  - url: https://github.blog/changelog/2026-06-17-github-copilot-app-generally-available
    title: GitHub Copilot app generally available - GitHub Changelog
    published_date: '2026-06-17'
  - url: https://github.blog/changelog/2026-07-02-upcoming-deprecation-of-gemini-2-5-pro-and-gemini-3-flash
    title: Upcoming deprecation of Gemini 2.5 Pro and Gemini 3 Flash
    published_date: '2026-07-02'
---

Si me preguntas qué está cambiando de verdad con GitHub Copilot en 2026, yo **no** te respondería «*ahora sugiere mejor código*». Eso, a estas alturas, se me queda cortísimo.

Lo que veo es algo bastante más profundo: Copilot deja de ser solo un asistente de autocompletado y empieza a comportarse como un agente con contexto, permisos, herramientas, navegación, capacidad de depurar y, en algunos escenarios, bastante autonomía (siempre y cuando se lo permitas y aceptes los potenciales riesgos). Y eso sí cambia la forma en la que yo desarrollo en Visual Studio y en VS Code.

Las novedades recientes apuntan justo en esa dirección. En VS Code han llegado sesiones de agente con niveles de permiso, modo **Autopilot**, depuración integrada en navegador, soporte multimodal con imágenes y vídeo, subagentes anidados (que si usas [Squads](https://github.com/bradygaster/squad) es una pasada) y un editor unificado para personalizar chat, agentes, *skills* y *plugins*, según el *changelog* de marzo y abril de 2026 de GitHub Copilot para VS Code ([github.blog](https://github.blog/changelog/2026-04-08-github-copilot-in-visual-studio-code-march-releases)). En Visual Studio, vemos el mismo patrón: sesiones de agente en la nube desde el propio IDE, agentes personalizados a nivel de usuario, *skills* en varias rutas y un nuevo *debugger agent* orientado a reproducir, instrumentar y validar errores contra el comportamiento real en ejecución ([github.blog](https://github.blog/changelog/2026-04-30-github-copilot-in-visual-studio-april-update)).

### El cambio importante no es la UI: es el modelo mental y el flujo de trabajo

Hasta hace poco, mi flujo con Copilot era bastante lineal: escribo código, pido una explicación, acepto o rechazo sugerencias y, como mucho, lanzo una conversación puntual. Ahora el modelo mental y la forma de trabajar cambia.

Yo empiezo a ver tres niveles bastante claros:

- **Asistente**: propone, explica y completa.
- **Operador**: toca ficheros, ejecuta pasos, inspecciona artefactos y sigue un plan.
- **Agente**: decide la secuencia de acciones, se recupera de errores, usa herramientas y avanza con menos intervención.

Eso encaja muy bien con los nuevos niveles de permisos en VS Code: **Default**, **Bypass Approvals** y **Autopilot** ([github.blog](https://github.blog/changelog/2026-04-08-github-copilot-in-visual-studio-code-march-releases)). Y no, no me parece un detalle cosmético. Me parece una declaración bastante seria sobre cómo vamos a interactuar con estas herramientas a partir de ahora: ya no gestionas solo respuestas, gestionas grados de delegación. Al fin y al cabo ese es el objetivo: poder delegar con confianza y rigurosidad a entidades de Inteligencia Artificial la realización de tareas tanto rutinarios como complejas.

{{< figure src="/images/copilot-se-vuelve-agente-asi-cambian-visual-studio-y-vs-code-en-2026/body-1.png" alt="Diagrama del paso de asistente a agente en Copilot" caption="El cambio de 2026 no es solo funcional: Copilot pasa de sugerir a ejecutar flujos con distintos grados de autonomía." >}}{{< /figure >}}

En mi experiencia, esto obliga a pensar bastante mejor qué tareas delego y cuáles no, y sobre todo a explicarlas con detalle y especificidad. No todo merece «Autopilot», sobre todo porque el consumo de créditos de IA (y los costes subyacentes) se pueden disparar. Refactorizar una batería de tests repetitivos o seguir una secuencia bien conocida puede encajar perfectamente. Tocar una migración delicada, un cambio de seguridad o una pieza de dominio especialmente sensible… ahí yo seguiría queriendo las manos en el volante.

### VS Code: de chat con herramientas a sesiones realmente *agentic*

Lo más llamativo de VS Code es que las piezas ya empiezan a encajar entre sí.

Por un lado, **Autopilot** permite que el agente apruebe sus propias acciones, reintente cuando falla y siga trabajando hasta completar la tarea, sin requerir aprobaciones manuales en cada paso ([github.blog](https://github.blog/changelog/2026-04-08-github-copilot-in-visual-studio-code-march-releases)). Para mí aquí hay una frontera muy clara: cuando un flujo deja de estar dominado por el *prompt* y pasa a estar dominado por la ejecución.

Por otro lado, GitHub ha añadido **subagentes anidados**, activables con `chat.subagents.allowInvocationsFromSubagents`, para permitir descomposición en tareas más complejas ([github.blog](https://github.blog/changelog/2026-04-08-github-copilot-in-visual-studio-code-march-releases)). Esto me parece importante por una razón muy poco glamurosa y muy real: muchas tareas de verdad no son «haz X», sino «investiga, reproduce, corrige, valida y documenta». Si el agente puede dividir ese trabajo, el valor sube mucho.

Y hay una tercera pieza que, sinceramente, me parece todavía más interesante: **depuración integrada en navegador**. VS Code incorpora el tipo de depuración `editor-browser`, compatible con muchas configuraciones ya existentes de `chrome` y `msedge`, para poner breakpoints, avanzar paso a paso e inspeccionar variables sin salir del editor ([github.blog](https://github.blog/changelog/2026-04-08-github-copilot-in-visual-studio-code-march-releases)).

Esto no solo mejora la productividad. Le da al agente acceso a un ciclo de observación mucho más cercano al *runtime* real. Y eso, cuando estás depurando frontend, Blazor, una SPA o cualquier aplicación con una parte importante en navegador, cambia bastante el juego. La diferencia entre «creo que aquí falla el estado» y «he visto la variable en tiempo de ejecución» es enorme.

Un ejemplo mínimo y concreto de `launch.json` sería este:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Depurar en navegador integrado",
      "type": "editor-browser", // Esta es la clave: activa la depuración web dentro del editor
      "request": "launch",
      "url": "http://localhost:5173",
      "webRoot": "${workspaceFolder}"
    }
  ]
}
```

No tiene mucha épica, la verdad, pero precisamente por eso me gusta: la línea importante es `"type": "editor-browser"`. Ahí está el cambio que acerca la depuración web al flujo agéntico dentro de VS Code.

{{< figure src="/images/copilot-se-vuelve-agente-asi-cambian-visual-studio-y-vs-code-en-2026/body-2.png" alt="Diagrama del flujo de depuración con navegador integrado en VS Code" caption="La depuración en navegador dentro de VS Code acerca al agente al comportamiento real de la aplicación." >}}{{< /figure >}}

### Visual Studio: el salto serio es llevar el agente al ciclo de resolución de incidencias

En Visual Studio, lo que más me llama la atención no es solo que haya agentes, sino **dónde** se integran. Las más recientes actualizaciones introducen **cloud agent sessions** iniciadas directamente desde el IDE. Según GitHub, eliges **Cloud** en el selector del agente, describes la tarea y el agente crea una *issue* y una *pull request* en infraestructura remota mientras tú sigues trabajando ([github.blog](https://github.blog/changelog/2026-04-30-github-copilot-in-visual-studio-april-update)).

Eso cambia una suposición bastante clásica: hasta ahora, el trabajo del asistente ocurría principalmente en tu sesión local. Ahora parte del trabajo puede trasladarse a un contexto remoto y paralelo. Desde el punto de vista del flujo de equipo, esto se parece menos a «*preguntarle algo a una IA*» y más a «*asignar una tarea a un colaborador digital*». Sí, suena un poco grandilocuente. Pero la dirección es esa.

Además, Visual Studio añade dos piezas muy útiles para equipos y para desarrolladores con manías propias (jejeje… yo el primero):

- **Agentes personalizados a nivel de usuario**, almacenados en `%USERPROFILE%/.github/agents/`.
- **Skills** descubiertas también en `.claude/skills/` y `.agents/skills/`, además de `.github/skills/` ([github.blog](https://github.blog/changelog/2026-04-30-github-copilot-in-visual-studio-april-update)).

A mí esto me gusta porque resuelve un problema real: no siempre quiero que la personalización viva solo en el repositorio. Hay reglas y patrones que son míos como desarrollador, algo así como mi propia propiedad intelectual: cómo reviso código, cómo pido diagnósticos, cómo exijo evidencias antes de aceptar un *fix*. Poder llevarme esos agentes entre proyectos sin tener que compartirlo por un repositorio, a veces, me parece mucho más potente de lo que podría ser a primera vista.

Otra cosa particularmente interesante es el **Debugger agent**. GitHub lo describe como un flujo que parte de una *issue* de GitHub o Azure DevOps (sip… este también) y permite reproducir, instrumentar, diagnosticar y sugerir una corrección basada en ejecución real ([github.blog](https://github.blog/changelog/2026-04-30-github-copilot-in-visual-studio-april-update)). Eso conecta muy bien con una idea que yo repito bastante: los bugs importantes no se resuelven con texto bonito, sino con evidencia. Si el agente participa en un circuito donde observa el sistema vivo, la conversación deja de ser puramente lingüística y se vuelve operativa.

{{< figure src="/images/copilot-se-vuelve-agente-asi-cambian-visual-studio-y-vs-code-en-2026/body-3.png" alt="Diagrama del ciclo de resolución de incidencias con agente en Visual Studio" caption="En Visual Studio, el valor está en cerrar el ciclo desde la incidencia hasta la validación del fix con evidencia de ejecución." >}}{{< /figure >}}

### Multimodalidad: cuando una captura vale más que diez *prompts*

Otra novedad que no conviene subestimar es el soporte de **imágenes y vídeo en chat** dentro de VS Code. Ahora puedes adjuntar capturas o vídeos, y los agentes pueden devolver imágenes o grabaciones de los cambios para revisarlos en un carrusel ([github.blog](https://github.blog/changelog/2026-04-08-github-copilot-in-visual-studio-code-march-releases)).

Parece una mejora cómoda, pero en realidad cambia bastante el tipo de problemas que puedes delegar.

Por ejemplo:

- Un bug visual que solo aparece en cierto estado de la UI.
- Un flujo de usuario que falla tras varios clics.
- Una discrepancia entre diseño esperado y resultado real.
- Un problema de *responsive* que es un suplicio describir con texto.

Antes yo tenía que traducir una observación visual a un *prompt* suficientemente preciso y detallado. Ahora puedo enseñar el problema. Y en tareas de depuración y ajuste fino, eso recorta muchísimo la ambigüedad. Incluso puedo editar la imagen resaltando áreas en círculos o cuadros rojos, y pasárselo al agente indicando que en esas zonas podrá encontrar el defecto o discrepancia (tal y como haría con una persona humana).

### El selector de modelo ya no es un detalle secundario

También cambia el peso del **model picker**. GitHub ha anunciado la disponibilidad general de **Kimi K2.7 Code** (por sugerencia de Borja Piris de Castro, he probado el Kimi 2.6 Code y la verdad que va muy bien) en Copilot como primer modelo *open-weight* seleccionable, precisamente para dar más elección y una opción de menor coste para determinadas tareas ([github.blog](https://github.blog/changelog/2026-07-01-kimi-k2-7-is-now-available-in-github-copilot)). Y, al mismo tiempo, ha comunicado la retirada futura de Gemini 2.5 Pro y Gemini 3 Flash en favor de Gemini 3.1 Pro y Gemini 3.5 Flash ([github.blog](https://github.blog/changelog/2026-07-02-upcoming-deprecation-of-gemini-2-5-pro-and-gemini-3-flash)).

{{< figure src="/images/copilot-se-vuelve-agente-asi-cambian-visual-studio-y-vs-code-en-2026/source-4.png" alt="Selector de modelos de GitHub Copilot con Kimi K2.7 Code" caption="El selector de modelos gana importancia cuando Copilot actúa como agente y no solo como autocompletado. Fuente: [github.blog](https://github.blog/changelog/2026-07-01-kimi-k2-7-is-now-available-in-github-copilot)" >}}{{< /figure >}}

Yo saco una conclusión muy práctica: si Copilot actúa cada vez más como agente, **elegir modelo deja de ser una preferencia anecdótica**. Afecta al coste, a la profundidad de razonamiento y a la idoneidad para cada tarea. De hecho, VS Code desde hace un tiempo permite ajustar el **thinking effort** de modelos de razonamiento desde el propio selector, y mantener esa preferencia entre conversaciones ([github.blog](https://github.blog/changelog/2026-04-08-github-copilot-in-visual-studio-code-march-releases)).

Mi lectura aquí es sencilla: el flujo moderno ya no es «*un Copilot para todo*», sino «*una combinación de permisos, herramientas, nivel de razonamiento y modelo según la tarea*».

### De IDE a plataforma: el contexto más amplio también importa

Aunque el foco aquí sean Visual Studio y VS Code, hay una señal adicional que a mí me parece importante. La **GitHub App** ya está disponible de forma general como escritorio para desarrollo guiado por agentes, con sesiones paralelas por repositorio, revisión de *diffs*, validación en terminal y navegador, PRs, *canvases* y automatizaciones cloud ([github.blog](https://github.blog/changelog/2026-06-17-github-copilot-app-generally-available)).

No lo menciono para irme por las ramas, sino porque confirma la tendencia: GitHub está construyendo una capa *agentic* que atraviesa editor, IDE, app dedicada y nube; buscando ampliar y democratizar el acceso a este tipo de herramientas a la mayor ampitud de audiencias posibles. Visual Studio y VS Code no son islas; son puntos de entrada a un flujo de trabajo mayor enfocafos a los desarrolladores, pero la GitHub App puede servir a *citizen developers* y a nóveles entusiastas de la IA.

### Entonces, ¿cómo cambia mi forma de desarrollar?

Yo lo resumiría así:

- **Delego más trabajo mecánico**, pero con límites de permiso claros.
- **Pido evidencia de *runtime*** antes de dar por buena una corrección.
- **Uso multimodalidad** con imágenes (o videos) cuando el problema es visual o conductual.
- **Ajusto modelo y esfuerzo de razonamiento** según la tarea.
- **Pienso en sesiones**, no solo en *prompts* sueltos.
- Me apoyo en herramientas de agentificación, tales como Squads, GitHub Spec Kit o AI-DLC.

Y, sobre todo, cambio una expectativa clave: ya no espero que Copilot «*acierte a la primera*», sino que **avance con criterio, deje rastro, use herramientas y sepa validarse**.

Ese es, para mí, el verdadero salto de 2026. No estamos solo ante un Copilot más listo. Estamos ante una transición hacia un compañero de trabajo más autónomo, más observable y más integrado en el ciclo real de desarrollo.

¿Mi opinión? Tiene muchísimo potencial, pero exige disciplina… mucha disciplina. Cuanta más autonomía le das a un agente, más importante se vuelve diseñar bien el entorno: permisos, *skills*, modelos, validación y puntos de control. Si eso se hace bien, el beneficio **no** es únicamente escribir más rápido: el beneficio de verdad es **cerrar antes el bucle entre intención, ejecución y verificación**.

Y ahí sí, ahora sí, estamos hablando de un cambio serio.
