---
slug: apis-monetizacion-parte-3
title: "Cómo monetizar nuestras APIs de Inteligencia Artificial con Azure API Management - Parte 3: Delegación en el APIM"
excerpt: "En esta serie de tres publicaciones, voy a ir mostrando los detalles técnicos que impartí en la pasada Global Azure Spain 2023 en Madrid sobre monetización de APIs empleando el Azure API Management en una arquitectura totalmente «Cloud Native», y que será de muchísima utilidad para capitalizar nuestras APIs, sobre todo las de Inteligencia Artificial."
date: 2023-05-31 00:00:00 +0000
lastmod: 2023-10-29 00:00:00 +0000
url: "/posts/apis-monetizacion-parte-3/"
image:
 path: /images/2023-05-31-moneitzar-apis-inteligencia-artificial-parte-3/header.webp
 thumbnail: /images/2023-05-31-moneitzar-apis-inteligencia-artificial-parte-3/thumbnail.webp
categories:
 - Tutorial
 - Azure
 - C#
 - API
 - APIM
 - Azure API Management
 - Inteligencia Artificial
---

{{< republished blog="Piensa en software, desarrolla en colores" url="https://blogs.encamina.com/piensa-en-software-desarrolla-en-colores/como-monetizar-nuestras-apis-de-inteligencia-artificial-con-el-azure-api-management-3a-parte/" >}}

{{< notice type="success" >}}
Este es la primera parte de una serie de trest publicaciones:

- [Parte 1: Introducción](/posts/apis-monetizacion-parte-1)
- [Parte 2: Implementación](/posts/apis-monetizacion-parte-2)
{{< /notice >}}

El Azure API Management ofrece la capacidad de delegación, la cual permite que un sitio web externo gestione la información de los usuarios, en lugar de utilizar las funciones integradas del Developers Portal. En este artículo, nos centraremos específicamente en la delegación de la gestión de suscripciones a productos en Azure Api Management.

### Configurando del Azure API Management

El Azure API Management (APIM) proporciona una capacidad llamada «Delegación», la cual sólo está disponible en los planes "Developer", "Basic", "Standard" y "Premium" del  recurso.

Gracias a esta capacidad, el APIM permite que un sitio web externo se apropie de los datos de los usuarios desde el Developers Portal y realice una validación personalizada. Con la  delegación, por ahora, se pueden controlar aspectos tales como el registro e inicio de  sesión de usuarios en el Developers Portal, y la gestión de subscripciones a productos, en lugar de que se emplee la funcionalidad integrada del propio Developers Portal.

Para esta publicación, nos interesa concretamente la delegación de la gestión de las  subscripciones a productos, la cual sigue el siguiente flujo de trabajo:

1. El usuario selecciona un producto en el Developers Portal del APIM y hace clic en el botón Suscribir.
2. El navegador se redirige al endpoint de delegación (en nuestro caso una aplicación desplegada en un Azure Container Applicationo ACA).
3. El endpoint de delegación realiza los pasos necesarios para la suscripción al producto. Estos pueden incluir lo siguiente:
   - Redirigir a otra página para solicitar información de facturación y de pago (como tarjeta de crédito).
   - Hacer preguntas adicionales.
   - Almacenar la información adicional relevante para la facturación.

La delegación de servicios del APIM se puede realizar fácilmente desde el Azure Portal como se muestra en la siguiente imagen:

{{< figure src="/images/2023-05-31-moneitzar-apis-inteligencia-artificial-parte-3/1.png" class="align-center" caption="Haz click para ver la imagen más grande." >}}
{{< /figure >}}

Es fundamental saber que no existe una "Delegation Validation Key" hasta tanto no le  demos al botón de generar y salvemos los cambios. Una vez hecho eso, guardar en un lugar seguro el valor del "Delegation Validation Key" ya que lo necesitaremos más adelante (aunque perfectamente podemos volver a esta pantalla para recuperarlo o generar uno nuevo).

### Recibiendo la delegación de subscripciones <br> desde el Azure API Management

La delegación de capacidades desde el Azure API Management (APIM) requiere la implementación de una aplicación web, no de una API (REST) como podríamos pensar. Es fundamental que la aplicación proporcione las pantallas necesarias para que los usuarios puedan suministrar la información que necesitemos como relevante para nuestra gestión de sus subscripciones. Para este ejemplo, y la integración con Stripe, sólo necesitamos que el usuario nos suministre el nombre de la subscripción.

