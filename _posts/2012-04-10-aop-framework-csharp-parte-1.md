---
title: "Framework de Programación Orientada a Aspectos (AOP) en C# - Parte 1: Implementación"
excerpt: "***Legacy*** - Cómo implementé un *framework* para Programación Ortiendata a Aspectos (AOP) en C#."
date: 2012-04-10 00:00:00 +0200
last_modified_at: 2023-10-27 00:00:00 +0200
layout: post
permalink: /posts/aop-parte-1
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
Este es la segunda parte de una serie de cuatro publicaciones que he realizando sobre programación orientada a aspectos en .NET empleando el lenguaje de programación C#.

- [Parte 0: Introducción](/posts/aop-parte-0)
- [Parte 2: Un aspecto para el registro de eventos (_logging_)](/posts/aop-parte-2)
- [Parte 3: Un aspecto para el manejo de excepciones](/posts/aop-parte-3)
{% endcapture %}

<div class="notice--info" style="font-size: medium;">
  {{ notice-text | markdownify }}
</div>

Hace un tiempo, trabajando con <a href="http://es.linkedin.com/in/daherrera" target="_blank" rel="noopener">Diego Herrera</a> (<a href="http://twitter.com/vermicida" target="_blank" rel="noopener">@vermicida</a>) decidimos indagar un poco dentro del mundo del AOP y crear un _framework_ que de forma universal permitiera a cualquier desarrollo en .NET crear pequeñas librerías que sirvieran para satisfacer una funcionalidad contextual como por ejemplo el registro de eventos (_logging_), la gestión de excepciones (_exception handling_), mecanismos de seguridad (como autenticación continua con cada invocación a métodos) o monitoreo de desempeño del sistema (_performance monitoring_). Esta es la primera parte de un tutorial para crear nuestro propio _framework_ para AOP.

Nuestra principal necesidad al crear este _framework_ era que los desarrolladores tuviesen las herramientas necesarias para aplicar las diferentes funcionalidades (_aspects_) transversales (_cross cutting_) de manera eficiente, sin resultar una carga que relentizara el tiempo de implementación pero que a la ves, desde un punto de gobernabilidad del proceso de desarrollo, no fueran capaces de omitir la colocación de dicha funcionalidad, es decir, evitar por ejemplo el típico caso de _"como son muchas cosas se me pasó escribir el código que loggea eventos"_, ó _"es que no sabía que colocar"_.

El mecanismo elegido es el uso de atributos de no más de dos (2) parámetros como máximo y de aplicación sobre métodos, de forma tal que los desarrolladores sólo tengan que colocar el atributo correspondiente al aspecto que se desea aplicar en los métodos en los que sea requerido, siendo la configuración del aspecto establecida por parámetros. Estos parámetros tendrán un valor por defecto lo suficientemente significativo para el aspecto para cubrir aquellos casos en los que los desarrolladores los omitan. Un ejemplo de un programa que emplearía este _framework_ sería el siguiente:

```csharp
...
    public class TestObject : InterceptableObject
    {
        [Log(VerbosityLevel.None)]
        public void MethodA() { }

        [Log(VerbosityLevel.Light)]
        public void MethodB(string str) { }

        [Log(VerbosityLevel.Medium)]
        public string MethodC(string name)
        {
            return String.Format("Hola {0}", name);
        }
        ...
    }
...
```

En el código anterior, el atributo `Log` es un aspecto desarrollado empleando este _framework_.

Al final del día lo que buscábamos era un mecanismo eficiente, simple, sencillo, y que ofreciera al equipo de desarrollo la posibilidad de agregar las funcionalidades transversales, evitando desvíos en la gobernabilidad de las desiciones y conceptos de diseño de la arquitectura (como el formato de los mensajes de excepción por ejemplo).

#### Implementación

La siguiente imagen corresponde al diagrama de clases de este _framework_ y cuyos elementos iremos describiendo y detallando a lo largo de esta publicación:

<figure class="align-center">
  <a href="{{ '/images/2012-04-10-aop-framework-csharp-parte-1/aop_diagrama_clases.png' | absolute_url }}" target="_blank" rel="noopener">
    <img src="{{ '/images/2012-04-10-aop-framework-csharp-parte-1/aop_diagrama_clases.png' | absolute_url }}" alt="Diagrama de Clases" class="image-border">
  </a>
  <figcaption>Haz click para ver la imagen más grande.</figcaption>
</figure>

Recordando de la parte cero de esta serie de publicaciones, en .NET para que una clase sea interceptable debe cumplir con dos (2) condiciones:

1. Debe extender de la clase <a href="http://msdn.microsoft.com/en-us/library/system.contextboundobject.aspx" target="_blank" rel="noopener">`ContextBoundObject`</a>
2. Debe estar decorada con un <a href="http://msdn.microsoft.com/en-us/library/system.attribute.aspx" target="_blank" rel="noopener">atributo</a> que extienda de <a href="http://msdn.microsoft.com/en-us/library/system.runtime.remoting.contexts.contextattribute.aspx" target="_blank" rel="noopener">`ContextAttribute`</a>

Un objeto que extiende de `ContextBoundObject` es como el <a href="http://es.wikipedia.org/wiki/Buda_Gautama" target="_blank" rel="noopener">Buda</a>, adquiere conciencia de sí mismo, de su relación con el universo (el CLR) y con los demás. Esto es muy útil porque podemos de alguna manera saber cuando se va a ejecutar un método dentro del objeto y cuando dicho método a finalizado su ejecución, que es justamente lo que se busca hacer en AOP para interceptar e intervenir la ejecución de los métodos e inyectar la funcionalidad del aspecto que se quiere introducir.

Sin embargo, un `ContextBoundObject` por sí sólo es incapaz de procesar la inyección en sí de código para los aspectos, sólo es capaz de decir cuando un método es invocado o retorna de su invocación; de ahí que se tenga que decorar con un `ContextAttribute`, que agregará a la meta-data de la clase toda la información y mecanismos necesarios para interactuar con su contexto, lo que en el caso de este _framework_ permitirá redirigir la ejecución a las porciones de funcionalidad de los aspectos a inyectar.

Pero en una arquitectura de N-capas con todo un dominio de clases susceptibles de ser interceptadas, podemos encontrarnos con que es realmente incómodo, poco escalable y flexible el tener que hacer que (todas) las clases de la arquitectura que requieran intercepción extiendan de `ContextBoundObject`, y que estén decoradas con el atributo `ContextAttribute`. Puede pasar que a algún desarrollador se le olvide extender de `ContextBoundObject` o aplicar el atributo `ContextAttribute`, y una de las intenciones de este _framework_ es evitar que estas situaciones pasen.

Lo ideal es que las clases de la arquitectura extiendan de una única clase padre, que sea la que esté decorada con el atributo `ContextAttribute` y que extienda de `ContextBoundObject`, y que llamaremos `InterceptableObject`:

```csharp
using System;
using System.Security.Permissions;

namespace AOPFramework
{
    /// <summary>;
    /// Represents a context-bound object whose execution must be intercepted.
    /// </summary>;
    [InterceptContextAttribute]
    public abstract class InterceptableObject : ContextBoundObject
    {
        /// <summary>
        /// Class constructor.
        /// </summary>
        protected InterceptableObject() : base() { }

        /// <summary>
        /// Obtains a lifetime service object to control the lifetime policy for this instance.
        /// </summary>
        /// <returns>Returns <c>null</c> since a lifetime service is not defined for interceptable objects.</returns>
        [SecurityPermission(SecurityAction.LinkDemand, Flags = SecurityPermissionFlag.Infrastructure)]
        public override object InitializeLifetimeService()
        {
            return null;
        }
    }
}
```

Hemos definido esta clase como abstracta para impedir que pueda ser instanciada, obligando a todas las clases de la arquitectura consumidora de este _framework_ a tener que extender de ella y de esta forma generar una familia de clases que podría ser identificadas de forma unívoca como _"interceptables"_.

