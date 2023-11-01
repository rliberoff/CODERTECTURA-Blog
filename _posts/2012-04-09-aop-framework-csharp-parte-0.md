---
title: "Framework de Programación Orientada a Aspectos (AOP) en C# - Parte 0: Introducción"
excerpt: "***Legacy*** - Introducción a cómo implementé un *framework* para Programación Ortiendata a Aspectos (AOP) en C#."
date: 2012-04-09 00:00:00 +0200
last_modified_at: 2023-10-27 00:00:00 +0200
layout: post
permalink: /posts/aop-parte-0
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
Este es el primero de una serie de cuatro publicaciones que he realizando sobre programación orientada a aspectos en .NET empleando el lenguaje de programación C#.

Mi intención inicial era que la primera parte incluyese una apropiada introducción teórica a la programación orientada a aspectos, adicional a los detalles propios de diseño e implementación de un framework. Sin embargo, la longitud que estaba adquiriendo esta primera publicación me ha obligado a dividirla en dos partes: una parte cero o introductoria con los conceptos y elementos teóricos, y una futura parte uno con el correspondiente detalle técnico de implementación.

- [Parte 1: Implementación](/posts/aop-parte-1)
- [Parte 2: Un aspecto para el registro de eventos (_logging_)](/posts/aop-parte-2)
- [Parte 3: Un aspecto para el manejo de excepciones](/posts/aop-parte-3)
{% endcapture %}

<div class="notice--info" style="font-size: medium;">
  {{ notice-text | markdownify }}
</div>

Acorde a la Wikipedia la programación orientada a aspectos, o AOP por sus siglas en inglés, es un paradigma de programación cuya intención es permitir una adecuada modularización de las aplicaciones y posibilitar una mejor separación de incumbencias; encapsulando de forma efectiva los diferentes conceptos que componen una aplicación en entidades bien definidas, eliminando las dependencias entre cada uno de ellas. Esta es la parte introductoria a un tutorial para crear nuestro propio _framework_ para AOP.

El principal objetivo de AOP es la separación de las funcionalidades dentro del sistema:

- Por un lado funcionalidades comunes utilizadas a lo largo de la aplicación.
- Por otro lado, las funcionalidades propias de cada módulo.

Cada funcionalidad común se encapsulará en una entidad.

#### Origen y Razón de Ser

La idea de la programación orientada a aspectos surge directamente del paradigma de la <a href="http://es.wikipedia.org/wiki/Programaci%C3%B3n_orientada_a_objetos" target="_blank">programación orientada a objectos</a> (o OOP por sus sigas en inglés), en la cual muchas veces al estar implementando funcionalidades de un aplicativo de tamaño considerable empiezan a aparecer retos y problemas que no son solventables a través de las formas o técnicas habituales. Algunos de estos problemas son:

- _Scattered Code_: o código disperso, no es más que líneas de código que están distribuidas por toda o gran parte del aplicativo, y que incrementan de forma considerable la dificultad de las tareas de mantenimiento y desarrollo.

- _Tangled Code_: o código enmarañado, es un problema que puede aparecer cuando una misma pieza de código (como un módulo) implementa múltiples comportamientos o aspectos diferentes del sistema de forma simultánea, empleando cláusulas de tipo `switch` ó `if-then-else` anidadas.

- _Loss Uniformity_: o pérdida de uniformidad, es más un problema de forma y gobernabilidad del desarrollo, que de diseño o implementación. Se basa en que aún cuando el arquitecto de software o el líder técnico haya sentado de manera formal los estándares y convenios de implementación en temas como nomenclatura o mensajes, estos se pierden a lo largo del ciclo de vida del desarrollo del aplicativo. El caso más común son los mensajes de la aplicación para casos como por ejemplo registro de evetos o excepciones, donde por más que exista un lineamiento formal, cada desarrollador puede acabar escribiendo el mensaje acorde a su mejor sentido común. Este fenómeno se encuentra mucho en equipos de desarrollo de alta rotación, en proyectos de duración muy prolongada (superior a dos años) o que son mantenidos por equipos de desarrollo diferentes.
  
Al final del día, la razón de ser de una AOP es buscar minimizar (o solventar) el desorden que puede aparecer en la arquitectura de un aplicativo desarrollado mediante OOP. Este desorden aparece cuando algo que el sistema tiene que hacer requiere la participación de muchos y variados objetos diferentes, lo cual suele ocurrir por la abstracción de los requerimientos en objetos que realiza el diseñador, quien a menudo pierde de vista el hecho de que en última instancia, dichos objetos van interactuar unos con otros con el fin de cumplir con tales requerimientos.

