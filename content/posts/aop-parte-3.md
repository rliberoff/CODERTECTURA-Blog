---
title: "Framework de Programación Orientada a Aspectos (AOP) en C# - Parte 3: Manejo de Excepciones"
excerpt: "***Legacy*** - Veamos cómo implementar el manejo de excepciones como un aspecto de nuestro código usando el *framework* para Programación Ortiendata a Aspectos (AOP) en C# que hemos creado en entradas anteriores."
date: 2012-04-12 00:00:00 +0200
lastmod: 2023-10-27 00:00:00 +0200
url: "/posts/aop-parte-3/"
image:
    path: /images/2012-04-12-aop-framework-csharp-parte-3/header.jpg
    thumbnail: /images/2012-04-12-aop-framework-csharp-parte-3/thumbnail.jpg
    caption: Imágen de <a href="https://www.pexels.com/photo/an-artist-s-illustration-of-artificial-intelligence-ai-this-image-represents-the-ways-in-which-ai-can-solve-important-problems-it-was-created-by-vincent-schwenk-as-part-of-the-visualis-17485819/" target="_blank" rel="noopener noreferrer">Pexels</a>
categories:
    - Legacy
    - Tutorial
    - C#
---

{{< notice type="danger" >}}
Este tutorial es sobre una aproximación a la Programación Orinetada a Aspectos (AOP) que desarrollé hace muchos años cuando no existían _frameworks_ para este tipo de orientaciones arquitectónicas de software, o la disponibilidad no era buena. Lo mantengo en este blog como un recuerdo de mi recorrido profesional y técnico.
{{< /notice >}}

{{< notice type="info" >}}
Este es la cuarta y última parte de una serie de cuatro publicaciones que he realizando sobre programación orientada a aspectos en .NET empleando el lenguaje de programación C#.

- [Parte 0: Introducción](/posts/aop-parte-0)
- [Parte 1: Introducción](/posts/aop-parte-1)
- [Parte 2: Un aspecto para el registro de eventos (_logging_)](/posts/aop-parte-2)
{{< /notice >}}

