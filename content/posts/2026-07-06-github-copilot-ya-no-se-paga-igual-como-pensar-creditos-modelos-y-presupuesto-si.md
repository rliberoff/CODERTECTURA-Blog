---
title: 'GitHub Copilot ya no se paga igual: cómo pensar créditos, modelos y presupuesto sin perder el control'
date: '2026-07-06T10:32:04+00:00'
draft: false
slug: github-copilot-ya-no-se-paga-igual-como-pensar-creditos-modelos-y-presupuesto-si
description: GitHub Copilot pasa a facturación por uso y eso cambia cómo elegir modelos, controlar créditos y gobernar planes. Te cuento qué miraría yo si lideras plataforma o arquitectura.
categories:
- Inteligencia Artificial
- Arquitectura de Software
- Azure
tags:
- GitHub Copilot
- FinOps
- Modelos de IA
- Gobierno de plataforma
- Billing
- Productividad
image: /images/github-copilot-ya-no-se-paga-igual-como-pensar-creditos-modelos-y-presupuesto-si/cover.png
comments: true
ai:
  assisted: true
  model: gpt-5.4
  prompt_version: 2026-06-30.5
  generated_at: '2026-07-06T10:32:04+00:00'
  reviewed_by: rliberoff
  review_status: approved
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://github.blog/changelog/2026-07-01-github-models-is-being-fully-retired-on-july-30-2026
    title: GitHub Models is being fully retired on July 30, 2026
    published_date: '2026-06-16'
  - url: https://github.blog/changelog/2026-06-17-copilot-individual-plan-sign-ups-are-reopening
    title: Copilot individual plan sign-ups are reopening - GitHub Changelog
    published_date: '2026-07-02'
  - url: https://github.blog/changelog/2026-07-02-upcoming-deprecation-of-gemini-2-5-pro-and-gemini-3-flash
    title: Upcoming deprecation of Gemini 2.5 Pro and Gemini 3 Flash
    published_date: '2026-07-02'
  - url: https://github.blog/changelog/2026-06-18-upcoming-deprecation-of-opus-4-6-fast
    title: Upcoming deprecation of Opus 4.6 (fast) - GitHub Changelog
    published_date: '2026-07-02'
  - url: https://github.blog/news-insights/company-news/github-copilot-is-moving-to-usage-based-billing
    title: GitHub Copilot is moving to usage-based billing
    published_date: null
  reviewed_at: '2026-07-14T06:42:57Z'
---

Si estás liderando arquitectura, plataforma o ingeniería, creo que estamos ante uno de esos cambios que, a primera vista, parecen puramente comerciales… pero no lo son en absoluto. En realidad, son profundamente técnicos. GitHub Copilot ya no se entiende bien si lo miras solo como una licencia por usuario.

Con el paso a facturación basada en uso, la elección del modelo, el tipo de interacción y la política de planes dejan de ser detalles operativos. Pasan a ser decisiones de diseño. Y sí, esto cambia bastante la conversación.