Lo anterior ocurre con facilidad y de forma subconscientemente, porque la forma fundamental en que interactúan los requerimientos es muchas veces diferente de la forma en que interactúan los objetos.

Los conceptos descritos en los patrones de diseño son un intento de entender formalmente los temas de la interacción de objetos y para proporcionar al diseñador de algunos medios bien comprendidos para resolver este problema de interdependencia. Más aún, la mayoría de las implementaciones de un AOP se apoyan fuertemente en el <a href="http://es.wikipedia.org/wiki/Observer_(patr%C3%B3n_de_dise%C3%B1o)" target="_blank">patrón de diseño observador</a> (u _Observer_ en inglés).

Así, podemos decir a modo de resumen que AOP surge como un paradigma de programación dentro del mismo paradigma de OOP, que no busca sustituir a éste, sino más bien mitigar algunas de sus limitaciones al modularizar todo aquel código de índole transversal en un sistema de software.

Por supuesto que AOP no es la panacea o un hito utópico en la implantación de arquitecturas y en el desarrollo de aplicativos en OOP, y es que _**siempre**_ se necesitará de la participación de equipos ágiles de desarrollo, con credenciales, entrenamiento y formación apropiada, experiencia adecuada y un liderazgo eficaz para llevar con éxito un proyecto de desarrollo de software, con o sin el seguimiento de una AOP.

#### Terminología

Los siguientes son los conceptos que se suelen manejarse en una AOP (según han sido tomados desde la Wikipedia):

- **Aspect** (_Aspecto_): es una funcionalidad transversal (_cross-cutting_) que se va a implementar de forma modular y separada del resto del sistema, y que en una OOP tradicional, es el causante habitual de código repetido, disperso o enmarañado. El ejemplo más común y simple de un aspecto es el registro de eventos (_event logging_) dentro del sistema, ya que necesariamente afecta a todas las partes que generan un suceso.

- **Join Point** (_Punto de Cruce_ o _de Unión_): es un punto de ejecución dentro del sistema donde un aspecto puede ser introducido, como la invocación o retorno de un método, la ocurrencia de una excepción o la modificación de un campo. El código del aspecto será inyectado en el flujo de ejecución de la aplicación para añadir su funcionalidad.

- **Advice** (_Consejo_) es la implementación del aspecto, es decir, contiene el código que implementa la nueva funcionalidad. Se insertan en la aplicación en los Puntos de Cruce.

- **Pointcut** (_Puntos de Corte_): define los Consejos que se aplicarán a cada Punto de Cruce. Se especifica mediante Expresiones Regulares o mediante patrones de nombres (de clases, métodos o campos), e incluso dinámicamente en tiempo de ejecución según el valor de ciertos parámetros.

- **Introduction** (_Introducción_): permite añadir métodos o atributos a clases ya existentes. Un ejemplo en el que resultaría útil es la creación de un Consejo de Auditoría que mantenga la fecha de la última modificación de un objeto, mediante una variable y un método apropiado a la tarea, que podrían ser introducidos en todas las clases (o sólo en algunas) para proporcionarles esta nueva funcionalidad. Este concepto también es conocido como inyección de código, o _injection_ por su término en inglés.

- **Target** (_Destinatario_): es la clase aconsejada, la clase que es objeto de un consejo. Sin AOP, esta clase debería contener su lógica, además de la lógica del aspecto.

- **Proxy** (_Resultante_): es el objeto creado después de aplicar el Consejo al Objeto Destinatario. El resto de la aplicación únicamente tendrá que soportar al Objeto Destinatario (pre-AOP) y no al Objeto Resultante (post-AOP).

- **Weaving** (_Tejido_): es el proceso de aplicar Aspectos a los Objetos Destinatarios para crear los nuevos Objetos Resultantes en los especificados Puntos de Cruce. Este proceso puede ocurrir a lo largo del ciclo de vida del Objeto Destinatario y del desarrollo del aplicativo:
  - Aspectos en Tiempo de Compilación, que necesita un compilador especial.
  - Aspectos en Tiempo de Carga, los Aspectos se implementan cuando el Objeto Destinatario es cargado a memoria. Requiere un `ClassLoader` especial.
  - Aspectos en Tiempo de Ejecución.

<br>

#### Contextos en .NET

Cuando entramos en el mundo de .NET y de AOP es necesario explicar un concepto adicional: el de Contextos. En .NET, un contexto es un conjunto de propiedades o reglas de uso que definen un entorno en el que una colección de objetos reside. Las reglas se aplican cuando los objetos entran o salen de un contexto.

