---
title: "Cómo monetizar nuestras APIs de Inteligencia Artificial con Azure API Management - Parte 2: Implementación"
excerpt: "En esta serie de tres publicaciones, voy a ir mostrando los detalles técnicos que impartí en la pasada Global Azure Spain 2023 en Madrid sobre monetización de APIs empleando el Azure API Management en una arquitectura totalmente «Cloud Native», y que será de muchísima utilidad para capitalizar nuestras APIs, sobre todo las de Inteligencia Artificial."
date: 2023-05-30 00:00:00 +0000
last_modified_at: 2023-10-29 00:00:00 +0000
layout: post
permalink: /posts/apis-monetizacion-parte-2
image:
  path: /images/2023-05-30-moneitzar-apis-inteligencia-artificial-parte-2/header.png
  thumbnail: /images/2023-05-30-moneitzar-apis-inteligencia-artificial-parte-2/thumbnail.png
categories:
  - Tutorial
  - Azure
  - C#
  - API
  - Inteligencia Artificial
---

{% capture notice-text %}
Artítculo publicado originalmente en el blog [«Piensa en software, desarrolla en colores»](https://blogs.encamina.com/piensa-en-software-desarrolla-en-colores/como-monetizar-nuestras-apis-de-inteligencia-artificial-con-el-azure-api-management-2a-parte/){:target="_blank"} de [ENCAMINA](https://www.encamina.com/){:target="_blank"}.
{% endcapture %}

<div class="notice--info" style="font-size: small; font-weight: bold;">
 {{ notice-text | markdownify }}
</div>

{% capture notice-text %}
Este es la primera parte de una serie de trest publicaciones:

- [Parte 1: Introducción](/posts/apis-monetizacion-parte-1)
- [Parte 3: Delegación en el APIM](/posts/apis-monetizacion-parte-3)
{% endcapture %}

<div class="notice--success" style="font-size: medium;">
  {{ notice-text | markdownify }}
</div>

La implementación de una arquitectura efectiva es fundamental para gestionar y monetizar APIs de Inteligencia Artifical de manera eficiente. En este artículo, nos centraremos en el componente central de esta arquitectura y también exploraremos la concepción del modelo de negocio y la inicialización del proveedor de pagos, utilizando Stripe ([https://stripe.com/es](https://stripe.com/es){:target="_blank"}).

### Arquitectura de la solución

El componente central de la arquitectura es el Azure API Management, un servicio extraordinario de Azure que permite la integración y transformación de APIs de origen heterogéneo en un único componente que centraliza su gestión y su gobierno. Habitualmente, el Azure API Management se abrevia como APIM.

Con el APIM podrás afrontar, entre otros, los siguientes desafíos:

- Abordar la diversidad y complejidad en las abstracciones de los *backends* (la parte que implementa la lógica de negocio de las APIs), así como la complejidad que puedan imponer los consumidores en las formas en que requieren o solicitan acceder a los APIs.

- Exponer de forma segura los servicios hospedados dentro y fuera de Azure como APIs.

- Facilitar y propiciar el descubrimiento y consumo de las APIs por parte de agentes internos y externos a la organización.

- Incrementar la protección de las APIs, acelerar significativamente su implementación y mejora, así como la "observabilidad" de su desempeño, uso y funcionamiento.

- Flexibilizar y gestionar el acceso controlado a las APIs, así como medir su consumo para acciones de monetización.

En ese sentido, la forma en alto nivel que tendrá la arquitectura que implementaremos es la siguiente:

{% include figure class="align-center" image_path="/images/2023-05-30-moneitzar-apis-inteligencia-artificial-parte-2/1.png" lightbox=true caption="Arquitectura en alto nivel para la monetización de APIs con el Azure API Management.<br>Haz click para ver la imagen más grande." %}

En esta arquitectura contaremos con los siguientes componentes:

- Un Azure API Management (APIM) con el Developers Portal.

- Un Azure Container Application (ACA) con una aplicación de Docker desarrollada en .NET 6 y programada con C# para gestionar el proceso de subscripciones a las APIs y la integración con el sistema de pagos.

- El sistema de pagos representado por Stripe.

- Una Azure Function que se encargará de reportar periódicamente los consumos de APIs de tus clientes al sistema de pagos.

- Servicios generalistas de Azure tales como un Azure Container Registry (ACR)  para mantener las imágenes de Docker a desplegar en el ACA, un Azure Storage Account para preservar archivos que necesitaremos en nuestra solución y una Azure Applications Insights integrado a un Azure Log Space para la conservación de trazas generadas por el APIM y el ACA.

### Concibiendo el modelo de negocio

Concebir un modelo de negocio nunca es una tarea sencilla. Si tu equipo trabaja bajo un  modelo de agilidad (digamos Scrum) es perfectamente normal que el concebir y establecer  el modelo de negocio para tus APIs tome fácilmente de tres a cuatro Sprints.

Tras definir el modelo de negocio es probable que las siguientes tareas sean desarrollar una aplicación para su gestión que se integre con el Azure API Management (APIM) mediante su [API REST de gestión](https://learn.microsoft.com/en-us/rest/api/apimanagement/){:target="_blank"} para crear y actualizar los elementos del modelo de negocio, siendo de los principales los Productos y las APIs vinculadas a cada uno.

Por temas de espacio de tiempo, crear tal tipo de aplicación se escapa al propósito de esta publicación, por lo cual simularemos el modelo de negocio diseñado empleando un archivo JSON que podrás encontrar en el repo de GitHub aquí 👉 [https://github.com/rliberoff/Global-Azure-Spain-2023-API-Monetization/blob/main/businessModel/monetizationModels.json](https://github.com/rliberoff/Global-Azure-Spain-2023-API-Monetization/blob/main/businessModel/monetizationModels.json){:target="_blank"}.

Como tal, el fichero se ve así (lo pongo en un GIF animado porque es muy largo):

<figure class="align-center">
    <img src="{{ '/images/2023-05-30-moneitzar-apis-inteligencia-artificial-parte-2/2.gif' | absolute_url }}" style="width: 650px;" class="image-border" >
  <figcaption>
    Extracto del JSON que representa (simula) el modelo de negocio.
  </figcaption>
</figure>

Este archivo JSON lo mantendremos y accederemos desde un contenedor de Blobs en el Azure Storage Account.

Así mismo, el equivalente en el APIM a este modelo de negocio fue creado manualmente y se ve de la siguiente forma:

{% include figure class="align-center" image_path="/images/2023-05-30-moneitzar-apis-inteligencia-artificial-parte-2/3.png" lightbox=true caption="Como se ve el modelo de negocio en el Azure API Management, en el apartado de «Productos».<br>Haz click para ver la imagen más grande." %}

### Inicializando el proveedor de pagos

Como he mencionado antes, usaremos Stripe como mecanismo de pagos, siendo las razones de mi elección las siguientes:

- Es un proveedor de pagos, con lo cual no nos hace falta implementar por nuestra cuenta los sistemas que tendrían que calcular cuánto cobrar a los consumidores periódicamente, solamente tenemos que implementar el mecanismo de reportar el consumo para que le sea cobrado a los clientes.

- Permite tener una cuenta de desarrollador completamente gratis y sin restricciones, proporcionando tarjetas de crédito para pruebas.

- Tiene un API de implementación simplemente exquisito, con ejemplos muy buenos y completos para una gran variedad de lenguajes de programación como C#, TypeScript (y JavaScript), Python, Java, y más.

- Las librerías de integración se actualizan constante y regularmente.

- Proporciona un CLI que nos permite integrar capacidades de gestión automatizadas para tares de DevOps y para integraciones necesarias durante flujos de integración y despliegue continuos.

- Permite tener una representación de nuestro modelo de negocio, con lo cual podemos definir productos que se facturen en diferentes tiempos (semanales, mensuales, trimestrales).

El único defecto que le veo a Stripe es que, de la variedad de sistemas ofrecidos en el mercado, está entre los más costosos.

Partiendo de que ya cuentas con una cuenta de desarrollador de Stripe, lo que haremos es ejecutar un *script* de PowerShell para inicializar el modelo de negocio dentro de Stripe. También la usaremos para inicializar un *webhook* que necesitaremos para la comunicación asíncrona entre Stripe y el Azure API Management.

Para poder ejecutar este script, necesitamos crear una API Key en Stripe con permisos específicos para la personalización de productos y servicios. Para ello:

1. Vamos a nuestra cuenta de Stripe y accedemos al dashboard de desarrolladores.
2. Elegimos la opción de "API Keys" del menú superior.
3. En la sección de "Restricted Keys" le damos al botón de "Create restricted key".
4. Le ponemos un nombre a la API Key que estamos creando, por ejemplo «Init Stripe».
5. En los permisos, otorgamos permisos de lectura y escritura a los aspectos de Prices, Products y Webhook Endpoints.

Una vez que tenemos este API Key, vamos a ver qué hace este *script*, el cual encontrarás completo en el repo de GitHub aquí 👉 [https://github.com/rliberoff/Global-Azure-Spain-2023-API-Monetization/blob/main/scripts/stripeInitialisation.ps1](https://github.com/rliberoff/Global-Azure-Spain-2023-API-Monetization/blob/main/scripts/stripeInitialisation.ps1){:target="_blank"}.

Lo primero es que el *script* necesita cinco parámetros:

- Un Stripe API Key que creamos anteriormente llamado «Init Stripe».
- La URL para el webhook. Esta URL debe ser la URL del Azure Applicacion Container (ACA) donde desplegaremos la aplicación de gestión de las subscripciones, seguido del valor webhook/stripe.
- La URL al archivo JSON con el modelo de monetización. Al estar desplegado en un contenedor de Blobs, podemos obtener una URL pública para acceder a este recurso directamente.
- La URL del gateway del Azure API Management (APIM).

{% include figure class="align-center" image_path="/images/2023-05-30-moneitzar-apis-inteligencia-artificial-parte-2/4.png" lightbox=true caption="Ubicación de la URL del Azure API Management Gateway.<br>Haz click para ver la imagen más grande." %}

- Una de las claves de subscripción del APIM, siendo la recomendada la que ya trae definida al provisionarse el recurso:

{% include figure class="align-center" image_path="/images/2023-05-30-moneitzar-apis-inteligencia-artificial-parte-2/5.png" lightbox=true caption="Ubicación de las claves de subscripción en el Azure API Management.<br>Haz click para ver la imagen más grande." %}

La llamada al *script* se ve de la siguiente forma:

{% include figure class="align-center" image_path="/images/2023-05-30-moneitzar-apis-inteligencia-artificial-parte-2/6.png" lightbox=true caption="Haz click para ver la imagen más grande." %}

La primera parte del *script* se encarga de instalar la versión más reciente del CLI de Stripe:

{% include figure class="align-center" image_path="/images/2023-05-30-moneitzar-apis-inteligencia-artificial-parte-2/7.png" lightbox=true caption="Primera parte del *script* de PowerShell de configuración de Stripe que se encarga de capturar los parámetros y de instalar el CLI de Stripe.<br>Haz click para ver la imagen más grande." %}

La siguiente parte del *script* hace dos cosas, por un lado, descarga el JSON con la  definición del modelo de negocio desde el contenedor de Blobs en el Azure Storage Account, y por otro se trae los productos definidos en el APIM a través del API REST de gestión.

{% include figure class="align-center" image_path="/images/2023-05-30-moneitzar-apis-inteligencia-artificial-parte-2/8.png" lightbox=true caption="Haz click para ver la imagen más grande." %}

Hago esto para poder asegurarme de que el producto que voy a crear en Stripe efectivamente existe configurado en el APIM y que concuerden los IDs de los mismos entre ambas plataformas, ya que será a través de dichos identificadores que, como veremos más adelante, se identificarán los consumos para generar la facturación y efectivamente monetizar nuestras APIs.

La siguiente parte del código es un poco más larga y os invito a leerla directamente del repo, y es la que se encarga de usar el CLI de Stripe para de forma recursiva hacer llamadas para crear los productos, sus características, sus precios y su frecuencia de facturación. Aquí es donde podríamos definir que un producto sea facturado semanal, mensual, trimestral, semestral o anualmente.

Por último, creamos el *webhook* y recuperamos su secreto para poder emplearlo como parámetro de configuración en la aplicación que desplegaremos en el Azure Container Application (ACA).

{% include figure class="align-center" image_path="/images/2023-05-30-moneitzar-apis-inteligencia-artificial-parte-2/9.png" lightbox=true caption="Haz click para ver la imagen más grande." %}

Tras ejecutar este *script*, si entramos en nuestra cuenta de Stripe veremos como los productos estarán configurados:

{% include figure class="align-center" image_path="/images/2023-05-30-moneitzar-apis-inteligencia-artificial-parte-2/10.png" lightbox=true caption="Haz click para ver la imagen más grande." %}

En la próxima publicación abordaremos la delegación de capacidades en Azure API Management, incluyendo la gestión de subscripciones y la integración con Stripe para la facturación 👉 [Parte 3](/post/apis-monetizacion-parte-3).
