---
title: "Cómo monetizar nuestras APIs de Inteligencia Artificial con Azure API Management - Parte 1: Introducción"
excerpt: "En esta serie de tres publicaciones, voy a ir mostrando los detalles técnicos que impartí en la pasada Global Azure Spain 2023 en Madrid sobre monetización de APIs empleando el Azure API Management en una arquitectura totalmente «Cloud Native», y que será de muchísima utilidad para capitalizar nuestras APIs, sobre todo las de Inteligencia Artificial."
date: 2023-05-29 00:00:00 +0000
last_modified_at: 2023-10-29 00:00:00 +0000
layout: post
permalink: /post/apis-monetizacion-parte-1
image:
    path: /images/2008-03-07-realizaciones-o-de-cuando-me-fui-de-venezuela/header.avif
    thumbnail: /images/2008-03-07-realizaciones-o-de-cuando-me-fui-de-venezuela/thumbnail.avif
categories:
    - Tutorial
    - Azure
    - C#
    - API
    - Inteligencia Artificial
---

{% capture notice-text %}
Artítculo publicado originalmente en el blog [«Piensa en software, desarrolla en colores»](https://blogs.encamina.com/piensa-en-software-desarrolla-en-colores/como-monetizar-nuestras-apis-de-inteligencia-artificial-con-el-azure-api-management-1a-parte/){:target="_blank"} de [ENCAMINA](https://www.encamina.com/){:target="_blank"}.
{% endcapture %}

<div class="notice--info" style="font-size: small; font-weight: bold;">
  {{ notice-text | markdownify }}
</div>

{% capture notice-text %}
Este es la primera parte de una serie de trest publicaciones:

- [Parte 2: Implementación](/post/apis-monetizacion-parte-2)
- [Parte 3: Delegación en el APIM](/post/apis-monetizacion-parte-3)
{% endcapture %}

<div class="notice--success" style="font-size: medium;">
  {{ notice-text | markdownify }}
</div>

Desde diciembre de 2022 estamos viendo una nueva ola de transformaciones digitales, donde cada día surgen nuevas herramientas que alegan aportar el poder de la Inteligencia Artificial a las capacidades que ofrecen.

Todas estas herramientas están soportadas por una nueva generación de APIs, las cuales muchas veces son ofrecidas más allá de las aplicaciones para las cuales fueron creadas como mecanismos de integración o productos de categoría empresarial.

Es muy probable que, si has llegado aquí, es porque tienes una idea o ya estás trabajando en un proyecto que utiliza lo último en Inteligencia Artificial, y has creado una serie de APIs que te gustaría publicar y por las cuales obtener algún tipo de rentabilidad dentro de un modelo de economía de APIs para tu negocio 😊

Así, seguramente tendrás una colección de recursos que te gustaría poner a disposición de particulares y empresas con diversos niveles de acceso para obtener beneficios sobre el uso y consumo de dichos recursos.

Como decía al principio, en los próximos artículos te mostraré los detalles técnicos que impartí en la pasada [Global Azure Spain 2023](https://globalazure.es/) en Madrid sobre ***Monetización de APIs empleando el Azure API Management*** en una arquitectura totalmente «Cloud Native» que, si estás en este mundo de las IAs, encontrarás más que adecuada para tus necesidades.

El código de esta publicación lo tienes disponible junto con la presentación (en formato PDF) en el siguiente repo de GitHub 👉 <a href=""> [https://github.com/rliberoff/Global-Azure-Spain-2023-API-Monetization](https://github.com/rliberoff/Global-Azure-Spain-2023-API-Monetization){:target="_blank"}.

A continuación, me gustaría conversar de algunos aspectos teóricos antes de entrar en la implementación, pero si estás impaciente por entender el código del repo y no tener que leer la chapa que escribo a continuación, entonces ve directamente aquí 🤓 ➡️ [Parte 2](/post/apis-monetizacion-parte-2).

### Algunos conceptos antes de empezar

Para poder entender lo que vamos a implementar, es importante conocer y entender un  par de conceptos teóricos fundamentales sobre la monetización de APIs: ***los modelos de negocio*** y ***los mecanismos de pago***.

#### Modelos de negocio para la monetización

Hoy día es más que evidente que las APIs apuntalan la economía digital, propiciando que la propiedad intelectual (IP – *Intellectual Property*) de una organización potencie el  negocio de terceros, agregando valor y generando rentabilidad. Con todo el tema de las Inteligencias Artificiales, estamos viendo que esto sigue más vigente que nunca.

Un tema común en los casos de éxito de la APIs es un modelo de negocio correcto, donde el valor se crea y se intercambia entre todas las partes, de forma sostenible.

Hay varios enfoques o modelos que una organización puede adoptar para la monetización de sus APIs, siendo principalmente los siguientes:

- Free / Gratis → Como tal no sería un modelo de negocio, ya que permite al consumidor de las APIs utilizar éstas de forma gratuita y sin compromisos.
Freemium → El término es acuñado a partir de una contracción en inglés de las palabras que definen el modelo de negocio, "free" (gratis) y "premium" (de pago). Es un modelo de negocio que funciona ofreciendo servicios básicos gratuitos, mientras se cobra por otros servicios más avanzados o especiales. También aplica a escenarios de demanda variable, donde una demanda baja (por ejemplo, las 100 primeras llamadas) son gratis, mientras que un incremento de la demanda (llamadas adicionales) genera cargos.

- Pay-as-you-use → Traducido habitualmente como "pago por uso", es un modelo de pago que cobra en función del uso de las APIs. La práctica es similar a las facturas de servicios públicos (por ejemplo, electricidad o agua), en las que sólo se cobran los recursos realmente consumidos. Es el modelo de monetización más utilizado por las plataformas de servicio en la nube, como el propio Azure. También se conoce como «Metered» ya que se cobra al medir y obtener métricas del consumo al final de un período (habitualmente mensual).

- Tier → Traducido habitualmente como "pago por plan", es un modelo de negocio donde el consumidor de las APIs paga por un número establecido de llamadas al mes (el plan). Si superan este límite, pagan un importe por uso por encima del límite por llamada adicional. Si regularmente incurren en dicho uso, pueden actualizar al siguiente nivel (otro plan).

- Unit → Parecido al anterior, y habitualmente traducido como "pago por unidad" o "pago por paquete". Es un modelo de negocio donde el consumidor de las APIs paga por una cantidad (unidad o paquete) establecida de llamadas, independientemente del tiempo. Si superan este límite, tienen que adquirir otro paquete o unidad nueva de llamadas para evitar un corte del servicio. Muchas veces para evitar dicho corte de servicio, la renovación de la unidad es automática, y es responsabilidad del cliente el indicar que desea la finalización de la subscripción.

- Flat Tier → Traducido habitualmente como "tarifa plana", es un modelo de negocio donde el consumidor paga una cantidad fija cada período de tiempo preestablecido (habitualmente mensual), independientemente del número de llamadas que realice al API.

<figure class="align-center">
    <img src="{{ '/images/2023-05-29-moneitzar-apis-inteligencia-artificial-parte-1/1.png' | absolute_url }}">
  <figcaption>Comparación de funcionamiento entre diversos modelos de negocio.</figcaption>
</figure>

En la documentación oficial de Microsoft para el Azure API Management, se cuenta con una excelente sección que describe las características organizacionales y de gestión para la monetización de APIs. Está disponible en el siguiente enlace: [https://learn.microsoft.com/es-es/azure/api-management/monetization-overview](https://learn.microsoft.com/es-es/azure/api-management/monetization-overview).

#### Soluciones de Pago

Una de las primeras decisiones y de las más críticas que debes tener que tomar para monetizar tus APIs de Inteligencia Artificial es elegir el mecanismo para recoger los pagos que realizarán tus consumidores de tus APIs. Por norma general se consideran que existen dos mecanismos:

- Plataformas de pago → Permiten a la organización calcular el pago en función de las métricas de uso de sus APIs sin procesar aplicando el modelo de negocio específico asociado a las APIs que el consumidor haya elegido. Básicamente, el cálculo de cuánto cobrar a los consumidores los realiza la plataforma en base a información (métricas y valores) que reciben sobre el consumo de forma periódica (habitualmente diaria), y realiza el cobro correspondiente al finalizar el período configurado (semanal, mensual, trimestral, etc.) en la plataforma.

- Proveedores de pago → A veces también llamadas "pasarelas de pago". Exclusivamente se encargan de facilitar la transacción del cobro. Esto quiere decir que la organización debe preocuparse y contar con los procedimientos para calcular cuánto cobrar a los consumidores de las APIs al finalizar el período de facturación considerado, el cual para este tipo de mecanismos se recomienda que sea el mismo y constante independientemente de la naturaleza del producto; por
ejemplo, mensualmente. La organización debe traducir las métricas de uso antes de llamar a la pasarela de pago. En vez de enviar métricas de uso de forma diaria, como sería con una plataforma de pago, se calcula el monto a cobrar cada mes, y se envía dicho monto al proveedor de pago para que realice el cargo correspondiente.

Si se elige un mecanismo proporcionado por una plataforma de pagos, lo conveniente es reportar diariamente el consumo de las subscripciones.

Por otro lado, si se elige un mecanismo proporcionado por una pasarela de pagos, lo conveniente es calcular el consumo de las subscripciones siempre en los mismos periodos para todos los productos (por ejemplo, mensualmente).

Es importante saber que el servicio de Azure API Management no está certificado en [PCI-DSS](https://www.pcisecuritystandards.org/), por lo cual la captura de los datos correspondientes a los medios de pago (por ejemplo, el número de una tarjeta de crédito) se debe delegar a una autoridad certificada que bien puede ser una plataforma o un proveedor de pago.

Cualquier mecanismo para recoger los pagos es perfectamente adaptable e integrable con el Azure API Management.

En la arquitectura e implementación que presento en esta publicación usaremos una plataforma de pagos llamada Stripe ([https://stripe.com/es](https://stripe.com/es)).

En el [próximo artículo](/post/apis-monetizacion-parte-2) exploraremos en detalle la arquitectura de la solución, nos centraremos en el modelo de negocio y el proveedor de pagos, y analizaremos la elección de Stripe como plataforma de pago.

¡No te lo pierdas y descubre cómo monetizar tus APIs de forma eficiente en el entorno de la nube!