Igualmente puede apreciarse que la clase `InterceptableObject` está decorada con un attributo de tipo `InterceptContextAttribute`, que no es más que una especificación de la clase `ContextAttribute`:

```csharp
using System;
using System.Runtime.Remoting.Activation;
using System.Runtime.Remoting.Contexts;
using System.Security.Permissions;

namespace AOPFramework
{
    /// <summary>
    /// Defines an attribute that will decorate those classes that can be intercepted in order to process its behaviour, represented by
    /// the invokation of its methods.
    /// </summary>
    /// <remarks>
    /// Class extends from <c>ContextAttribute</c>, which provides the default implementations of the <c>IContextAttribute</c> and <c>IContextProperty</c> interfaces.
    /// </remarks>
    [AttributeUsage(AttributeTargets.Class, Inherited = true)]
    internal sealed class InterceptContextAttribute : ContextAttribute
    {
        /// <summary>
        /// Class constructor.
        /// </summary>
        public InterceptContextAttribute() : base(Guid.NewGuid().ToString()) { }

        /// <summary>
        /// Called when the context is frozen.
        /// </summary>
        /// <param name="newContext">The context to freeze.</param>
        [SecurityPermission(SecurityAction.LinkDemand, Flags = SecurityPermissionFlag.Infrastructure)]
        public override void Freeze(Context newContext) { }

        /// <summary>
        /// Adds the current context property to the given message.
        /// </summary>
        /// <param name="ctorMsg">The <c>IConstructionCallMessage</c> to which to add the context property.</param>
        [SecurityPermission(SecurityAction.LinkDemand, Flags = SecurityPermissionFlag.Infrastructure)]
        public override void GetPropertiesForNewContext(IConstructionCallMessage ctorMsg)
        {
            if (ctorMsg != null)
            {
                ctorMsg.ContextProperties.Add(new InterceptProperty(this.Name));
            }
        }

        /// <summary>
        /// Returns a Boolean value indicating whether the context parameter meets the context attribute's requirements.
        /// </summary>
        /// <param name="ctx">The context in which to check.</param>
        /// <param name="ctorMsg">The <c>IConstructionCallMessage</c> to which to add the context property.</param>
        /// <returns>
        /// This method will return <c>true</c> if the passed in context is okay; otherwise, it will return <c>false</c>.
        /// </returns>
        [SecurityPermission(SecurityAction.LinkDemand, Flags = SecurityPermissionFlag.Infrastructure)]
        public override bool IsContextOK(Context ctx, IConstructionCallMessage ctorMsg)
        {
            return (ctx != null) &amp;amp;&amp;amp; (ctx.GetProperty(this.Name) as InterceptProperty) != null;
        }

        /// <summary>
        /// Returns a Boolean value indicating whether the context property is compatible with the new context.
        /// </summary>
        /// <param name="newCtx">The new context in which the property has been created.</param>
        /// <returns>
        /// This method will return <c>true</c> if the context property is okay with the new context; otherwise, it will return <c>false</c>.
        /// </returns>
        [SecurityPermission(SecurityAction.LinkDemand, Flags = SecurityPermissionFlag.Infrastructure)]
        public override bool IsNewContextOK(Context newCtx)
        {
            return (newCtx != null) &amp;amp;&amp;amp; (newCtx.GetProperty(this.Name) as InterceptProperty) != null;
        }
    }
}
```

Como la idea es crear un _framework_, y parte de ello significa esconder la mayor cantidad de complejidad a futuros consumidores, la clase `InterceptContextAttribute` se implementa como `internal` para que **no** pueda ser referenciada fuera del <a href="http://msdn.microsoft.com/en-us/library/hk5f40ct(v=vs.100).aspx" target="_blank" rel="noopener">`assembly`</a> del _framework_ y sea empleada únicamente por la clase `InterceptableObject`.

