---
title: "Framework de Programación Orientada a Aspectos (AOP) en C# - Parte 2: Registro de Eventos (*Logging*)"
excerpt: "***Legacy*** - Veamos cómo implementar el registro de eventos o trazas (*logging*) como un aspecto de nuestro código usando el *framework* para Programación Ortiendata a Aspectos (AOP) en C# que hemos creado en entradas anteriores."
date: 2012-04-11 00:00:00 +0200
last_modified_at: 2023-10-27 00:00:00 +0200
layout: post
permalink: /aop/parte-2
image:
    path: /images/2008-03-07-realizaciones-o-de-cuando-me-fui-de-venezuela/header.avif
    thumbnail: /images/2008-03-07-realizaciones-o-de-cuando-me-fui-de-venezuela/thumbnail.avif
categories:
    - Legacy
    - Tutorial
    - C#
---

{% capture notice-text %}
Este tutorial es sobre una aproximación a la Programación Orinetada a Aspectos (AOP) que desarrollé hace muchos años cuando no existían _frameworks_ para este tipo de orientaciones arquitectónicas de software, o la disponibilidad no era buena. Lo mantengo en este blog como un recuerdo de mi recorrido profesional y técnico.
{% endcapture %}

<div class="notice--danger" style="font-size: small; font-weight: bold;">
  {{ notice-text | markdownify }}
</div>

{% capture notice-text %}
Este es la tercera parte de una serie de cuatro publicaciones que he realizando sobre programación orientada a aspectos en .NET empleando el lenguaje de programación C#.

- [Parte 0: Introducción](/aop/parte-0)
- [Parte 1: Introducción](/aop/parte-1)
- [Parte 3: Un aspecto para el manejo de excepciones](/aop/parte-3)
{% endcapture %}

<div class="notice--info" style="font-size: medium;">
  {{ notice-text | markdownify }}
</div>

El que es quizás sea el ejemplo más sencillo de un aspecto es el registro de eventos de un sistema o aplicación. Así mismo, resulta ser el más significativo también.
El típico _infierno_ al que se enfrenta un arquitecto o líder técnico a la hora de establecer la política de registro de eventos en su diseño es la gobernabilidad de dicho diseño, y la monitorización de su cumplimiento por parte del equipo de desarrollo, cosa que se torna excesivamente complicada por la _creatividad_ de algunos miembros del equipo que rompe la homogeneidad de los mensajes que se ha establecido como parte del modelo de eventos.

Otro típico incidente es que los desarrolladores, muchas veces culpando a las restricciones de tiempo del proyecto o a la urgencia de la solicitud en la implementación de un determinado requerimiento, omiten agregar las líneas de código que generan el registro de eventos, lo cual a veces puede resultar incluso difícil de detectar en revisiones de código (a través de prácticas como los <a href="http://en.wikipedia.org/wiki/Peer_review" target="_blank" rel="noopener">_peer reviews_</a>).

A través del enfoque de AOP, es posible esconder el mensaje del evento y reducir su implementación a colocar un atributo que decore el método que se desea _loggear_, lo cual permitirá establacer el formato del mensaje e impedir que los miembros del equipo lo modifiquen, reforzando la arquitectura y la gobernabilidad del proyecto, a la vez que se simplifica el proceso de desarrollo y de verificación del código.

#### Un Apropiado Soporte

Al crear un sistema de registro de eventos, no deberíamos partir desde cero, ya que existe un montón de excelentes productos y _frameworks_ que nos simplificarían esta tarea. Para este caso, emplearé los <a href="http://msdn.microsoft.com/en-us/library/ff648951.aspx" target="_blank" rel="noopener">Microsoft Libraries</a>, en particular el _Logging Application Block_; sin embargo el enfoque de AOP y de este _framework_ que he venido presentado permite emplear cualquier otra _librería_ como <a href="http://logging.apache.org/log4net/" target="_blank" rel="noopener">log4net</a> o <a href="http://nlog-project.org/" target="_blank" rel="noopener">NLog</a>.

#### Implementación

Es importante que si no han leido las primeras partes de esta serie de artículos, aprovechen este momento para hacerlo, sobre todo la [Parte 1](/aop/parte-1).

A partir de este momento mis explicaciones considerarán que el conocimiento y los detalles técnicos explicados en esa parte ya son conocidos.

El primer paso es crear el atributo (`Attribute`) que decorará las clases/interfaces para capturar su ejecución e inyectar el código de registro de eventos. Nuestro atributo se llamará `LogAttribute` y extiende de `InterceptableAttribute`, la clase base en el _framework_ de AOP que sirve para definir atributos de intercepción.