A parte del registro de eventos, otro elemento muy común en la programación orientada a objetos y en los lenguajes actuales (como Java o C#) es la gestión de excepciones.

El otro típico _infierno_ al que se enfrenta un arquitecto o líder técnico a la hora de establecer la política de gestión de errores y excepciones en su diseño es la gobernabilidad de dicho diseño, y la monitorización de su cumplimiento por parte del equipo de desarrollo, cosa que se torna excesivamente complicada por la creatividad de algunos miembros del equipo que rompe la homogeneidad del mecanismo elegido como parte del modelo. Hasta aquí, este párrafo es prácticamente igual al de la [Parte 2](/posts/aop-parte-2) de esta serie de artículos.

Y es que el diseño y la gobernabilidad del mecanismo de gestión y manejo de excepciones adoloce de los mismos problemas y retos que que podemos encontrar con el registro de eventos.

Particularmente se encuentra que los dos (2) aspectos más difíciles de gestionar son el acto de capturar y apropiadamente manejar la excepción, seguidamente de la política a aplicar sobre ésta. Muchas veces podemos encontrarnos con aplicativos web que cuando una excepción ocurre nos muestra la temida pantalla amarilla de ASP.NET o directamente nos expone todo el _stack trace_ de la excepción (con información de base de datos y todo), lo cual fácilmente podría usar un potencial atacante para literalmente destruir el aplicativo.

{{< figure src="/images/2012-04-12-aop-framework-csharp-parte-3/asp-net-yellow-page-of-death.png" class="align-center" caption="Haz click para ver la imagen más grande." >}}{{< /figure >}}

A través del enfoque de AOP, es posible interceptar las llamadas a los métodos y determinar cuando estos han generado una excepción para posteriormente aplicar la política de manejo más apropiada. Estas políticas puede ser parte del propio aspecto de gestión de excepciones. Como en el caso del registro de eventos, la implementación de este aspecto buscará reducir su implementación (y aplicación) a un atributo que decore el método cuyas posibles excepciones se quieren gestionar.

#### Un Apropiado Soporte

Al crear un mecanismo de gestión y manejo de excepciones, no deberíamos partir desde cero, ya que existe un montón de excelentes productos y _frameworks_ que nos simplificarían esta tarea. Para este caso, emplearé los <a href="http://msdn.microsoft.com/en-us/library/ff648951.aspx" target="_blank" rel="noopener">Microsoft Libraries</a>, en particular el _Exception Handling Application Block_; sin embargo el enfoque de AOP y de este _framework_ que he venido presentado permite emplear cualquier otra _librería_.

#### Implementación

Es importante que si no han leido las primeras partes de esta serie de artículos, aprovechen este momento para hacerlo, sobre todo la [Parte 1](/posts/aop-parte-1). A partir de este momento mis explicaciones considerarán que el conocimiento y los detalles técnicos explicados en esa parte ya son conocidos.

El primer paso es crear el atributo (`Attribute`) que decorará las clases/interfaces para capturar su ejecución e inyectar el código de manejo de excepciones. Nuestro atributo se llamará `ExceptionHandlingAttribute` y extiende de `InterceptableAttribute`, la clase base en el _framework_ de AOP que sirve para definir atributos de intercepción.

```csharp
/// <summary>
/// A custom attribute for exception handling purposes under an Aspect Oriented Programming paradigm.
/// </summary>
/// <remarks>It applies only to methods.</remarks>
[AttributeUsage(AttributeTargets.Method, AllowMultiple = false, Inherited = true)]
public sealed class ExceptionHandlingAttribute : InterceptableAttribute
{
    /// <summary>
    /// Represents the exception handling politic to apply while intercepting with this concern.
    /// </summary>
    private ExceptionHandlingPolitic politic;

    /// <summary>
    /// Initializes a new instance of the <see cref="ExceptionHandlingAttribute" /> class.
    /// </summary>
    /// <param name="politic">The exception handling politic to follow.</param>
    public ExceptionHandlingAttribute(ExceptionHandlingPolitic politic)
    {
        this.politic = politic;
        this.Processor = Activator.CreateInstance(typeof(ExceptionHandlingProcessor)) as IProcessor;
    }

    /// <summary>
    /// Gets the specified exception handling politic.
    /// </summary>
    /// <value>
    /// Returns the politic to use when handling exceptions represented as a <see cref="ExceptionHandlingPolitic"/>.
    /// </value>
    public ExceptionHandlingPolitic Politic { get { return this.politic; } }
}
```

Este atributo tiene una propiedad muy importantes llamada `Politic` la cual permite establecer la política con la que se gestionará la excepción.

En el tema de políticas de manejo de excepciones hay muchas opiniones, controversias y _religiones_. En lo personal, dependen mucho de las características del sistema y del entorno donde se desplegará, pero habitalmente me decanto por las siguientes tres (3) políticas:

- `Encapsular`: o _encapsulate_ en inglés, es la política más habitualmente aplicada en la gestión de excepciones. Consiste en retornar una excepción nueva más significativa al llamador, pero agregando o anexando (encapsular) la excepción original en la nueva excepción. Esta política preserva el _stack trace_.
- `Reemplazar`: o _repace_ en inglés, consiste en retornar una nueva excepción más significativa al llamador del método, pero si agregar o anexar la excepción original; incluso pudiéndose cambiar el mensaje de la excepción. En esta política el _stack trace_ **no** se preserva.
- `Propagar`: o _propagate_ en inglés, se refiere al acto de pasar la excepción al llamador del método. Esto no quiere decir que no se gestione la excepción _per se_, sino que no se transformará o encapsulará esta. El _stack trace_ no sufre modificación alguna.

Utilizo estas políticas, porque la mayoría de mis diseños de software siguen un enfoque de capas, donde las excepciones que ocurren dentro de una misma capa son propagadas, cuando se pasa de una capa inferior a una capa superior se encapsulan, y cuando se tienen que llevar a la capa de UI o presentar la excepción al usuario, entonces se reemplaza (para evitar mostrar datos e información sensible a un potencial atacante). Otros enfoques arquitectónicos como el <a href="http://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller" target="_blank" rel="noopener">MVC</a> o el <a href="http://en.wikipedia.org/wiki/Model_View_ViewModel" target="_blank" rel="noopener">MVVC</a> muy probablemente empleen políticas totalmente diferentes.

Así, la propiedad `Politic` del atributo `ExceptionHandlingAttribute` admite valores del siguiente enumerado que representa las políticas antes mencionadas:

```csharp
/// <summary>
/// Defines the exception handling politics to use.
/// </summary>
public enum ExceptionHandlingPolitic
{
    /// <summary>
    /// Represents the propagation politic.
    /// This politic specifies that every exception will be passed to the caller without any transformation.
    /// </summary>
    Propagate,

    /// <summary>
    /// Represents the wrap politic.
    /// This politic specifies that every exception will be wrapped inside another exception and then passed to the caller.
    /// </summary>
    Wrap,

    /// <summary>
    /// Represents the replacement politic.
    /// This politic specifies that every exception will be replaced for another exception; then the new exception will be passed to the caller.
    /// </summary>
    /// <remarks>The original exception will be lost.</remarks>
    Replace
}
```

Una vez establecido el atributo de intercepción, procedemos a crear el `Processor` que se encargará de manejar la inyección de código antes y después de la ejecución de los métodos interceptados. Para esto crearemos la clase `ExceptionHandlingProcessor` que implementará la interfaz `IProcessor` del _framework_.
Esta clase es la que dependiento del valor de la propiedad `Politic` y basado en el Microsoft Enterprise Library Exception Handling Application Block procederá a manejar la excepción interceptada acorde a la configuración del mencionado Application Block.

La parte interesante es que para el caso de la gestión de excepciones no se necesitará el método `ProcessCallMessage`, ya que las excepciones como tal sólo ocurren como un retorno de método, con lo cual toda la acción ocurrirá en el método `ProcessReturnMessage`.

```csharp
 /// <summary>
/// Intercep processor for the calling and returning messages of the methods decorated as interceptable by this component.
/// </summary>
internal class ExceptionHandlingProcessor : IProcessor
{
    /// <summary>
    /// Constant that identifies the exception handling policy of propagation.
    /// </summary>
    private const string PROPAGATE = @"PROPAGATE";

    /// <summary>
    /// Constant that identifies the exception handling policy of replacement.
    /// </summary>
    private const string REPLACE = @"REPLACE";

    /// <summary>
    /// Constant that identifies the exception handling policy of wrap.
    /// </summary>
    private const string WRAP = @"WRAP";

    /// <summary>
    /// Processes the call message, which happens before the execution of the body of the interceptable or processable method.
    /// </summary>
    /// <remarks>
    /// <para>
    /// Since the exception handling only occurs after the execution of the body of the interceptable or processable method, this
    /// method does nothing.
    /// </para>
    /// <para>
    /// This is because the exception type is contained in the <c>Method Return Message</c>.
    /// </para>
    /// </remarks>
    /// <param name="callMessage">The <c>Method Call Message</c> to process.</param>
    /// <param name="processable">The processable decorated object to process.</param>
    public void ProcessCallMessage(IMethodCallMessage callMessage, InterceptableAttribute processable)
    {
        // Do Nothing.
    }

    /// <summary>
    /// Processes the return message, which happens after the execution of the body of the interceptable or processable method.
    /// </summary>
    /// <remarks>
    /// <para>
    /// Since the <c>Method Return Message</c> contains the exception type, this method processes such message to retrieve the exception
    /// information.
    /// </para>
    /// <para>
    /// This method leverages the Microsoft Enterprise Library Exception Handling Application Block.
    /// </para>
    /// </remarks>
    /// <param name="returnMessage">The <c>Method Return Message</c> to process.</param>
    /// <param name="processable">The processable or interceptable object.</param>
    public void ProcessReturnMessage(IMethodReturnMessage returnMessage, InterceptableAttribute processable)
    {
        if (returnMessage != null &amp;amp;&amp;amp; returnMessage.Exception != null)
        {
            string policyName = null;

            switch (((ExceptionHandlingAttribute)processable).Politic)
            {
                case ExceptionHandlingPolitic.Propagate:
                    policyName = PROPAGATE;
                    break;

                case ExceptionHandlingPolitic.Replace:
                    policyName = REPLACE;
                    break;

                case ExceptionHandlingPolitic.Wrap:
                    policyName = WRAP;
                    break;

                default:
                    throw new InvalidOperationException(@"Invalid or not defined exception handling politic.");
            }

            // Call to the static main entrance of the Microsoft Enterprise Library Exception Application Block.
            if (ExceptionPolicy.HandleException(returnMessage.Exception, policyName))
            {
                throw returnMessage.Exception;
            }
        }
    }
}
```

Como puede apreciarse en el método `ProcessReturnMessage` lo primero es saber si el método interceptado a retornado una excepción, lo cual se puede determinar fácilmente si la priedad `Exception` de la interfaz `IMethodReturnMessage` (a la cual pertenece el parámetro `returnMessage`) no es nula (`null`).

De haber una excepción, basta con recuperar el valor de la propiedad `Politic` del atributo para saber que política aplicar a la excepción interceptada. La configuración de estas políticas están delegadas al archivo de configuración del _Exception Handling Application Block_, y su aplicación se realiza en la línea `79`.

Como en artículos anteriores, <a href="https://github.com/rliberoff/CODERTECTURA-Blog-AOPFramework" target="_blank" rel="noopener">aquí</a> esta el código de este aspecto para estudiarlo. Espero que sea de utilidad.