Nuevamente recordando de la parte cero de esta serie de publicaciones, en .NET cuando se trabaja con clases de contexto, existe el concepto de sumidero (o _sink_): clases responsables de gestionar los mensajes que genera la clase, determinando la apropiada y correspondiente inyección de aspectos. La clase `InterceptProperty`, que es referenciada en la anterior `InterceptContextAttribute`, es responsable de comunicar al contexto el tipo (`Type`) correspondiente al sumidero que gestionará los mensajes que se generen.

```csharp
using System;
using System.Runtime.Remoting.Contexts;
using System.Runtime.Remoting.Messaging;

namespace AOPFramework
{
    /// <summary>
    /// This class implements the necessary methods to represent a property that can be intercepted and provide information as well as
    /// data to the context sink.
    /// </summary>
    internal class InterceptProperty : IContextProperty, IContributeClientContextSink, IContributeServerContextSink
    {
        /// <summary>
        /// Class constructor.
        /// </summary>
        public InterceptProperty(string name) : base() { this.Name = name; }

        /// <summary>
        /// Gets the name of the property under which it will be added to the context.
        /// </summary>
        public string Name { get; set; }

        /// <summary>
        /// Called when the context is frozen.
        /// </summary>
        /// <param name="newContext">The context to freeze.</param>
        public void Freeze(Context newContext) { }

        /// <summary>
        /// Returns a Boolean value indicating whether the context property is compatible with the new context.
        /// </summary>
        /// <param name="newCtx">The new context in which the ContextProperty has been created.</param>
        /// <returns>
        /// <c>True</c> if the context property can coexist with the other context properties in the given context; otherwise, <c>false</c>.
        /// </returns>
        public bool IsNewContextOK(Context newCtx)
        {
            return (newCtx != null) &amp;amp;&amp;amp; (newCtx.GetProperty(this.Name) as InterceptProperty) != null;
        }

        /// <summary>
        /// Chains the message sink of the provided server object in front of the given sink chain.
        /// </summary>
        /// <param name="nextSink">The chain of sinks composed so far.</param>
        /// <returns>The composite sink chain.</returns>
        public IMessageSink GetClientContextSink(IMessageSink nextSink)
        {
            return new InterceptSink(nextSink);
        }

        /// <summary>
        /// Chains the message sink of the provided server object in front of the given sink chain.
        /// </summary>
        /// <param name="nextSink">The chain of sinks composed so far.</param>
        /// <returns>The composite sink chain.</returns>
        public IMessageSink GetServerContextSink(IMessageSink nextSink)
        {
            return new InterceptSink(nextSink);
        }
    }
}
```

Nótese que la clase implementa tres (3) interfaces:

- <a href="http://msdn.microsoft.com/en-us/library/system.runtime.remoting.contexts.icontextproperty.aspx" target="_blank" rel="noopener">`IContextProperty`</a>: encargada de obtener el nombre y las características del contexto de ejecución.
- <a href="http://msdn.microsoft.com/en-us/library/system.runtime.remoting.contexts.icontributeclientcontextsink.aspx" target="_blank" rel="noopener">`IContributeClientContextSink`</a>: encargada de interceptar todos los mensajes que salgan del contexto.
- <a href="http://msdn.microsoft.com/en-us/library/system.runtime.remoting.contexts.icontributeservercontextsink.aspx" target="_blank" rel="noopener">`IContributeServerContextSink`</a>: encargada de interceptar todos los mensajes que entren al contexto.

Ahora viene la parte complicada en el diseño del _framework_. Independientemente de si el mensaje entra o sale del contexto, la clase `InterceptProperty` retornará una instancia de la clase `InterceptSink`, que será el único sumidero que interese para procesar los mensajes. Es decir, que todos los mensajes serán procesados por el mismo sumidero independientemente del momento de su intercepción.