Esta aplicación web la podemos programar con el lenguaje de programación que mejor se adapte a nuestra forma de trabajar, y que se puede desplegar en cualquier tipo de recursos que consideremos apropiado.

Para esta demo, he querido crear una arquitectura totalmente «Cloud Native», por lo cual elegí desarrollar la aplicación web como una imagen Docker que perfectamente podríamos desplegar en un Azure Web Application for Docker, un Azure Container Instance o un Azure Kubernetes Service; sin embargo, he elegido la opción más de moda en cuanto a rendimiento, costo y capacidades que son las Azure Container Applications (ACA).

Como leguaje de programación he elegido C# con .NET 6 porque es mi favorito, aunque todo lo implementado es perfectamente realizable con otros lenguajes.

En el ejemplo he decidido usar ASP.NET MVC con Razor como tecnología de implementación.

Recordemos que Azure, y más aún nuestra aplicación, no estarán certificadas en <a href="https://www.pcisecuritystandards.org/" target="_blank" rel="noopener noreferrer">PCI-DSS</a>, razón por la cual tenemos que redirigir a las pantallas de Stripe (fuera del contexto de nuestra aplicación y de Azure) para obtener esta información. Otra alternativa es incrustar las pantallas de Stripe en un `<iframe>` pero muchas veces encuentro eso más laborioso e innecesario.

Como nuestra aplicación se va a integrar con Stripe, primero es necesario tener una referencia a su API a través de una librería que nos permite usarla con C#. Para ello nos basta con usar el paquete NuGet que nos proporciona la misma gente de Stripe aquí: <a href="https://www.nuget.org/packages/Stripe.net/" target="_blank" rel="noopener noreferrer">https://www.nuget.org/packages/Stripe.net/</a>.

Luego, necesitamos configurar algunos parámetros que conservaremos en el `appsettings.json` de nuestra aplicación y que recuperaremos con una clase de opciones como la siguiente:

{{< figure src="/images/2023-05-31-moneitzar-apis-inteligencia-artificial-parte-3/2.png" class="align-center" caption="Haz click para ver la imagen más grande." imageBorder="false" >}}
{{< /figure >}}

Necesitaremos:

- Una nueva «Restricted Keys» que podemos crear desde el portal del desarrollador de Stripe, que podemos llamar «App Key» y con permisos otorgados para leer precios y productos, y para poder leer y escribir subscripciones, registros de uso y sesiones de pago (*checkout*).
- El valor de la «Publishable key» que ya nos da Stripe como parte de sus «Standard keys».
- El secreto del *webhook*, ya sea porque lo conservamos de la ejecución del *script* de configuración de Stripe, o porque lo recuperamos desde el portal del desarrollador.

Para trabajar con el APIM desde código C#, lo más conveniente es usar el paquete NuGet que nos proporciona Microsoft aquí: <a href="https://www.nuget.org/packages/Azure.ResourceManager.ApiManagement" target="_blank" rel="noopener noreferrer">https://www.nuget.org/packages/Azure.ResourceManager.ApiManagement</a>.

Para poder usar las librerías de este paquete necesitamos ciertos valores a obtener de nuestra instancia del APIM a conservar en el `appsettings.json` de nuestra aplicación y que recuperaremos con una clase de opciones como la siguiente:

{{< figure src="/images/2023-05-31-moneitzar-apis-inteligencia-artificial-parte-3/3.png" class="align-center" caption="Haz click para ver la imagen más grande." imageBorder="false" >}}
{{< /figure >}}

Necesitaremos:

- El valor del «Delegation Validation Key» generado al configurar la delegación de capacidades del APIM en el Azure Portal.
- La URL al Developers Portal.

{{< figure src="/images/2023-05-31-moneitzar-apis-inteligencia-artificial-parte-3/4.png" class="align-center" caption="Haz click para ver la imagen más grande." >}}
{{< /figure >}}

- La URL para la gestión del APIM, que se puede obtener como se muestra en la siguiente imagen. También es importante encenderla.

{{< figure src="/images/2023-05-31-moneitzar-apis-inteligencia-artificial-parte-3/5.png" class="align-center" caption="Haz click para ver la imagen más grande." >}}
{{< /figure >}}

