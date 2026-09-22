---
title: 'Guided Copilot en VS Code: así cambia de verdad la forma de crear apps en
  Azure'
date: '2026-09-21T12:17:02+00:00'
draft: true
slug: guided-copilot-en-vs-code-asi-cambia-de-verdad-la-forma-de-crear-apps-en-azure
description: La experiencia guiada de Copilot en VS Code cambia el chat abierto por
  un flujo más predecible para crear y desplegar apps en Azure.
categories:
- Azure
- Inteligencia Artificial
- Arquitectura de Software
tags:
- GitHub Copilot
- Visual Studio Code
- Azure
- Despliegue
- Experiencia de desarrollo
image: /images/guided-copilot-en-vs-code-asi-cambia-de-verdad-la-forma-de-crear-apps-en-azure/cover.png
comments: true
ai:
  assisted: true
  article_type: technical
  model: gpt-5.4
  prompt_version: 2026-08-21.1
  generated_at: '2026-09-21T12:17:02+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://techcommunity.microsoft.com/t5/apps-on-azure-blog/introducing-a-guided-copilot-experience-for-building-azure-apps/ba-p/4557120
    title: Introducing a Guided Copilot Experience for Building Azure Apps in VS Code
    published_date: '2026-09-18'
  - url: https://learn.microsoft.com/en-us/azure/devops/release-notes/features-timeline-released
    title: Azure DevOps Released Features - Microsoft Learn
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/devops/repos/git/review-pull-requests?view=azure-devops
    title: Review and comment on pull requests - Azure Repos
    published_date: null
---