Estos mensajes son producidos por la invocación o retorno de los métodos de las clases que extiendan de `InterceptableObject`, los cuales se espera estén decorados con atributos que extienden de la clase `InterceptableAttribute`, y que permite emplear este _framework_ para crear atributos _custom_ (tal y como se mostró en la primera porción de código al inicio de esta publicación) que servirán para indicar en el código fuente la inyección de un aspecto.

```csharp
using System;

namespace AOPFramework
{
    /// <summary>
    /// Defines or decorates a class as interceptable. An interceptable class can be processed by a class that implements the <c>IProcessor</c> interface.
    /// </summary>
    [AttributeUsage(AttributeTargets.Method, AllowMultiple = false, Inherited = true)]
    public abstract class InterceptableAttribute : Attribute
    {
        /// <summary>
        /// Sets or gets the processor for this class.
        /// </summary>
        public IProcessor Processor { get; set; }

        /// <summary>
        /// Sets or gets this attribute processing priority.
        /// </summary>
        /// <remarks>
        /// The bigger the value of this property, the bigger the importance or priority of processing
        /// this attribute.
        /// </remarks>
        public int Priority { get; set; }
    }
}
```

El atributo `InterceptableAttribute` permite agregar dos propiedades a la meta-data de los métodos que se decoren con él: una instancia de la interface `IProcess` y un valor entero que define la prioridad de atención al aspecto que se modele con este atributo.

#### Un Tema de Prioridad

El argumento detrás de una propiedad para definir una prioridad es que en .NET al recuperar los atributos (por _reflection_ por ejemplo), estos aparecen en el órden inverso a como fueron colocados en el código. Esto significa que los programadores estarían restringidos a colocar los atributos que definen aspectos en el órden preciso que se necesita para su inyección, lo cual primero no es flexible y segundo puede llevar a escenarios que rompan con la gobernabilidad que haya decidido el Arquitecto de Software o el Líder Técnico para la inyección de los aspectos.

<figure class="align-center">
  <a href="{{ '/images/2012-04-10-aop-framework-csharp-parte-1/aop_propiedad_prioridad.png' | absolute_url }}" target="_blank" rel="noopener">
    <img src="{{ '/images/2012-04-10-aop-framework-csharp-parte-1/aop_propiedad_prioridad.png' | absolute_url }}" class="image-border">
  </a>
  <figcaption>Haz click para ver la imagen más grande.</figcaption>
</figure>

Definiendo una prioridad para un aspecto como parte de sus propiedades y ordenando luego los aspectos que se deben aplicar a un método acorde a dicha prioridad se otorga a los programadores la libertad de agregar los atributos que los definen en el orden que deseen. Más aún, si durante la vida de un proyecto se crean o descartan aspectos, sólo bastará con agregar o remover el atributo correspondiente sin tomar en cuenta si esta de primero o último en la pila de atributos (ganando flexibilidad y escalabilidad en el diseño e implementación).

#### Un Tema de Procesamiento

La otra propiedad que agrega a la meta-data de los métodos decorados con el atributo `InterceptableAttribute` es la posibilidad de obtener una instancia de la inteface `IProcess` que definirá el contrato que debe seguir los aspectos que se programen con este _framework_:

```csharp
using System;
using System.Runtime.Remoting.Messaging;

namespace AOPFramework
{
    /// <summary>
    /// Defines the interface for those objects that will process the calling and return messages for a class that extends
    /// from <c>InterceptableObject</c>.
    /// </summary>
    /// <seealso cref="AOPFramework.InterceptableObject"/>
    public interface IProcessor
    {
        /// <summary>
        /// Process a <c>Method Call Message</c>.
        /// </summary>
        /// <remarks>
        /// This method will be called before the execution of the body of an interceptable or processable object.
        /// </remarks>
        /// <param name="callMessage">The <c>Method Call Message</c> to process.</param>
        /// <param name="processable">The processable decorated object to process.</param>
        [System.Diagnostics.CodeAnalysis.SuppressMessage("Microsoft.Naming", "CA1704:IdentifiersShouldBeSpelledCorrectly", MessageId = "processable", Justification = "According to Merriam-Webster dictionary, the word 'Processable' exists and is correctly spelled (http://www.merriam-webster.com/dictionary/processable).")]
        void ProcessCallMessage(IMethodCallMessage callMessage, InterceptableAttribute processable);

        /// <summary>
        /// Process a <c>Method Return Message</c>.
        /// </summary>
        /// <remarks>
        /// This method will be called after the execution of the body of an interceptable or processable object. The <c>returnMessage</c> parameter will
        /// contain the result of the execution, including any possible exception type.
        /// </remarks>
        /// <param name="returnMessage">The <c>Method Return Message</c> to process.</param>
        /// <param name="processable">The processable decorated object to process.</param>
        [System.Diagnostics.CodeAnalysis.SuppressMessage("Microsoft.Naming", "CA1704:IdentifiersShouldBeSpelledCorrectly", MessageId = "processable", Justification = "According to Merriam-Webster dictionary, the word 'Processable' exists and is correctly spelled (http://www.merriam-webster.com/dictionary/processable).")]
        void ProcessReturnMessage(IMethodReturnMessage returnMessage, InterceptableAttribute processable);
    }
}
```

Esta interface define dos métodos:

- `ProcessCallMessage`: Establece el método que debe atender el pre-procesamiento o acciones a realizar antes de ejecutar el método interceptado. Básicamente es el que sería invocado en el momento en que un `ContextAttribute` procede a ejecutar (llamar) a uno de sus métodos, inyectando aspectos cuya ejecución se realizará previa a la ejecución de dicho método.
- `ProcessReturnMessage`: Establece el método que debe atender el post-procesamiento o acciones a realizar después de haber ejecutado el método que está siendo interceptado; es decir, inyecta aspectos cuya ejecución se realizará posterior a la ejecución de dicho método.

#### Retomando el Sumidero

Como se explicó previamente, la clase `InterceptProperty` retornará una instancia de la clase `InterceptSink`, que en este _framework_ es el único sumidero necesario para atender los mensajes entrantes y salientes.

```csharp
using System;
using System.Runtime.Remoting.Messaging;

namespace AOPFramework
{
    /// <summary>
    /// Represents an intercept sink.
    /// </summary>
    internal class InterceptSink : IMessageSink
    {
        /// <summary>
        /// Stores the next message sink in the sink chain.
        /// </summary>
        private IMessageSink nextSink;

        /// <summary>
        /// A generic instance of an object to lock on, rather than locking on the type itself, to avoid deadlocks.
        /// </summary>
        /// <remarks>
        /// The initialization of this variable uses the <i>static initialization</i> approach, where the instance is created
        /// the first time any member of the class is referenced. The common language runtime (CLR) takes care of the variable
        /// initialization.
        /// </remarks>
        private static object syncRoot = new Object();

        /// <summary>
        /// Class constructor.
        /// </summary>
        /// <param name="nextSink">The next message sink in the sink chain.</param>
        public InterceptSink(IMessageSink nextSink)
        {
            lock (syncRoot)
            {
                this.nextSink = nextSink;
            }
        }

        /// <summary>
        /// Gets the next message sink in the sink chain.
        /// </summary>
        public IMessageSink NextSink
        {
            get { return this.nextSink; }
        }

        /// <summary>
        /// Asynchronously processes the given message.
        /// </summary>
        /// <param name="msg">The message to process.</param>
        /// <param name="replySink">The reply sink for the reply message.</param>
        /// <returns>
        /// Returns an <c>IMessageCtrl</c> interface that provides a way to control asynchronous messages after they have been dispatched.
        /// </returns>
        public IMessageCtrl AsyncProcessMessage(IMessage msg, IMessageSink replySink)
        {
            return nextSink.AsyncProcessMessage(msg, replySink);
        }

        /// <summary>
        /// Synchronously processes the given message.
        /// </summary>
        /// <param name="msg">The message to process.</param>
        /// <returns>A reply message in response to the request.</returns>
        public IMessage SyncProcessMessage(IMessage msg)
        {
            IMethodCallMessage callMessage = (msg as IMethodCallMessage);

            if (callMessage != null)
            {
                InterceptableAttribute[] processables = (InterceptableAttribute[])(msg as IMethodMessage).MethodBase.GetCustomAttributes(typeof(InterceptableAttribute), true);

                // Sort 'aspects' (attributes) based on the value of the 'priority' property.
                Array.Sort<InterceptableAttribute>(processables, new Comparison<InterceptableAttribute>(delegate(InterceptableAttribute a, InterceptableAttribute b) { return a.Priority.CompareTo(b.Priority); }));

                // Do pre-processing: process the method call before its body execution. The calling parameters are going to be available.
                for (int i = 0; i < processables.Length; i++)
                {
                    processables[i].Processor.ProcessCallMessage(callMessage, processables[i]);
                }

                // Do post-processing: process the method call after its body execution. The return values (or exception) are going to be available.
                IMethodReturnMessage returnMessage = (nextSink.SyncProcessMessage(callMessage) as IMethodReturnMessage);

                if (returnMessage != null)
                {
                    for (int i = 0; i < processables.Length; i++)
                    {
                        processables[i].Processor.ProcessReturnMessage(returnMessage, processables[i]);
                    }

                    return returnMessage;
                }
            }

            return msg;
        }
    }
}
```