La señal más clara está en el anuncio de GitHub sobre el cambio a **usage-based billing** a partir del 1 de junio de 2026: los planes pasan a consumir **GitHub AI Credits** en función del uso real de tokens de entrada, salida y caché, según las tarifas publicadas por modelo, mientras que el precio base del plan no cambia y las autocompletaciones y *Next Edit Suggestions* siguen incluidas en todos los planes [(fuente)](https://github.blog/news-insights/company-news/github-copilot-is-moving-to-usage-based-billing). Yo, al menos, ya no lo plantearía como «¿tenemos Copilot?», sino como «¿para qué trabajo, con qué modelo y con qué *guardrails*?».

### Qué cambia de verdad con la facturación por uso

Hasta ahora, mucha gente razonaba Copilot como un coste bastante predecible por asiento. Eso facilitaba adoptar la herramienta rápido, pero también escondía una realidad incómoda: no cuesta lo mismo una consulta corta que una sesión agente larga, iterativa y lanzada sobre un repositorio grande.

GitHub lo explica precisamente así al justificar el cambio: Copilot ha evolucionado hacia un producto más *agentic*, con sesiones multietapa y una demanda de inferencia mayor [(fuente)](https://github.blog/news-insights/company-news/github-copilot-is-moving-to-usage-based-billing).

Para mí, de aquí salen tres implicaciones muy prácticas:

1. **El consumo ya no depende solo de cuántos usuarios tienes**, sino de cómo usan Copilot.
2. **El modelo importa más**, porque no todos consumen igual.
3. **La experiencia del desarrollador y el presupuesto quedan conectados**.

{{< figure src="/images/github-copilot-ya-no-se-paga-igual-como-pensar-creditos-modelos-y-presupuesto-si/body-1.png" alt="Diagrama del flujo de consumo de créditos de GitHub Copilot" caption="Cómo paso yo de una interacción en Copilot a una conversación de coste, política y observabilidad." >}}{{< /figure >}}

Dicho de forma más directa: si activas modelos muy potentes para todo el mundo, sin distinguir tareas ni contextos, puedes comprar comodidad a corto plazo… y llevarte una sorpresa bastante fea al cierre del mes.

### El selector de modelo ya es una política, no una preferencia personal

Uno de los síntomas más visibles de este cambio es que GitHub Copilot ya expone una oferta de modelos mucho más dinámica. Y no hablo solo de variedad: hablo también de rotación.

En julio de 2026 GitHub anunció la deprecación de **Gemini 2.5 Pro** y **Gemini 3 Flash**, con alternativas sugeridas **Gemini 3.1 Pro** y **Gemini 3.5 Flash** respectivamente [(fuente)](https://github.blog/changelog/2026-07-02-upcoming-deprecation-of-gemini-2-5-pro-and-gemini-3-flash). Poco antes también anunció la retirada de **Opus 4.6 (fast)** en favor de **Opus 4.8 (fast)** [(fuente)](https://github.blog/changelog/2026-06-18-upcoming-deprecation-of-opus-4-6-fast).

A mí esto me invalida una idea bastante extendida: «elegimos un modelo estándar y nos olvidamos». Pues no. No funciona así. La cartera de modelos está viva. Cambia por coste, disponibilidad, rendimiento o, sencillamente, por estrategia del proveedor.

Y aquí hay un detalle importante para quien administre una empresa: además necesitas habilitar los modelos alternativos mediante políticas para que aparezcan en el selector de Copilot, tal y como indican esos anuncios [(fuente)](https://github.blog/changelog/2026-07-02-upcoming-deprecation-of-gemini-2-5-pro-and-gemini-3-flash).

{{< figure src="/images/github-copilot-ya-no-se-paga-igual-como-pensar-creditos-modelos-y-presupuesto-si/source-2.jpg" alt="Selector de modelos en GitHub Copilot" caption="La elección de modelo ya no es un detalle visual: afecta a políticas, continuidad y coste operativo. Fuente: [github.blog](https://github.blog/changelog/2026-07-02-upcoming-deprecation-of-gemini-2-5-pro-and-gemini-3-flash)" >}}{{< /figure >}}

Mi lectura es bastante clara: el selector de modelo no debería tratarse ni como barra libre para cada desarrollador ni como un bloqueo centralizado extremo. Yo lo trataría como una **capacidad gobernada**:

- Modelos rápidos y más baratos para exploración cotidiana;
- Modelos más capaces para tareas complejas y justificadas;
- Revisión periódica de alternativas cuando haya deprecaciones;
- Políticas de acceso por colectivo, no café para todos.

Porque sí, elegir modelo ya no es solo una cuestión de preferencia. También es una decisión económica.

### Lo primero que yo vigilaría: patrones de uso, no solo gasto total

Cuando un producto pasa a cobrar por uso, el error más típico es abrir el panel de *billing* y mirar solo el número final. Eso, sinceramente, llega tarde.

Lo que realmente me interesa entender es **qué patrón de trabajo** está generando el consumo:

- Chats largos con mucho contexto pegado manualmente;
- Sesiones *agentic* sobre repositorios completos;
- Cambios iterativos que fuerzan muchas respuestas largas;
- Uso de modelos avanzados para tareas donde bastaría uno más ligero.

GitHub anunció además una **preview bill** para dar visibilidad previa a la transición y también ha seguido empujando mejoras de visibilidad sobre el uso. Aunque aquí no voy a entrar en informes concretos que no estén detallados en las fuentes, sí me parece evidente que GitHub está empujando a los clientes a gestionar Copilot como un servicio con observabilidad, no como una simple suscripción [(fuente)](https://github.blog/news-insights/company-news/github-copilot-is-moving-to-usage-based-billing).

Si me preguntas por una hoja de ruta razonable, yo empezaría por aquí.

### 1. Segmenta a los usuarios por tipo de trabajo

No todo el mundo consume igual. Y asumir lo contrario suele acabar en políticas torpes.

Por ejemplo:

- Quien mantiene microservicios maduros suele tirar más de completado y menos de sesiones largas;
- Quien está en *greenfield*, grandes refactors o migraciones consume más contexto y más iteración;
- Quien trabaja en enablement o plataforma puede usar Copilot para tareas más transversales y, a veces, más costosas.

Yo no intentaría optimizar nada sin esta segmentación previa. Si no la tienes, acabarás tomando decisiones injustas, inútiles o ambas cosas a la vez.

### 2. Define una estrategia de modelos por casos de uso

Aquí yo haría una matriz simple. Nada épico, nada de 14 dimensiones (que luego nadie mantiene). Algo como esto:

- **Bajo coste / alta frecuencia**: preguntas cortas, *scaffolding* acotado, ayuda con tests;
- **Coste medio / valor medio**: refactors moderados, explicación de código, documentación;
- **Coste alto / alto valor**: sesiones *agentic*, cambios multiarchivo, análisis complejos.

La idea no es imponer un modelo universal. La idea es que tú no tengas que decidir a ciegas cuándo merece la pena gastar más.

{{< figure src="/images/github-copilot-ya-no-se-paga-igual-como-pensar-creditos-modelos-y-presupuesto-si/body-3.png" alt="Matriz de selección de modelos por coste y valor" caption="Una matriz simple ayuda más que una lista infinita de modelos cuando quieres gobernar Copilot con criterio." >}}{{< /figure >}}

Y esto me parece importante: un buen *default* hace mucho más por el control de coste que una política larguísima que nadie entiende. Los *defaults* mandan. Siempre.

### 3. Pon límites de gasto y una política de escalado

Aquí me parece especialmente interesante otro cambio anunciado por GitHub: para planes individuales reabiertos, si te acercas a tus límites incluidos y adicionales, puedes **subir al siguiente plan** pagando solo la diferencia, o **seguir en el plan actual y pagar el uso adicional ya consumido** para continuar sin cambiar de nivel [(fuente)](https://github.blog/changelog/2026-06-17-copilot-individual-plan-sign-ups-are-reopening).

Aunque ese anuncio habla de planes individuales, la lección de gestión me parece trasladable también a equipos: ya no basta con elegir el plan al principio del año y olvidarte. Necesitas una política de respuesta cuando un colectivo agota su capacidad prevista.

Yo definiría tres estados muy simples:

- **Verde**: uso dentro de lo esperado;
- **Ámbar**: aumento puntual justificado por un proyecto o un pico concreto;
- **Rojo**: consumo sostenido que obliga a revisar modelo, prácticas o plan.

La clave, para mí, es que el paso de ámbar a rojo no sea automático ni emocional. Tiene que apoyarse en contexto: entregables, tipo de trabajo y retorno esperado. Porque si no, acabas gestionando a golpe de susto, y eso nunca sale bien.

### 4. Asume que habrá rotación y deprecaciones

En muy poco tiempo hemos visto anuncios de retirada de modelos y sugerencias de reemplazo dentro de Copilot [(fuente)](https://github.blog/changelog/2026-07-02-upcoming-deprecation-of-gemini-2-5-pro-and-gemini-3-flash) [(fuente)](https://github.blog/changelog/2026-06-18-upcoming-deprecation-of-opus-4-6-fast). Eso significa algo bastante simple: tu estrategia no puede depender de un único modelo «estrella».

Para mí, la práctica sana sería mantener siempre:

- Un modelo preferente por defecto;
- Un modelo alternativo equivalente para contingencia o transición;
- Una revisión mensual de catálogo y políticas.

{{< figure src="/images/github-copilot-ya-no-se-paga-igual-como-pensar-creditos-modelos-y-presupuesto-si/source-4.jpg" alt="Anuncio de retirada de GitHub Models" caption="La retirada de GitHub Models refuerza la idea de separar productividad en GitHub de plataforma de IA generalista. Fuente: [github.blog](https://github.blog/changelog/2026-07-01-github-models-is-being-fully-retired-on-july-30-2026)" >}}{{< /figure >}}

No es burocracia. Es higiene operativa. Que suena menos emocionante, sí, pero suele evitar incendios.

### GitHub Models se retira: otra pista de por dónde va la plataforma

Hay otro movimiento que yo no ignoraría: **GitHub Models se retira completamente el 30 de julio de 2026**, incluyendo *playground*, catálogo, *inference API* y BYOK. GitHub recomienda para acceso a modelos en nuevos proyectos usar **Azure AI Foundry**, y para flujos de trabajo directamente en GitHub apoyarse en **GitHub Copilot** [(fuente)](https://github.blog/changelog/2026-07-01-github-models-is-being-fully-retired-on-july-30-2026).

Mi interpretación es que aquí se dibuja una separación bastante más nítida entre dos capas:

- **Copilot** como experiencia de productividad dentro de GitHub;
- **Azure AI Foundry** como plataforma más amplia para construir soluciones de IA con catálogo de modelos.

Y esto, para arquitectura empresarial, importa bastante. Si mezclas ambos casos de uso, acabarás comparando mal costes y mal capacidades. Copilot no sustituye automáticamente a una plataforma de IA generalista. Y una plataforma de IA generalista tampoco sustituye la ergonomía de Copilot en el día a día del desarrollador.

Son cosas distintas. Relacionadas, sí. Intercambiables, no.

### La política mínima que yo sí dejaría por escrito

Si mañana tuviera que documentar esto para un equipo de plataforma, yo no haría un documento de 30 páginas (entre otras cosas, porque luego nadie lo relee). Haría una política breve, clara y accionable, con cinco reglas:

1. **Copilot es un servicio con presupuesto**, no una licencia plana sin fricción.
2. **El modelo por defecto debe optimizar coste/valor**, no maximizar capacidad teórica.
3. **Los modelos premium se reservan para escenarios concretos** y revisables.
4. **Toda deprecación debe tener plan de sustitución** antes de la fecha límite.
5. **El consumo se revisa por patrones y equipos**, no solo por total mensual.

Y, sobre todo, intentaría evitar dos extremos.

El primero: bloquear tanto que nadie pueda usar bien la herramienta.

El segundo: abrirlo todo y confiar en que «ya se autorregulará». En mi experiencia, eso rara vez ocurre cuando la experiencia de uso es muy buena y el coste llega diferido.

### Mi conclusión

Creo que el cambio de GitHub Copilot a facturación por uso obliga a madurar la conversación. Ya no estamos solo comprando productividad. Estamos diseñando una combinación de **experiencia de desarrollador, cartera de modelos y control financiero**.

La buena noticia es que esto no tiene por qué convertirse en burocracia. Si segmentas bien, defines *defaults* sensatos y asumes que el catálogo de modelos va a cambiar, puedes mantener una experiencia excelente sin perder visibilidad del gasto.

La mala noticia es la contraria: si no haces nada, el coste dejará de ser predecible justo cuando más dependas de la herramienta.

Y para mí, esa es la idea central de todo esto: en esta nueva fase de Copilot, **elegir modelo ya es también elegir presupuesto**.