- Por último, necesitamos el nombre de la instancia del APIM, el nombre del grupo de recursos donde la hemos desplegado y el identificador de la subscripción de Azure a la que pertenece dicho grupo de recursos.

Con este paquete agregado a nuestro proyecto de aplicación web, y los valores de integración ya configurados, sólo necesitamos registrarlos en nuestro `Program.cs` de la siguiente forma:

{{< figure src="/images/2023-05-31-moneitzar-apis-inteligencia-artificial-parte-3/6.png" class="align-center" caption="Haz click para ver la imagen más grande." imageBorder="false" >}}
{{< /figure >}}

Cada vez que el APIM envíe una delegación de operaciones, lo hará a una ruta que hayamos definido al configurar la delegación, y siempre acompañada de un parámetro (por query string) llamado `operation` que identifica la operación que el usuario quiere realizar.

Lo recomendable aquí es que tengamos un solo controlador para recibir las peticiones desde el APIM que se encargue de extraer el valor del parámetro `operation` para enrutar al siguiente controlador que se encargará de efectivamente ejecutar la lógica de la operación.

En el código de ejemplo encontrarás dentro del directorio `Pages` la página `Index.cshtml` que contiene la lógica de enrutamiento de las peticiones que llegan desde el APIM.

En concreto nos interesan dos operaciones:

- ***Subscribe*** → recibida cuando se está creando una nueva subscripción a productos desde el Developers Portal.
- ***Unsubscribe*** → recibida cuando se cancela una subscripción activa desde el Developers Portal.

Ahora procedemos a crear una interfaz que defina las operaciones que realizaremos desde código con C# sobre el Azure API Management usando el paquete NuGet importado anteriormente.

{{< figure src="/images/2023-05-31-moneitzar-apis-inteligencia-artificial-parte-3/7.png" class="align-center" caption="Haz click para ver la imagen más grande." imageBorder="false" >}}
{{< /figure >}}

Cada una de estas operaciones están implementadas en la clase `ApiService`, la cual usamos como un Singleton que registramos en nuestro contenedor de dependencias en el `Program.cs`.

El constructor de la clase `ApiService` se encarga de crear una instancia de la clase ArmClient (que obtenemos del paquete NuGet) la cual a su vez necesita de las credenciales de Azure para operar correctamente.

{{< figure src="/images/2023-05-31-moneitzar-apis-inteligencia-artificial-parte-3/8.png" class="align-center" caption="Haz click para ver la imagen más grande." imageBorder="false" >}}
{{< /figure >}}

La clase `ArmClient` es como un cliente agnóstico del tipo de servicio o recurso de Azure que vamos a gestionar. Para identificar el recurso del APIM necesitamos ciertos parámetros que hemos configurado en el appsettings.json y que obtenemos de la clase de opciones ApimServiceOptions, que son el identificador de la subscripción de Azure, el nombre del grupo de recursos y el nombre del servicio, los cuales usaremos para crear un identificador del recurso APIM gracias al método `CreateResourceIdentifier` de la clase `ApiManagementServiceResource` la cual representa un APIM junto con las operaciones de instancia que se pueden realizar el mismo.

{{< figure src="/images/2023-05-31-moneitzar-apis-inteligencia-artificial-parte-3/9.png" class="align-center" caption="Haz click para ver la imagen más grande." imageBorder="false" >}}
{{< /figure >}}

En el código anterior se obtiene una instancia de `ApiManagementServiceResource`, que sirve para gestionar aspectos tales como las subscripciones. Sin embargo, existen muchas más como `ApiManagementProductResource` que sirve para gestionar productos (por ejemplo, obtenerlos a partir de su identificador), `ApiManagementUserResource` que sirve para gestionar los usuarios creados desde el Developer Portal, entre otros.

Cada método de la interface `IApimService` hará uso de la instancia del `ArmClient` creada en el constructor de `ApimService` así como del identificador de creado por `ApiManagementUserResource` para obtener una instancia del servicio que se necesite para cada operatividad.

La interface (y su implementación) definen las siguientes operaciones:

- `CancelSubscriptionAsync` → Se encarga de cancelar una subscripción, ya sea porque el usuario lo especifica de esta forma desde el Developer Portal, o porque es cancelada administrativamente desde el portal de Stripe.
- `CreateSubscriptionAsync` → Se encarga de crear la subscripción dentro del APIM una vez que Stripe nos reporte que se ha validado y registrado correctamente el pago.
- `GetProductAsync` → Obtiene información de un producto desde el APIM empleado para propósitos de subscripción.
- `SuspendSubscriptionAsync` → Suspende una subscripción, habitualmente por motivos de impago. A diferencia de una cancelación, si se paga la deuda, la subscripción se reactivaría.
- `ValidateRequest` → La explico a continuación.

Un de los primeros métodos a implementar es el `ValidateRequest`, ya que cada vez que el APIM llama a una aplicación externa en la delegación de servicios, es fundamental verificar la validez de la llamada. Esta validación se hace empleando el algoritmo de HMAC para verificación de firmas con una encriptación `SHA-512`.

Así, la implementación del método `ValidateRequest` sería la siguiente:

{{< figure src="/images/2023-05-31-moneitzar-apis-inteligencia-artificial-parte-3/10.png" class="align-center" caption="Haz click para ver la imagen más grande." imageBorder="false" >}}
{{< /figure >}}

La clase `HMACSHA512` la proporciona .NET 6 en `System.Security.Cryptography`.

Como puedes ver, se emplea desde la configuración el valor de la opción `DelegationValidationKey`, que es utilizada para verificar que efectivamente la petición llega desde el APIM y que un potencial atacante no ha manipulado la petición. Esto importante porque para bien o para mal todas las peticiones del APIM hacia la aplicación sobre la que delega operaciones envía los parámetros por URL (en forma de query strings) con lo cual son "*capturables*" por un potencial atacante.

Dependiendo de cada operación que envíe desde el APIM a la aplicación externa de delegación de servicios, se debe validar un conjunto específico de parámetros, los cuales podemos consultar en la documentación oficial de Microsoft aquí: <a href="https://learn.microsoft.com/es-es/azure/api-management/api-management-howto-setup-delegation#create-your-delegation-endpoint-1" target="_blank" rel="noopener noreferrer">https://learn.microsoft.com/es-es/azure/api-management/api-management-howto-setup-delegation#create-your-delegation-endpoint-1</a>.

En el caso de nuestro código tenemos las siguientes implementaciones:

{{< figure src="/images/2023-05-31-moneitzar-apis-inteligencia-artificial-parte-3/11.png" class="align-center" caption="Haz click para ver la imagen más grande." imageBorder="false" >}}
{{< /figure >}}

Para cada situación de delegación necesitaremos controladores y pantallas concretas para atenderlas.

Cubrir todo el código que las implementa en una publicación como esta puede ser algo extenso (casi un libro 🤓), con lo cual os indicaré para qué es cada controlador y pantalla en la aplicación web y os invito a que os clonéis el repo para revisarla y adaptarla a vuestras necesidades.

- `Index` → Como os comentaba es el controlador que recibe las peticiones desde el APIM y las enruta al controlador o pantalla más conveniente para atenderla.

- `Unsubscribe` → Se encarga de cancelar una subscripción en el APIM y en Stripe.

- `Subscribe` → Se encarga de capturar la información para la subscripción de parte del usuario. En nuestro caso, sólo nos interesa el nombre de la subscripción. Al final de procesamiento, nos redirige el procesamiento a StripeCheckout.

- `StripeCheckout` → Se encarga de configurar el cliente JavaScript de Stripe para realizar la redirección a la pantalla que capturará la información de la tarjeta de crédito. Recordemos que como ni Azure ni el APIM están certificadas en certificadas en <a href="https://www.pcisecuritystandards.org/" target="_blank" rel="noopener noreferrer">PCI-DSS</a>, la pantalla que se muestra para obtener esta información del cliente está en la infraestructura y contexto de ejecución de Stripe, por lo cual Stripe debe eventualmente conocer a donde redirigir si todo ha salido bien. Para ello, la pantalla de `StripeCheckout` primero hace un POST a su Controller inicializar una sesión de pago con Stripe. El identificador de esa sesión es lo que se usará en el código del cliente para renderizar la pantalla de Stripe en el navegador, fuera de Azure y nuestra web app, y dentro e Stripe. Uno de esos datos es la dirección donde se está ejecutando nuestra aplicación, la cual tenemos que capturar desde el navegador pues nuestro aplicativo está en Docker y de hacerlo en el lado servidor nos retornaría siempre `localhost`.