Los contextos se crean durante la activación de un objeto. Un nuevo objeto se coloca en un contexto existente o en un nuevo contexto creado con los atributos incluidos en la metadata del tipo que corresponde al objeto activado.

Desde el punto de vista del CLR (_Common Lenguage Runtime_), un contexto no es más que una de las muchas subdivisiones que puede llegar a tener un <a href="http://msdn.microsoft.com/en-us/library/cxk374d9.aspx" target="_blank">_app domain_</a>. Más aún, cuando un _app domain_ es creado, tiene un contexto por defecto (que justamente se llama _default context_).

Un contexto funciona básicamente a través de mensajes (objetos que implementan la interfaz <a href="http://msdn.microsoft.com/en-us/library/system.runtime.remoting.messaging.imessage.aspx" target="_blank">`IMessage`</a>), que se definen como un conjunto de propiedades tales como el nombre del método que se está invocando, sus parámetros (tanto de entrada como de salida) así como cualquier otra característica propia que defina a la invocación. Estos mensajes son recibidos por sumideros (o _sinks_ en inglés, y que son objetos que implementan la interfaz <a href="http://msdn.microsoft.com/en-us/library/system.runtime.remoting.messaging.imessagesink.aspx" target="_blank">`IMessageSink`</a>) y encargadas de procesar los mensajes para ejecutar acciones a través de los datos que estos portan.

La idea de contexto es fundamental para desarrollar una AOP en .NET empleado el lenguage C#, ya que es gracias a las clases que permiten decorar objectos como objetos de contexto (tal como <a href="http://msdn.microsoft.com/en-us/library/system.contextboundobject.aspx" target="_blank">`ContextBoundObject`</a>) que se podrá intervenir en la ejecución de la lógica de éstos para inyectar la funcionalidad de los aspectos que se implementen a través de los mensajes.

Cuando se ejecuta un sistema desde la óptica de la clase `ContextBoundObject` ocurre lo siguiente:

1. La invocación a un método se convierte en una instancia de `IMessage`.
2. El mensaje pasa a través de una serie de sumideros (objetos del tipo `IMessageSink`), que son enlazados para formar una cadena (_chain_) conceptual.
3. Cada sumidero es capaz de analizar el mensaje y sus características, ejecutando una lógica específica.
4. De ser necesario, un sumidero puede modificar el mensaje.
5. Cuando un sumidero finaliza de procesar el mensaje, lo pasa al siguiente sumidero en la cadena conceptual.
6. Eventualmente la cadena es totalmente ejecutada y el método invocado se ejecuta.
7. Si el método retorna algún valor (o genera una excepción) la cadena de sumideros se ejecuta nuevamente en sentido revertido.

#### Un Framework para .NET

Si realizamos una búsqueda en Internet sobre _frameworks_ en .NET para realizar AOP, encontramos muchos productos que ofrecen toda una gama de posibilidades para inyectar contextos dentro del código durante el tiempo de diseño/codificación del sistema, durante su compilación o después de ésta directamente en el MSIL.

Entonces… ¿por qué crear un _framework_ para AOP habiendo tantos productos disponibles?

Pues porque como Arquitecto de Soluciones de Software encuentro siempre reconfortante el poder crear mis propios _frameworks_ sobre los cuales puedo tener un control más fino y delicado, y en los que puedo poner toda mi confianza en que estoy entregando a clientes y compañeros de trabajo productos de calidad que pueden utilizar y extender fácilmente.

Por otra parte, simplemente ocurre que no me convencen los productos que hay actualmente para hacer AOP; no porque sean malos... sino simplemente porque no siguen una aproximación con la que me sienta cómodo, sobre todo porque estos productos suelen ser muy mastodónticos y complejos. De ahí esta iniciativa de crear un _framework_ lo suficientemente minimalista como para ser confortable de emplear y extender, universal para que cada aspecto pueda implementarse independientemente con el apoyo de la tecnología que el desarrollador encuentre más apropiada a sus gustos y necesidades (que en mi caso suele ser apoyarme en los <a target="_blank" href="http://msdn.microsoft.com/en-us/library/ff648951.aspx">Microsoft Enterprise Libraries</a>).

En la próxima parte de esta serie de publicaciones mostraré los detalles técnicos de diseño e implementación de este _custom framework_.

#### Referencias

- <a href="http://es.wikipedia.org/wiki/Programaci%C3%B3n_orientada_a_aspectos" target="_blank">Wikipedia: Programación orientada a aspectos</a>
- <a href="http://www.codeproject.com/Articles/4039/Aspect-Oriented-Programming-Aspect-Oriented-Softwa" target="_blank">Aspect Oriented Programming & Software Design</a>