```csharp
/// <summary>
/// A custom attribute for logging purposes under an Aspect Oriented Programming paradigm.
/// </summary>
/// <remarks>
/// It applies only to methods.
/// </remarks>
[AttributeUsage(AttributeTargets.Method, AllowMultiple = false, Inherited = true)]
public sealed class LogAttribute : InterceptableAttribute
{
    /// <summary>
    /// A stopwatch to use then the verbority level is set to its highest value, in order to
    /// log the amount of time consumed by methods calls.
    /// </summary>
    private Stopwatch timer;

    /// <summary>
    /// The verbosity level to log.
    /// </summary>
    private VerbosityLevel verbosity;

    /// <summary>
    /// Initializes a new instance of the <see cref=&amp;quot;LogAttribute&amp;quot; /> class.
    /// </summary>
    /// <param name=&amp;quot;verbosity&amp;quot;>The verbosity level to log.</param>
    public LogAttribute(VerbosityLevel verbosity)
    {
        this.verbosity = verbosity;
        this.Processor = Activator.CreateInstance(typeof(LogProcessor)) as IProcessor;

        if (verbosity.Equals(VerbosityLevel.Full))
        {
            this.timer = new Stopwatch();
            this.timer.Reset();
        }
    }

    /// <summary>
    /// Gets the verbosity level to log.
    /// </summary>
    /// <value>The verbosity level of the log trace as defined in <see cref=&amp;quot;VerbosityLevel&amp;quot;/>.</value>
    public VerbosityLevel Verbosity { get { return this.verbosity; } }

    /// <summary>
    /// Gets the this log timer.
    /// </summary>
    /// <remarks>
    /// If the <c>Verbosity</c> is different than <see cref=&amp;quot;VerbosityLevel.Full&amp;quot;/> then this property will return <c>null</c>.
    /// </remarks>
    /// <value>
    /// An instance of a <see cref=&amp;quot;Stopwatch&amp;quot;/> to retrieve execution time when logging with <see cref=&amp;quot;VerbosityLevel.Full&amp;quot;/>.
    /// </value>
    /// <see cref=&amp;quot;Stopwatch&amp;quot;/>
    /// <see cref=&amp;quot;AOPLoggingApplicationBlock.VerbosityLevel&amp;quot;/>
    public Stopwatch Timer { get { return this.timer; } }
}
```

Este atributo tiene dos propiedades muy importantes. La primera, llamada `VerbosityLevel` permite establecer que tanta información se generará/almacenará cuando se registre eventos con cada intercepción. En principio para este ejemplo he definido cuatro niveles de verbosidad:

1. `None`: no se registrarán eventos.
2. `Light`: una mínima, pero significativa cantidad de información será generada.
3. `Medium`: una cantidad moderada de significante información será generada.
4. `Full`: mucha información será generada, no necesariamente todoa ella significativa, pero sí útil.

La segunda propiedad se llama `Timer` no es más que un <a href="http://msdn.microsoft.com/en-us/library/system.diagnostics.stopwatch(v=vs.100).aspx" target="_blank" rel="noopener">`Stopwatch`</a> y que para el caso de `VerbosityLevel.Full` nos medirá cuanto ha tardado en ejecutarse un método interceptado (con lo cual podríamos identificar cuellos de botella en tiempos de producción por ejemplo).
Una vez establecido el atributo de intercepción, procedemos a crear el `Processor` que se encargará de manejar la inyección de código antes y después de la ejecución de los métodos interceptados. Para esto crearemos la clase `LogProcessor` que implementará la interfaz `IProcessor` del _framework_.

Esta clase es la que dependiento del `VerbosityLevel` y basado en el Microsoft Enterprise Library Logging Application Block procederá a _escribir_ registros acorde a la configuración del mencionado Application Block. Los métodos `ProcessCallMessage` y `ProcessReturnMessage` se encargarán de crear el mensaje del evento de una manera estandard y pre-establecida (evitando que los desarrolladores _decidan_ el mensaje y rompan con la gobernabilidad).

Lamentablemente la implementación de la clase `LogProcessor` es un tanto extensa como para ponerla en esta publicación, estando disponible para descargarse (y estudiarse) justo <a href="https://github.com/rliberoff/CODERTECTURA-Blog-AOPFramework" target="_blank" rel="noopener">aquí</a>.
