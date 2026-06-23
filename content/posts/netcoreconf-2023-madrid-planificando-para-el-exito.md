---
title: "¡Planificando para el éxito!"
excerpt: "Este es el artículo técnico con el detalle de todo lo que mostré durante mi sesión para la Netcoreconf 2023 en Madrid sobre cómo usar los Planners de Semantic Kernel para poder realizar las metas solicitadas por los usuarios."
date: 2023-11-20 00:00:00 +0000
lastmod: 2023-11-20 00:00:00 +0000
url: "/posts/netcoreconf-2023-madrid-planificando-para-el-exito/"
image:
 path: /images/2023-11-20-netcoreconf-2023-madrid-planificando-para-el-exito/header.jpg
 thumbnail: /images/2023-11-20-netcoreconf-2023-madrid-planificando-para-el-exito/thumbnail.png
categories:
  - Eventos
  - Netcoreconf
  - Inteligencia Artificial
  - Semantic Kernel
  - Tutorial
---
¡Pues ya tenemos publicado en <a href="https://youtu.be/oE1NIXiq-hE?si=t7b_jr948XQGu-bi" target="_blank" rel="noopener noreferrer">YouTube</a> la sesión que di <a href="/posts/nos-vemos-en-la-net-core-conf-2023-madrid) en la [Netcoreconf 2023](https://netcoreconf.com/" target="_blank" rel="noopener noreferrer">hace unas semanas</a> de Madrid junto con mi complice habitual <a href="https://www.linkedin.com/in/borja-piris/" target="_blank" rel="noopener noreferrer">Borja Piris de Castro</a>.

En esta charla, estuve dando una introducción técnica a una de las abstracciones más esotéricas dentro del Semantic Kernel conocidas como los Planificadores, los cuales no son más que plugins que trae por defecto la librería y que sirven principalmente como orquestadores que eligen y ejecutan de entre toda la colección de funciones que tenga cargada el *kernel* aquellas que permitirían cumplir con un objetivo específico.

{{< responsive-embed url="https://www.youtube.com/embed/oE1NIXiq-hE?si=2O-Nsjjz7LS-POmw" ratio="16:9" title="¡Planificando para el éxito! Usando los Planners de Semantic Kernel para realizar metas." class="image-border" style="width:70%" >}}{{< /responsive-embed >}}

Los planificadores son realmente muy útiles en aquellos escenarios donde la colección de funciones disponibles es tán amplia que, para los desarrolladores de un *plugin* o un Copilot, sería imposible determinar todas las posibles combinatorias de los flujos que se necesitarían ejecutar para satisfacer todas las posibles permutaciones de las solicitudes de los usuarios.

En esos casos, la solución que escala mejor es aquella en la que el *kernel* pudiera aprender cómo combinar las funciones que tiene disponibles automáticamente sobre la marcha. Aquí es donde entran los planificadores, los cuales son en sí mismos funciones que toman la solicitud de un usuario (el objetivo) y devuelve un plan sobre cómo y qué funciones ejecutar para obtener un resultado para esa la solicitud. Los planificadores consiguen hacer esto haciendo uso de la Inteligencia Artificial para mezclar y combinar los *plugins* y sus funciones registradas en el *kernel*, recombinándolas en una serie de pasos que completan el objetivo solicitado. Y eso es algo muy poderos, porque a través de los planificadores será posble crear y utilizar funciones atómicas que podrían combinarse de maneras en las que sus desarrolladores quizás no hayan jamás imaginado.

Para .NET existen actualmente cuatro planificadores: 

- Action Planner
- Sequential Planner
- Stepwise Planner
- Custom Planner

En la hoja de ruta del equipo de Semantic Kernel está pautado ir agregado planificadores más sofisticados con cada nueva versión:

A continuación te mostraré como funcionan cada uno de éstos, y los mejores escenarios para utilizarlos. Recuerda que todo el código fuente lo tienes disponible en mi <a href="https://github.com/rliberoff/.NET-Core-Conf-2023" target="_blank" rel="noopener noreferrer">GitHub aquí</a>.

También al final de este artículo encontrarás las *slides* completas de la sesión.

### Action Planner

El «Action Planner» opera identificando la función más relevante de las funciones registradas en el *kernel* que podría servir para logra el objetivo del usuario. Lo que lo diferencia de otros planificadores es que solo elige una única función a ejecutar.

Puede parecer un poco raro que sea útil algo que sólo considera una única función, sin embargo resulta que este planificador es útil en escenarios en los que ya se han definido otros planificadores de orden superior que logran la intención u objetivo del usuario y simplemente necesita un mecanismo para elegir el correcto. Esto es interesante pues nada impide que tengamos muchos planificadores instanciados y que relamente lo que necesitemos es elegir de entre éstos el que debemos ejecutar. Esto hace que el «Action Planner» sea muy eficiente y sea utilizado para escenarios de baja latencia.