{{< figure src="/images/2023-05-31-moneitzar-apis-inteligencia-artificial-parte-3/12.png" class="align-center" caption="Haz click para ver la imagen más grande." imageBorder="false" >}}
{{< /figure >}}

Al recibir el POST, una de las primeras cosas que se hacen es construir las URLs para escenarios de cancelación y éxito del pago (ver líneas 12 a 32 en la siguiente imagen), las cuales necesitan una URL de retorno que se obtiene del lado cliente como se muestra en la imagen anterior, en la línea morada dentro del recuadro verde.

{{< figure src="/images/2023-05-31-moneitzar-apis-inteligencia-artificial-parte-3/13.png" class="align-center" caption="Haz click para ver la imagen más grande." imageBorder="false" >}}
{{< /figure >}}

Con esta información (líneas 36 a 75) se crea una sesión de Stripe.

Nótese como en las líneas 55 a 73 se especifica el precio a pagar, así como las cantidades. El precio es obtenido desde Stripe empleado una instancia de su clase `PriceService` e identificando el producto con el identificador de producto del APIM. Esto es posible porque cuando inicializamos Stripe con el script de PowerShell tomamos en cuenta la configuración de productos del APIM, de la cual, entre otras cosas, se toma el identificador del producto para emplearlo tal cual como identificador en Stripe.

Creada la sesión de Stripe, basta con retornar su identificador como resultado del POST para que el código del lado del cliente en su navegador (cuadro naranja dos imágenes más arriba) haga la redirección.

- `PaymentCancelled` → Notifica al usuario que ha habido algún fallo con el pago desde Stripe y le da la oportunidad de reintentar.

- `PaymentSucceeded` → Notifica al usuario que todo ha salido bien con el pago, y que su subscripción estará pronto disponible, redirigiéndole al Developers Portal.

Ahora bien, una vez que Stripe ha procesado el pago necesita comunicar al APIM que todo ha ido bien para que se realizan las acciones necesarias para que la subscripción esté disponible para el usuario y sea visible en el Developer Portal.

Esta integración con Stripe requiere de un webhook, al cual Stripe enviará notificaciones sobre cambios en las subscripciones.

En concreto nos interesan tres eventos:

- Subscripción creada representada por el evento `CUSTOMER.SUBSCRIPTION.CREATED`, es enviado por Stripe una vez la
información del pago se ha validado y registrado correctamente para que el APIM pueda crear la subscripción.

- Subscripción actualizada representada por el evento `CUSTOMER.SUBSCRIPTION.UPDATED` es enviada por Stripe cuando algo pasa con la subscripción, por ejemplo, que no se ha podido pagar y que por lo tanto debería ser suspendida.

- Subscripción cancelada representada por ele vento `CUSTOMER.SUBSCRIPTION.DELETED` es enviada por Stripe si la subscripción es borrada desde el propio portal de Stripe para que sea cancelada en el APIM.

El *webhook* está implementado por un `Controller` llamado `StripeWebhook`, y utiliza los métodos de la interface `IApimService` para atender a cada evento como según corresponda.

En caso de fallo de comunicación, Stripe se encargará de constantemente llamar al *webhook* para asegurar que las acciones necesarias se lleven a cabo. Por su parte, el *webhook* puede notificaría a Stripe que todo está en orden simplemente retornando un valor *booleano* a `true`.

### Reportando consumo desde Azure API Management<br>a Stripe para su facturación

Cuando los usuarios realizan llamadas a las APIs de cada Producto dentro del Azure API Management (APIM) deben hacer uso de una clave de subscripción que les identifica. Gracias a esta clave, una base de datos interna del APIM registra las llamadas (tanto totales, como segregadas por exitosas o fallidas) para que puedan ser reportadas en un informe que se puede utilizar para calcular cuánto cobrar a dichos usuarios.

En esta demo usaremos una Azure Function para obtener esta información, procesarla y enviarla a Stripe.

La Azure Function se debe ejecutar periódicamente. Para la demo tengo puesto que se ejecute cada minuto, pero esto es un overkill en toda regla. Lo suyo sería que se ejecute cada 24 horas dentro de una ventana de tiempo que se considere "apropiada".