El método `SyncProcessMessage` es el principal responsable en esta clase, y se encarga de ejecutar las siguientes acciones con cada instancia de `IMessage` que procesa:

1. Se verifica que el mensaje es un mensaje de llamada (_call_) a un método. Es decir, que el mensaje es una instancia de la interface <a href="http://msdn.microsoft.com/en-us/library/system.runtime.remoting.messaging.imethodcallmessage.aspx" target="_blank" rel="noopener">`IMethodCallMessage`</a>.
2. Se recuperan todos los atributos del mensaje que sean del tipo `InterceptableAttribute`.
3. Se ordenan los atributos acorde a su propiedad de prioridad.
4. Se obtiene la instancia de la clase procesadora del aspecto (de tipo `IProcessor`) y se invoca al método `ProcessCallMessage` para inyectar cualquier funcionalidad que defina el aspecto y que deba ejecutarse previo a la ejecución del cuerpo del método que está siendo interceptado.
5. Se procede a continuar con la cadena (_chain_) conceptual de funcionalidades; verificando que los mensajes que se reciben sean de salida (_return_) de un método. Es decir, que el mensaje es una instancia de la interface <a href="http://msdn.microsoft.com/en-us/library/system.runtime.remoting.messaging.imethodreturnmessage.aspx" target="_blank" rel="noopener">`IMethodReturnMessage`</a>.
6. Nuevamente se obtiene la instancia de la clase procesadora del aspecto, y se invoca al método `ProcessReturnMessage` para inyectar cualquier funcionalidad que defina el aspecto y que deba ejecutarse posteriormente a la ejecución del cuerpo del método que está siendo interceptado.
7. Se retorna el mensaje para continuar con la cadena conceptual.

#### Finalizando

La siguiente imagen corresponde al diagrama de dependencias de clases de este _framework_ y que muestra la relación de los elementos descritos y detallados en esta publicación:

<figure class="align-center">
  <a href="{{ '/images/2012-04-10-aop-framework-csharp-parte-1/aop_diagrama_dependencias.png' | absolute_url }}" target="_blank" rel="noopener">
    <img src="{{ '/images/2012-04-10-aop-framework-csharp-parte-1/aop_diagrama_dependencias.png' | absolute_url }}" alt="Diagrama de Dependencias" class="image-border">
  </a>
  <figcaption>Haz click para ver la imagen más grande.</figcaption>
</figure>

Para emplear este _framework_ y crear aspectos se deben seguir los siguientes pasos:

1. Crear un atributo para definir el aspecto (como el atributo `Log` del ejemplo al principio de esta publicación) simplemente extendiendo la clase `InterceptableAttribute`. A esta implementación se le pueden agregar tantas propiedades como sean necesarias para definir la meta-data y funcionalidades del aspecto.
2. Implementar la interface `IProcessor` y sus dos métodos (si así se requiere) para inyectar la funcionalidad del aspecto en los métodos interceptados.

En próximas publicaciones mostraré ejemplos de como emplear este _framework_ para crear aspectos y consumirlos dentro de un diseño.

#### Limitaciones

Emplear y diseñar arquitecturas de software empleando el paradigma de AOP no es ni una panacea ni una utopía en .NET; lamentablemente, existe un precio a pagar en tiempo de ejecución y de memoria entre otras limitaciones que debemos tener en cuenta:

- **Desempeño**: Empleando diferentes herramientas de medición de desempeño, he encontrado que en el peor caso puede haber un incremento de tiempo de ejecución en cada llamada (invocación a método interceptado) de cerca de 0,05 microsegundos. Esto quiere decir que se necesita cerca de unas 20000 llamadas para perder un segundo, lo cual se podría considerar no tan grave. Sin embargo, en aplicativos donde el tiempo y el desempeño sea primordial... quizás el enfoque de AOP no sea el más apropiado.
- **Memoria**: El uso de contextos propios, así como de _sinks_ y en general cualquier objeto que extienda de la clase `ContextBoundObjects` consume más memoria que objetos "normales". Hoy día el recurso de memoria no suele ser considerado como un recurso costoso o valioso, pero siempre es importante tenerlo en cuenta.
- **Capacidades**: Lamentablemente por diseño y arquitectura del CLR es, a través de esta aproximación e implementación de AOP, absolutamente imposible interceptar métodos o elementos estáticos (`static`) del código. Esto impone una importante limitación a la hora de diseñar arquitecturas de software, porque significa que o bien descartamos el uso de elementos estáticos, o bien asumimos que su criticidad y necesidad de ser interceptados puede ser ignorada de forma segura, o que su operatividad y la inyección de aspectos puede inferirse y extrapolarse desde sus miembros llamadores no estáticos.

#### Código Fuente

Por último, <a href="https://github.com/rliberoff/CODERTECTURA-Blog-AOPFramework" target="_blank" rel="noopener">aquí</a> esta una copia del código fuente completo descrito en esta publicación.

#### Referencias

- <a href="http://blogs.msdn.com/b/tilovell/archive/2011/02/07/contextboundobject-part-1-making-contexts.aspx" target="_blank" rel="noopener">ContextBoundObject – Part #1 – Making Contexts</a>.
- <a href="http://blogs.msdn.com/b/tilovell/archive/2011/02/10/contextboundobject-2-contexts-and-interception.aspx" target="_blank" rel="noopener">ContextBoundObject – #2 – Contexts and Interception</a>.
- <a href="http://www.codeproject.com/Articles/8436/Intercepting-method-calls-in-C-an-approach-to-AOSD" target="_blank" rel="noopener">Intercepting method calls in C#, an approach to AOSD</a> [2 Oct 2004].
- <a href="http://msdn.microsoft.com/en-us/magazine/cc164165.aspx" target="_blank" rel="noopener">Decouple Components by Injecting Custom Services into Your Object's Interception Chain</a> por Juval Lowy.
- <a href="http://www.codeproject.com/Articles/8414/The-simplest-AOP-scenario-in-C" target="_blank" rel="noopener">The simplest AOP scenario in C#</a> [29 Sep 2004].
- <a href="http://www.codeproject.com/Articles/11385/Aspect-Oriented-Programming-in-NET" target="_blank" rel="noopener">Aspect Oriented Programming in .NET</a> [22 Ago 2005].
- <a href="http://www.codeproject.com/Articles/14334/AOP-using-System-Reflection-Emit-Code-Injection-IL" target="_blank" rel="noopener">AOP using System.Reflection.Emit - Code Injection IL</a> [2 Jun 2006].