El «Action Planner» funciona implementando un patrón de detección de intenciones, que identifica la intención de un usuario para el objetivo que desea cumplir, y la compara con las funciones disponibles en el *kernel*. Una vez que encuentra la función que más se alinea con el objetivo del usuario, utiliza Inteligencia Articial para completar los parámetros de entrada necesarios.

De la sesión en la Netcoreconf, el código que mostré para este planificador fue el siguiente:

```csharp
private static void InitKernel(IKernel kernel, IOptions<BingOptions> bingOptions, IOptions<SmtpClientOptions> smptOptions)
{
    kernel.ImportSemanticFunctionsFromDirectory(PluginsDirectory, @"TextPlugin", @"MealsPlugin");

    kernel.ImportFunctions(new TextPlugin(), nameof(TextPlugin));
    kernel.ImportFunctions(new WebSearchEnginePlugin(new BingConnector(bingOptions.Value.Key)), nameof(WebSearchEnginePlugin));
    kernel.ImportFunctions(new SendEmailPlugin(smptOptions), nameof(SendEmailPlugin));
}
...
public async Task<IActionResult> ActionPlannerDemoAsync(PlannerRequest request, CancellationToken cancellationToken)
{
    var actionPlan = await new ActionPlanner(kernel).CreatePlanAsync(request.Goal, cancellationToken);

    if (actionPlan.Steps.Count == 0)
    {
        return BadRequest(new PlannerResponse()
        {
            Output = @"Could not create a plan. Check that the goal is supported by the planner, configured plug-ins, and functions!",
            Plan = actionPlan.ToJson(true),
        });
    }

    var result = await kernel.RunAsync(cancellationToken, actionPlan);

    return Ok(new PlannerResponse()
    {
        Output = result.GetValue<string>(),
        Plan = actionPlan.ToJson(true),
    });
}
```

Del código anterior, lo que hacemos es inicializar un *kernel* con una serie de *plugins* (y sus respectivas funciones). Seguidamente contamos con una acción de un controllador que recibe el objetivo del usuario (*goal*) e instancia un «Action Planner» el cual recibe como parámetro el *kernel* para poder buscar entre la colección de funciones la que mejor se adecúe a la consecuón del objetivo del usuario.

Al trabajar con ciertos planificadores, es importante determinar si se han encontado pasos a ejecutar. En caso contrario, lo más conveniente es devolver un mensaje al usuario para poder informar de la imposibilidad de poder satisfacer su objetivo. En el caso del «Action Planner» esto puede pasar por dos razones:

1. El objetivo del usuario involucra dos acciones, por ejemplo "*crear un texto y mandarlo por correo electrónico*".
2. Efectivamente en el *kernel* no hay cargado un plugin con funciones que identifiquen poder cumplir con el objetivo del usuario.

### Sequential Planner

A diferencia del «Action Planner», el «Sequential Planner» destaca como un poderoso planificador capaz de ejecutar una serie de pasos pasando resultados de un paso al siguiente según corresponda de forma serial. Esto se convierte en una gran solución para escenarios en los que necesitas secuenciar funciones. Por ejemplo, realizar una búsqueda en la web sobre un tema específico para seguidamente necesitar obtener un resumen en texto del mismo que finalmente debe ser enviado como un correo electrónico a una o varias direcciones. Cada una de estas acciones corresponderían a funciones de diferentes *plugins* individuales que entre sí pueden parecer desconectados, pero gracias a un «Sequential Planner» y el poder de un LLM aporpiado se podría convertir en planes eficientes que permiten un flujo de datos fluido y listo para su ejecución.

De la sesión en la Netcoreconf, el código que mostré para este planificador fue el siguiente:

```csharp
private const int MaxTokens = 2000;
...
public async Task<IActionResult> SequentialPlannerDemoAsync(PlannerRequest request, CancellationToken cancellationToken)
{
    var sequentialPlannerConfig = new SequentialPlannerConfig
    {
      RelevancyThreshold = 0.6,
      MaxTokens = MaxTokens
    };

    var sequentialPlan = await new SequentialPlanner(kernel, sequentialPlannerConfig).CreatePlanAsync(request.Goal, cancellationToken);

    if (sequentialPlan.Steps.Count == 0)
    {
        return BadRequest(new PlannerResponse()
        {
            Output = @"Could not create a plan. Check that the goal is supported by the planner, configured plug-ins, and functions!",
            Plan = sequentialPlan.ToJson(true),
        });
    }

    var result = await kernel.RunAsync(cancellationToken, sequentialPlan);

    return Ok(new PlannerResponse()
    {
        Output = result.GetValue<string>(),
        Plan = sequentialPlan.ToJson(true),
    });
}
```