A la hora de recuperar información, hay que decidir que plataforma (el APIM o Stripe)  consideramos como el maestro de los datos. En mi caso, para la demo he considerado que Stripe lleva la voz cantante en cuanto al estado de las subscripciones, razón por la cual comienza la ejecución de la Azure Function recuperando las subscripciones activas desde Stripe. No obstante, otra alternativa es obtener las subscripciones activas desde el APIM y luego consultar Stripe. Elegí este enfoque porque es el que realiza menos llamadas.

{{< figure src="/images/2023-05-31-moneitzar-apis-inteligencia-artificial-parte-3/14.png" class="align-center" caption="Haz click para ver la imagen más grande." imageBorder="false" >}}
{{< /figure >}}

Una vez que tenemos las subscripciones activas desde Stripe, iteramos sobre éstas hasta que ya no queden subscripciones por procesar.

Por cada subscripción, se obtiene el identificador de esta en el APIM (el cual es  almacenado como metadata en Stripe al crear la subscripción). También se obtiene de la metadata un valor identificado como `last-usage-update` el cual es utilizado para calcular que no existan espacios de tiempo entre los usos habidos de un API y sus usos reportados, tal que no se pierda datos de facturación. Esto lo hago entre las líneas 26 y 39 de la  siguiente imagen, aunque la mayoría de las veces es un código que rara vez se ejecuta; no  obstante, es importante entender que el "tema del dinero" es delicado y que tenemos que  considerar las casuísticas límite (o borde) para asegurar que no se pierde facturación.

{{< figure src="/images/2023-05-31-moneitzar-apis-inteligencia-artificial-parte-3/15.png" class="align-center" caption="Haz click para ver la imagen más grande." imageBorder="false" >}}
{{< /figure >}}

Nótese que en la línea 30 estamos obteniendo el reporte de uso de la subscripción en un  período específico. El método `GetUsageReportAsync` está implementado de forma  privada dentro de la función de la siguiente manera:

{{< figure src="/images/2023-05-31-moneitzar-apis-inteligencia-artificial-parte-3/16.png" class="align-center" caption="Haz click para ver la imagen más grande." imageBorder="false" >}}
{{< /figure >}}

Los filtros usados para obtener el reporte de consumo usan notación de OData.

Luego tenemos el método privado `ProcessReportAsync` que toma el reporte de uso y lo procesa de forma tal que se envía información a Stripe sobre el consumo. Su  implementación es la siguiente:

{{< figure src="/images/2023-05-31-moneitzar-apis-inteligencia-artificial-parte-3/17.png" class="align-center" caption="Haz click para ver la imagen más grande." imageBorder="false" >}}
{{< /figure >}}

El código determina si existen datos de uso en el reporte obtenido desde el APIM. De haberlos, se crea un registro de consumo con la cantidad de unidades reportadas y en una fecha específica. Luego se actualiza la subscripción en Stripe con un nuevo valor para la metadata identificada como `last-usage-update` para asegurarnos como mencionamos antes que no se pierden datos de facturación.

Y esto es todo lo que hace la Azure Function. Gracias al API de gestión del APIM y a cómo éste almacena en una base de datos interna la información sobre el uso de las APIs, podemos fácilmente informar al proveedor de pagos (en este caso Stripe) de forma periódica cuántas llamadas se han realizado para que las conserve y cobre a los usuarios cuando corresponda según el modelo de negocio configurado.

Por último, puede ser interesante destacar que en una implementación "más real" que la de esta demo, cada acción que realiza esta Azure Function esté repartida entre varias Azure Functions, conectadas entre sí mediante un mecanismo que siga el patrón de diseño «<a href="https://microservices.io/patterns/data/transactional-outbox.html" target="_blank" rel="noopener noreferrer">Transactional Outbox</a>», el cual es relativamente sencillo de implementar utilizando Cosmos DB y su funcionalidad de «<a href="https://learn.microsoft.com/en-us/azure/cosmos-db/change-feed" target="_blank" rel="noopener noreferrer">Change Feed</a>» combinada con la capacidad de «<a href="https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/transactional-batch?tabs=dotnet" target="_blank" rel="noopener noreferrer">Transactional Batches</a>», aunque eso es tema para otra conversación y otra publicación 😉

**¡Muchas gracias por leerme y espero que os sea de utilidad!**