Hay anuncios de producto que, a primera vista, parecen una iteración menor. Y luego te paras un momento, conectas dos o tres ideas, y ves que en realidad están tocando algo bastante más profundo. Eso es exactamente lo que me pasa con la nueva [experiencia guiada de Copilot para crear aplicaciones en Azure desde VS Code](https://techcommunity.microsoft.com/t5/apps-on-azure-blog/introducing-a-guided-copilot-experience-for-building-azure-apps/ba-p/4557120).

Yo no la leo como “otro asistente más” ni como una capa bonita sobre el mismo chat de siempre. La leo como un cambio de diseño: dejar de depender de una conversación abierta y pasar a un flujo con etapas explícitas, validaciones, decisiones visibles y un camino de despliegue reconocible. Puede sonar menos espectacular. A mí, precisamente por eso, me parece más útil.

Si tú ya has intentado montar una app cloud a base de prompts libres, seguramente te suene la escena. Un día Copilot te clava medio proyecto, otro día te genera código razonable pero se deja fuera la infraestructura, y otro mezcla piezas con bastante alegría y te toca recomponerlo todo a mano. **El problema no era solo el modelo; era la forma de la experiencia.** Y ahí es donde esta propuesta me parece relevante para cualquiera que viva en VS Code, GitHub Copilot y Azure.

### Qué aporta realmente la experiencia guiada

Según describe Microsoft en [el anuncio oficial](https://techcommunity.microsoft.com/t5/apps-on-azure-blog/introducing-a-guided-copilot-experience-for-building-azure-apps/ba-p/4557120), el flujo se organiza en tres fases bastante claras: planificación y *scaffolding* del proyecto, desarrollo local y despliegue. La idea, en el fondo, es muy simple: en lugar de confiar en que un chat recuerde el contexto, haga las preguntas adecuadas y no se desvíe por el camino, la herramienta te guía con formularios, selectores y puntos de aprobación antes de generar código o tocar recursos de Azure.

Eso tiene una consecuencia práctica importante. La conversación deja de ser el contrato principal y lo pasa a ser el **plan explícito**: qué tipo de aplicación quieres, con qué lenguaje, qué servicios van a intervenir, qué herramientas faltan en tu equipo y qué recursos se van a crear al publicar. En el propio [post de presentación](https://techcommunity.microsoft.com/t5/apps-on-azure-blog/introducing-a-guided-copilot-experience-for-building-azure-apps/ba-p/4557120) la promesa se formula de una manera muy concreta: menos improvisación, más recorrido predecible desde la idea hasta una app funcionando en Azure.

{{< figure src="/images/guided-copilot-en-vs-code-asi-cambia-de-verdad-la-forma-de-crear-apps-en-azure/body-1.png" alt="Diagrama de las tres fases de Guided Copilot para Azure" caption="La propuesta gira en torno a tres etapas: planificar, validar en local y desplegar con herramientas estándar de Azure." >}}{{< /figure >}}

Yo aquí veo una tesis bastante nítida: esto no intenta sustituir el valor del chat libre, sino **meterlo dentro de una experiencia con barandillas**. Y, sinceramente, para trabajar con cloud me parece una decisión sensata. Cuando ya no estás pidiendo solo una clase o un endpoint, sino infraestructura, dependencias locales, configuración de depuración y despliegue, la libertad total deja de ser tan romántica como parecía y empieza a convertirse en variabilidad.

### Antes de empezar

Si quieres reproducir hoy una parte parecida del flujo que describe la experiencia guiada, yo partiría de unos prerrequisitos muy concretos:

- **Visual Studio Code** actualizado.
- **GitHub Copilot** activo en tu cuenta y con la extensión instalada en VS Code.
- **Azure CLI 2.75 o superior** instalado y autenticado.
- **Azure Developer CLI (`azd`)** instalado.
- **Node.js 20 LTS** para el ejemplo práctico.
- Una **suscripción de Azure** donde puedas crear recursos.
- Permisos suficientes para desplegar; en la práctica, yo asumiría al menos rol de **Contributor** sobre la suscripción o sobre el grupo de recursos donde vayas a trabajar.

Para verificar rápido que la base está lista, yo usaría esto:

```bash
az version --output json
azd version
node --version
```

Lo razonable es ver una versión de `az` igual o superior a 2.75, una versión 1.x de `azd` y Node.js 20.x. Y antes de abrir el proyecto, mejor dejar resuelta la autenticación:

```bash
az login
azd auth login
```

Lo normal es que se abra el navegador para iniciar sesión y que ambas herramientas queden preparadas para trabajar con tu suscripción activa. Parece un detalle menor, pero no lo es: si algo quiere corregir esta experiencia guiada es precisamente el clásico arranque torpe en el que la mitad de los problemas no están en la app, sino en el entorno.

### El cambio importante: de prompt abierto a workflow opinado

El detalle del anuncio que más me interesa no es la interfaz, sino el hecho de que el despliegue se apoya en herramientas reales de Azure como [Azure CLI y Azure Developer CLI, `az` y `azd`](https://techcommunity.microsoft.com/t5/apps-on-azure-blog/introducing-a-guided-copilot-experience-for-building-azure-apps/ba-p/4557120). Para mí, eso es lo que le da credibilidad a la propuesta. Reduce la distancia entre “lo que hace el asistente” y “lo que luego tu equipo puede repetir, revisar o automatizar sin depender de una demo”.

Si me preguntas por qué esto importa desde el punto de vista de arquitectura, yo lo resumiría así: hace más visible la frontera entre aplicación e infraestructura. En una experiencia de chat puro, esa frontera se difumina mucho; a veces descubres demasiado tarde qué recursos se van a crear, cómo se va a desplegar o qué dependencias tenías que haber instalado antes. En una experiencia guiada, la promesa va justo en dirección contraria: ver el plan, el coste estimado y el conjunto de recursos antes de ejecutar.

**No es solo comodidad; es una forma de gobernanza ligera desde el minuto uno.** Y eso encaja muy bien con equipos que quieren ir rápidos sin renunciar del todo a la repetibilidad.

### Ejemplo 1: preparar el proyecto y desplegarlo con `azd`

Como la funcionalidad anunciada se apoya en el *tooling* de Azure para el despliegue, la manera más realista de reproducir hoy la parte verificable del flujo es arrancar un proyecto basado en `azd`, aprovisionar infraestructura y publicarlo. No sustituye la UI guiada de VS Code, pero sí te permite validar el núcleo operativo sobre el que se apoya.

Primero crea una carpeta de trabajo, inicializa el proyecto y define un entorno. Este ejemplo está pensado para **Azure Developer CLI (`azd`) 1.x** y **Azure CLI 2.75+**:

```bash
mkdir guided-copilot-azure-app
cd guided-copilot-azure-app
azd init --template todo-nodejs-mongo --environment dev # fijo el entorno desde el inicio para evitar prompts extra y hacer el flujo más reproducible
```

Lo esperable es que `azd` inicialice la plantilla y deje creado el entorno `dev`. Ese paso ya anticipa una de las ideas fuertes de la experiencia guiada: partir de una intención de aplicación y aterrizarla en una estructura de proyecto con infraestructura asociada, no en un puñado de archivos sueltos.

Después lanza el aprovisionamiento y el despliegue completo:

```bash
azd up
```

Durante la ejecución, `azd` te pedirá la suscripción y la región si todavía no las has fijado, creará los recursos necesarios y después publicará la aplicación. Al final deberías ver un resumen con los recursos creados y la URL pública del servicio.

```text
Provisioning Azure resources...
Deploying services...
SUCCESS: Your up workflow to provision and deploy to Azure completed.

Endpoint:
  web: https://app-guidedcopilot-dev.azurewebsites.net/
```

A mí este detalle me parece especialmente valioso porque conecta con una de las promesas del anuncio: evitar el clásico “te genero algo, pero el script falla a mitad y luego ya te apañas”. Aquí el despliegue deja de depender de una improvisación del modelo y se apoya en una cadena conocida, repetible y bastante menos frágil.

{{< figure src="/images/guided-copilot-en-vs-code-asi-cambia-de-verdad-la-forma-de-crear-apps-en-azure/body-2.png" alt="Secuencia de despliegue con azd desde VS Code a Azure" caption="Detrás de la experiencia guiada, el valor real está en apoyarse en un camino de despliegue repetible con az y azd." >}}{{< /figure >}}

### Verificación del despliegue

Una vez publicado, yo comprobaría dos cosas. La primera, que el entorno generado por `azd` contiene los valores esperados. La segunda, que los recursos realmente existen en Azure y no solo en la narrativa optimista de la consola (que a veces también pasa).

Para inspeccionar el entorno con **Azure Developer CLI (`azd`) 1.x**, usaría esto:

```bash
azd env get-values
```

Lo razonable es ver algo parecido a esto:

```text
AZURE_ENV_NAME="dev"
AZURE_LOCATION="westeurope"
AZURE_SUBSCRIPTION_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
SERVICE_WEB_ENDPOINT="https://app-guidedcopilot-dev.azurewebsites.net/"
```

Y para listar los recursos creados con **Azure CLI 2.75+**:

```bash
az resource list \
  --resource-group rg-guided-copilot-dev \
  --output table
```

Si el grupo tiene otro nombre, usa el que te haya devuelto `azd up`. Lo normal es encontrar App Service, el plan asociado y el resto de recursos definidos por la plantilla elegida.

```text
Name                               ResourceGroup              Location    Type
---------------------------------  -------------------------  ----------  ----------------------------------------
app-guidedcopilot-dev              rg-guided-copilot-dev      westeurope  Microsoft.Web/sites
app-guidedcopilot-dev-plan         rg-guided-copilot-dev      westeurope  Microsoft.Web/serverfarms
...
```

Lo interesante aquí no es solo que funcione, sino que el resultado sea observable y revisable. Esa diferencia, que parece pequeña, es justo la que separa una ayuda puntual de un flujo de trabajo de verdad.

### Ejemplo 2: comparar un enfoque guiado frente a un prompt libre

Para mí, el valor de esta experiencia no se entiende del todo hasta que la comparas mentalmente con una petición abierta. Imagina que quieres “una API Node.js en Azure con base de datos y despliegue”. En un chat libre, ese prompt puede acabar en resultados bastante distintos según cómo continúe la conversación. En el enfoque guiado, en cambio, la intención se traduce en decisiones explícitas antes de tocar nada importante.

Yo haría la comparación de una forma muy simple dentro de VS Code. Primero, escribe una intención breve y concreta, algo como esto, y guárdala para reutilizarla en ambas pruebas:

```text
Crear una API Node.js para tareas en Azure.
Necesito ejecución serverless, persistencia gestionada y despliegue reproducible.
Quiero poder ejecutarla en local antes de publicarla.
```

Lo que deberías observar en el flujo guiado, según [la descripción del anuncio](https://techcommunity.microsoft.com/t5/apps-on-azure-blog/introducing-a-guided-copilot-experience-for-building-azure-apps/ba-p/4557120), es que VS Code te pida concretar lenguaje, tipo de aplicación y servicios de Azure mediante interfaz, y que no se ponga inmediatamente a escupir archivos. Primero plan. Después *scaffolding*. Y luego validación del entorno local antes del despliegue.

Para contrastarlo con el chat libre, yo usaría una lista de verificación muy terrenal:

- ¿Propone arquitectura antes de generar código?
- ¿Explica qué recursos de Azure va a crear?
- ¿Comprueba dependencias locales?
- ¿Deja el proyecto listo para ejecutar al primer intento?
- ¿Te da un camino de despliegue reproducible con `az` o `azd`?

{{< figure src="/images/guided-copilot-en-vs-code-asi-cambia-de-verdad-la-forma-de-crear-apps-en-azure/body-3.png" alt="Comparativa entre chat libre y flujo guiado" caption="La diferencia no está en pedir menos a la IA, sino en pedirle dentro de un proceso con checkpoints y decisiones visibles." >}}{{< /figure >}}

Si quieres objetivar un poco más la comparación, puedes añadir una verificación local sobre el proyecto resultante. En una aplicación Node.js típica con **Node.js 20**, la prueba mínima sería esta:

```bash
npm install
npm run start
```

Lo razonable es que el proyecto arranque y exponga un endpoint local sin obligarte a pasar por varias rondas de reparación manual. Y ahí está, para mí, la métrica que realmente importa: **no que “genere cosas”, sino que la primera ejecución local y el primer despliegue fallen menos**.

### Qué significa esto para un equipo real

Yo no vendería esta novedad como magia (ya sabes que cuando una demo parece magia, normalmente hay bastante fregado detrás). La vendería como una mejora clara en la ergonomía del proceso. Cuando un equipo trabaja con Azure, lo difícil rara vez es conseguir un controlador, un endpoint CRUD o un archivo más. Lo difícil es alinear intención, arquitectura, entorno local, infraestructura y despliegue sin que cada desarrollador acabe improvisando su propia ruta.

En ese sentido, esta experiencia guiada apunta a un sitio bastante razonable: mantenerte dentro de VS Code, ayudarte a concretar decisiones con interfaz en lugar de con párrafos de chat, y apoyarse en herramientas que luego puedes ejecutar también fuera del asistente. A mí eso me parece una diferencia importante frente a esas experiencias de IA que deslumbran mucho el primer día y dejan poco artefacto reutilizable el segundo.

También le veo una lectura interesante desde el gobierno técnico. Si la herramienta te muestra antes los recursos, el coste estimado y el método de despliegue, te obliga a tomar decisiones de forma más visible. No resuelve por sí sola la disciplina de arquitectura —ojalá—, pero sí empuja a que exista un momento de validación que en un chat libre es mucho más fácil saltarse.

### Mis reservas: dónde puede quedarse corta

Dicho todo esto, yo mantendría dos cautelas. La primera es bastante obvia: “más guiado” también significa “más opinado”. Y eso suele ir muy bien en escenarios frecuentes, pero puede volverse rígido cuando tu arquitectura se sale del carril esperado. Si necesitas combinaciones menos comunes, el flujo guiado tendrá que demostrar que no se convierte en una jaula con buena iluminación.

La segunda cautela tiene más que ver con la ejecución real que con la idea. La previsibilidad prometida depende mucho de la calidad de las plantillas, de la integración efectiva con `az` y `azd`, y de cómo conserve Copilot el contexto cuando vuelves días después a retocar la solución. El propio [anuncio menciona que Copilot retiene el contexto de la arquitectura del proyecto](https://techcommunity.microsoft.com/t5/apps-on-azure-blog/introducing-a-guided-copilot-experience-for-building-azure-apps/ba-p/4557120), y yo diría que ahí está una parte importante del examen de verdad.

### Mi conclusión

A mí esta evolución me gusta porque deja de tratar el desarrollo cloud como una conversación inspiracional y empieza a tratarlo como un flujo de trabajo. Puede parecer menos brillante en una demo de cinco minutos, pero sospecho que será bastante más útil en el día a día. Para crear aplicaciones en Azure, **yo prefiero una IA que me haga avanzar por etapas verificables antes que una IA que improvise muy bien durante cinco prompts y me deje solo en el sexto**.

Si tú trabajas con VS Code, GitHub Copilot y Azure, yo seguiría esta novedad de cerca. No porque elimine la necesidad de entender arquitectura, despliegue o costes —eso no te lo va a regalar nadie—, sino porque puede reducir bastante la fricción entre tener una idea y convertirla en una aplicación reproducible, ejecutable en local y desplegable con herramientas estándar. Y, sinceramente, ahí es donde estas experiencias empiezan a tener valor de verdad.