Como se puede apreciar, no es muy diferente del código del «Action Planner», salvo que el plan que se genera considera más de una función a ejecutar. Como en el caso del «Action Planner», debemos determinar si se han generado pasos, pues en caso contrario debemos notificar al usuario la imposibilida de poder satisfacer su objetivo. En este caso, a diferencia del «Action Planner» será exclusivamente porque el *kernel* no tiene configurado *plugins* o funciones que pudiera haber identificado como idóneas para conseguir el objetivo.

Por otro laso, un «Sequential Planner» tiene ciertos elementos de configuración, tales como el `RelevancyThreshold` que permite que el planificador filtre funciones irrelevantes al crear planes. Esto significa que durante la generación del plan solo se considerarán las funciones que se consideren relevantes para el objetivo determinado, lo que dará como resultado planes más centrados y eficientes. Este  filtrado puede ayudar a mejorar el rendimiento general del proceso de planificación y aumentar la probabilidad de generar planes exitosos para lograr objetivos complejos.

También es posible establecer que funciones deben ser excluidas por el planificador y no tomadas en cuenta a la hora de generar el plan, independientemente del umbral de relevancia que se establezca.

### Stepwise Planner

El «Stepwise Planner» es un poderoso planificador basado en una arquitectura neurosimbólica denominada en sus términos en ingles como «Modular Reasoning, Knowledge and Language» (<a href="https://arxiv.org/pdf/2205.00445.pdf" target="_blank" rel="noopener noreferrer">MRKL</a>, y pronunciado *miracle* en Inglés).

Este planificador tiene un enfoque único que permite a los desarrolladores ejecutar planes paso a paso para lograr objetivos complejos dentro de sus aplicaciones. El «Stepwise Planner» es una excelente opción cuando tienes un escenario que requiere una selección dinámica de funciones para lidiar con solicitudes complejas de varios pasos interconectados. Este planificador puede "aprender" de sus errores mientras "explora" las funciones disponibles en el *kernel* para determinar cómo resolver un problema y conseguir el objetivo del usuario.

De la sesión en la Netcoreconf, el código que mostré para este planificador fue el siguiente:

```csharp
private const int MaxTokens = 2000;
...
public async Task<IActionResult> StepwisePlannerDemoAsync(PlannerRequest request, CancellationToken cancellationToken)
{
    var plannerConfig = new StepwisePlannerConfig
    {
        MinIterationTimeMs = 1500,
        MaxIterations = 5,
        MaxTokens = MaxTokens,
    };

    var stepwisePlan = new StepwisePlanner(kernel, plannerConfig).CreatePlan(request.Goal);
    var result = await kernel.RunAsync(cancellationToken, stepwisePlan);

    return Ok(new PlannerResponse()
    {
        Output = result.GetValue<string>(),
        Plan = stepwisePlan.ToJson(true),
    });
}
```

Ahora, este código de por si no nos dice mucho sin el ejemplo del objetivo que pedimos en su momento. Lo que haremos es pedirle que cree una receta vegana empleando huevos, los cuales obviamente no pueden ser empleados en este tipo de comidas al ser un producto de origen animal. Lo que va a ocurrir es que el planificador entrará en duda de cómo poder cumplir con el objetivo del usuario, por lo cual buscará a través de Bing confirmar si los huevos son utilizables en recetas veganas o no, y al determinar que no lo son, retorna un "No es Posible" como resultado. Esto lo puedes ver en las trazas de la ejecución:

{{< figure src="/images/2023-11-20-netcoreconf-2023-madrid-planificando-para-el-exito/logs.png" class="align-center" caption="Haz click para ver la imagen más grande." imageBorder="true" >}}{{< /figure >}}

Recuerda que tienes más detalle de todo esto en el código de esta publicación en mi <a href="https://github.com/rliberoff/.NET-Core-Conf-2023" target="_blank" rel="noopener noreferrer">GitHub aquí</a>.

## ¿Dónde está la mágia?

Como decía antes, los planificadores no son más que *plugins* para Semantic Kernel con funciones que utilizan mensajes para un LLM (*Large Language Model*), habitualmente alguno de OpenAI, para generar un plan. Por ejemplo, el mensaje que utiliza el «Sequential Planner» lo podeos encontrar en el código fuente de Semantic Kernel dentro de un archivo `skprompt.txt` (es decir, que es una <a href="https://youtu.be/jc6H8gmXAAA?si=bnXygSteId3XR64Q" target="_blank" rel="noopener noreferrer">función semántica</a>), y parece algo así como lo siguiente:


```text
Create an XML plan step by step, to satisfy the goal given.
To create a plan, follow these steps:
0. The plan should be as short as possible.
1. From a <goal> create a <plan> as a series of <functions>.
2. Before using any function in a plan, check that it is present in the most recent [AVAILABLE FUNCTIONS] list. If it is not, do not use it. Do not assume that any function that was previously defined or used in another plan or in [EXAMPLES] is automatically available or compatible with the current plan.
3. Only use functions that are required for the given goal.
4. A function has a single 'input' and a single 'output' which are both strings and not objects.
5. The 'output' from each function is automatically passed as 'input' to the subsequent <function>.
6. 'input' does not need to be specified if it consumes the 'output' of the previous function.
7. To save an 'output' from a <function>, to pass into a future <function>, use <function.{FunctionName} ... setContextVariable: "<UNIQUE_VARIABLE_KEY>"/>
8. To save an 'output' from a <function>, to return as part of a plan result, use <function.{FunctionName} ... appendToResult: "RESULT__<UNIQUE_RESULT_KEY>"/>
9. Append an "END" XML comment at the end of the plan.

[AVAILABLE FUNCTIONS]

{{$available_functions}}

[END AVAILABLE FUNCTIONS]

<goal>{{$input}}</goal>
```


Por lo tanto, realmente lo que ocurre cuando utilizamos un planificador es que estamos instanciando un *plugin* o función, pasándole algunos parámetros especificos y recibiendo el resultado el cual no es más que el producto de sucesivas llamadas a un LLM.

Cada planificador es capaz de identificar que funciones necesita incluir a partir de la propiedad `description` de la función y de sus parámetros.

Por ejemplo, del siguiente JSON, un LLM que esté siendo utilizado por un planificador podrá saber que la función descrita sirve para "*crear recetas para un estilo de vida vegano*" y que hay dos parámetros: uno para indicar el tipo de plato a preparar (entrante, principal o postre) y otro para indicar el ingrediente principal a utilizar:

```json
{
  "schema": 1,
  "description": "A Nutrition Coach with expertise in a Vegan lifestyle who creates vegan recipes for any course dish.",
  "models": [
    {
      "max_tokens": 2000,
      "temperature": 0.9,
      "top_p": 0.0,
      "presence_penalty": 0.0,
      "frequency_penalty": 0.0,
      "stop_sequences": [
        "[done]"
      ]
    }
  ],
  "input": {
    "parameters": [
      {
        "name": "input",
        "description": "The course of the vegan dish you want the recipe to prepare. For example: Starter, Main, or Dessert.",
        "defaultValue": ""
      },
      {
        "name": "mainIngredient",
        "description": "The main ingredient to use in the recipe to prepare.",
        "defaultValue": "[No main ingredient]"
      }
    ]
  }
}
```

Gracias a dicho campo `description` combinado con los *prompts* de los planificadores, es que se contruyen los planes tan sofisticados que son capaces de generar el «Sequential Planner» o el «Stepwise Planner».

## Trucos, pros y contras

- Ten en cuenta que usar planificadores tiene un impacto importante en el rendimiento de tus aplicaciones. Los planificadores son lentos.
- Puesto que los planificadores realizan varias llamadas al LLM, pueden incrementar de forma importante tu costo por consumo de estos servicios.
- Recuerda que esta tecnología no es discreta sino estocástica, y por lo tanto siempre existe la posibilidad de que se generen planes defectuosos. Para que el planificador sea sólido, lo mejos es  proporcionar un adecuado manejo de errores. Por ejemplo, si el planificador debe retornar un esquema con formato específico (JSON, XML, etc.) y genera un resultado incorrecto o con esquema inválido, se podría implementar una política de reintentos solicitando al planificador que "arregle" el plan.
- La mejor manera de mitigar un consumo exesivo es excluyendo aquellas funciones que sabemos nuestro planificador no debería tomar en cuenta.
- También ayuda a planificar mejor el proporcionar descripciones verbosas, completas, concretas y no ambiguas de cada función y sus parámetros de entrada. En la descripción de la función se puede especificar por ejemplo la salida de la misma.

## Para cerrar

Finalmente, aquí os dejo la presentación completa de la sesión 😎

{{< responsive-embed url="https://www.slideshare.net/slideshow/embed_code/key/8fAP7L3yaRBoeL" ratio="16:9" title="¡Planificando para el éxito! Usando los Planners de Semantic Kernel para realizar metas." class="image-border" >}}{{< /responsive-embed >}}
