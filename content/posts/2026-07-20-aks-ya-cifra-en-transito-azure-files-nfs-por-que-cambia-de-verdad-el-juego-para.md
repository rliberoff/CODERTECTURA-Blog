---
title: 'AKS ya cifra en tránsito Azure Files NFS: por qué sí cambia el juego para
  cargas con estado'
date: '2026-07-20T09:07:53+00:00'
draft: true
slug: aks-ya-cifra-en-transito-azure-files-nfs-por-que-cambia-de-verdad-el-juego-para
description: AKS ya soporta cifrado en tránsito para Azure Files NFS. Te cuento por
  qué esta novedad cambia de verdad el diseño, la seguridad y la gobernanza de cargas
  con estado.
categories:
- Azure
- Arquitectura de Software
- Seguridad
tags:
- AKS
- Azure Files
- NFS
- Seguridad
- Kubernetes
- Compliance
image: /images/aks-ya-cifra-en-transito-azure-files-nfs-por-que-cambia-de-verdad-el-juego-para/cover.png
comments: true
ai:
  assisted: true
  model: gpt-5.4
  prompt_version: 2026-07-15.1
  generated_at: '2026-07-20T09:07:53+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://azure.microsoft.com/updates?id=567787
    title: '[Launched] Generally Available: Encryption in Transit for Azure Files
      NFS Shares in Azure Kubernetes Service (AKS)'
    published_date: '2026-07-17'
  - url: https://learn.microsoft.com/en-us/azure/sap/workloads/sap-azure-files-nfs-encryption-in-transit-guide
    title: Azure Files NFS Encryption in Transit for SAP on Azure Systems | Microsoft
      Learn
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/governance/policy/samples/built-in-policies
    title: List of built-in policy definitions - Azure Policy
    published_date: null
---

Si trabajas con Kubernetes en entornos reales, tarde o temprano dejas de hablar solo de pods, *deployments* y autoscaling. Empiezas a hablar de datos. De cómo se montan, cómo se protegen, cómo se gobiernan y, sobre todo, de qué objeciones aparecen cuando intentas pasar una arquitectura por seguridad o por compliance. Por eso esta novedad me parece bastante más importante de lo que suena en un titular: según el [anuncio de disponibilidad general en AKS](https://azure.microsoft.com/updates?id=567787), Azure Kubernetes Service ya soporta *Encryption in Transit* para volúmenes Azure Files NFS v4.1 a través del Azure File CSI driver. Traducido a lenguaje de pasillo: el tráfico entre tu carga en AKS y el recurso NFS de Azure Files ya puede viajar cifrado con TLS.

Parece un detalle incremental. Pero no lo es. **Esto no convierte mágicamente a NFS en la respuesta universal**, claro, pero sí elimina una de esas pegas incómodas que bloqueaban conversaciones enteras. Y en arquitectura, muchas decisiones no se caen por falta de funcionalidades espectaculares; se caen por un pequeño “sí, pero...”.

El matiz que me interesa aquí no es solo técnico, sino arquitectónico. Hasta ahora, cuando alguien me preguntaba por NFS en Kubernetes para datos compartidos, mi respuesta casi siempre venía con letra pequeña: “sí, puede encajar”, “sí, para ciertos patrones tiene sentido”, “sí, operativamente puede simplificar bastante”, pero el debate sobre la seguridad en tránsito seguía ahí, mirándote fijamente. En organizaciones con requisitos serios de segmentación, cumplimiento o revisión formal de riesgo, ese detalle era suficiente para frenar una adopción que por operación sí tenía lógica. Con esta capacidad en GA, AKS recorta una de las objeciones más difíciles de defender… o de sufrir, según el lado de la reunión en el que te toque sentarte.

{{< figure src="/images/aks-ya-cifra-en-transito-azure-files-nfs-por-que-cambia-de-verdad-el-juego-para/body-1.png" alt="Diagrama del flujo cifrado entre pods de AKS y Azure Files NFS" caption="El cambio importante es este: el acceso desde los workloads de AKS a Azure Files NFS ya puede viajar cifrado en tránsito." >}}{{< /figure >}}

### Lo que se ha anunciado exactamente

Microsoft ha publicado que AKS soporta de forma general el [cifrado en tránsito para Azure Files NFS v4.1](https://azure.microsoft.com/updates?id=567787) mediante el Azure File CSI driver. La base técnica, tal y como explica la guía de [Azure Files NFS Encryption in Transit](https://learn.microsoft.com/en-us/azure/sap/workloads/sap-azure-files-nfs-encryption-in-transit-guide), es que el tráfico entre cliente y servidor se protege con TLS.

A mí me gusta separar muy bien lo que esto significa y lo que no, porque aquí es muy fácil pasarse de entusiasmo. Sí significa que el canal de acceso al volumen NFS gana una protección que muchas organizaciones necesitaban para considerarlo aceptable. No significa que Azure Files NFS pase, de repente, a ser la mejor opción para cualquier carga con estado que se te ocurra. El rendimiento sigue importando. La latencia sigue importando. Los patrones de acceso siguen importando. Y el comportamiento concreto de la aplicación frente a NFS sigue importando exactamente igual que ayer por la mañana.

Lo valioso está en otro sitio: **se reduce la distancia entre lo que es viable operativamente y lo que además es aprobable** desde seguridad, compliance y gobierno de plataforma. Y esa distancia, aunque no salga en una demo, es la que decide si una tecnología entra en producción o se queda en una diapositiva muy bonita.

### Por qué importa especialmente en cargas con estado

Cuando hablo de cargas con estado en AKS, no estoy pensando solo en bases de datos. De hecho, muchas veces las bases de datos serias van por caminos bastante más especializados. Estoy pensando en aplicaciones que necesitan un sistema de archivos compartido, repositorios documentales, motores de procesamiento que escriben y leen de una ubicación común, *pipelines* que publican artefactos, aplicaciones legacy contenedorizadas o escenarios tipo SAP donde el sistema de archivos en red forma parte del contrato funcional y no de un capricho de infraestructura.

En ese tipo de casos, NFS no es un extra: es una dependencia estructural. Y si esa dependencia tenía una conversación pendiente sobre protección del canal, entonces la novedad sí cambia el panorama. La propia documentación de [Azure Files NFS con cifrado en tránsito para SAP on Azure](https://learn.microsoft.com/en-us/azure/sap/workloads/sap-azure-files-nfs-encryption-in-transit-guide) me parece una señal bastante clara de madurez, porque apunta justo a escenarios donde el requisito de seguridad no es negociable. Cuando una capacidad se documenta pensando en entornos así, yo no la leo como una *feature* cosmética. La leo como una pieza que ya entra en conversaciones serias.

A efectos prácticos, esto abre varias puertas muy concretas:

- Permite defender mejor Azure Files NFS en revisiones de arquitectura;
- Reduce fricción con equipos de seguridad que exigen cifrado del tráfico;
- Facilita mover a AKS ciertas aplicaciones compartidas por fichero que antes se quedaban en VM por pura prudencia;
- Mejora la postura de cumplimiento cuando el dato viaja entre nodo y almacenamiento.

No es poca cosa. De hecho, para algunos equipos puede ser exactamente la diferencia entre “ni lo intentes” y “vamos a evaluarlo bien”.

{{< figure src="/images/aks-ya-cifra-en-transito-azure-files-nfs-por-que-cambia-de-verdad-el-juego-para/source-2.png" alt="Pantalla del portal de Azure para montar una compartición NFS con cifrado en tránsito" caption="La configuración de montaje con cifrado en tránsito ya aparece reflejada en la experiencia de Azure Files para NFS. Fuente: [learn.microsoft.com](https://learn.microsoft.com/en-us/azure/sap/workloads/sap-azure-files-nfs-encryption-in-transit-guide)" >}}{{< /figure >}}

### Lo que cambia en el diseño de arquitectura

Aquí está el punto que a mí más me interesa. Antes, en muchos equipos, la conversación era: “¿podemos usar Azure Files NFS en AKS?”. Ahora la pregunta más sana pasa a ser: “¿**deberíamos** usarlo para este patrón concreto?”. Y ese cambio me parece buenísimo, porque te obliga a diseñar por adecuación, no por carencia de una funcionalidad básica de seguridad.

Yo lo resumiría así. Si tu aplicación necesita un sistema de archivos compartido entre varias réplicas, Azure Files NFS gana atractivo. Si tu bloqueo principal era que el tráfico entre cómputo y almacenamiento no iba cifrado, esta novedad reduce mucho esa objeción. Y si tu aplicación depende de semánticas de almacenamiento muy específicas, de IOPS muy previsibles o de latencias especialmente agresivas, entonces sigues teniendo que comparar con otras opciones. **La novedad mejora la elegibilidad; no elimina el análisis.**

También cambia, o debería cambiar, la forma de hablar de red. Que el canal vaya cifrado no es una excusa para relajar la topología ni los controles de conectividad. La propia guía de [despliegue de EiT para Azure Files NFS](https://learn.microsoft.com/en-us/azure/sap/workloads/sap-azure-files-nfs-encryption-in-transit-guide) sigue poniendo el foco en preparar correctamente la cuenta de almacenamiento, el recurso NFS y el *private endpoint*. Es decir, el mensaje sensato no es “como ya hay TLS, la red importa menos”. Más bien al contrario: **TLS completa una arquitectura de red buena; no la sustituye**.

Y esto, aunque suene muy de manual, conviene repetirlo. Porque en cuanto aparece una nueva capa de seguridad, siempre existe la tentación de usarla como coartada para simplificar donde no toca. Yo no haría eso. Ni en AKS, ni fuera de AKS, ni aunque me prometieran una tarde sin tickets.

### El impacto real en gobernanza y compliance

En muchas empresas, el problema nunca fue montar el volumen. El problema era aprobarlo. Y sospecho que aquí esta mejora puede tener más impacto en los comités y controles que en el YAML del clúster.

Cuando un equipo de seguridad revisa un diseño, suele preguntar cosas bastante razonables: cómo se protege el dato en reposo, cómo se protege en tránsito, cómo se restringe el acceso de red y cómo se mantiene una postura coherente entre entornos. Con Azure Files NFS en AKS, ahora la parte del cifrado en tránsito tiene una respuesta oficial mucho más sólida, respaldada por el [anuncio de GA en AKS](https://azure.microsoft.com/updates?id=567787).

A partir de ahí, yo intentaría no dejarlo en una simple capacidad “disponible”. Si en tu organización esto pasa a ser requisito, lo lógico es llevarlo al terreno de plataforma y de gobierno. La [lista de definiciones integradas de Azure Policy](https://learn.microsoft.com/en-us/azure/governance/policy/samples/built-in-policies) es el sitio natural para revisar qué políticas existentes te ayudan a gobernar cuentas de almacenamiento, transferencia segura y configuraciones relacionadas. No estoy afirmando aquí una *policy* exacta para este caso concreto, porque eso hay que validarlo en tu *tenant* y con la definición vigente, pero sí tengo bastante clara la idea de fondo: **no basta con poder activar EiT; hay que hacerlo consistente**.

Eso implica pensar en entornos, en excepciones, en automatización y en revisiones periódicas. Porque si producción exige una postura y preproducción va por libre, el problema no tarda en aparecer. Y cuando aparece en almacenamiento compartido, normalmente aparece mal y tarde.

{{< figure src="/images/aks-ya-cifra-en-transito-azure-files-nfs-por-que-cambia-de-verdad-el-juego-para/body-3.png" alt="Capas de gobernanza para Azure Files NFS en AKS" caption="El cifrado en tránsito tiene valor cuando forma parte de una postura completa: red, almacenamiento, clúster y policy." >}}{{< /figure >}}

### Qué miraría yo antes de adoptarlo en producción

Si me pidieras una checklist corta, práctica y sin humo, yo revisaría cinco cosas.

La primera es la compatibilidad real del *workload*. No todo lo que “monta un volumen” encaja bien sobre NFS. Hay aplicaciones que funcionan perfectas desde el minuto uno y otras que parecen ir bien hasta que aparecen bloqueos, operaciones intensivas de metadatos o patrones de concurrencia algo menos amables. Aquí no hay sustituto para probar con la aplicación real y con sus comportamientos reales.

La segunda es la topología de red. La guía de [Azure Files NFS Encryption in Transit](https://learn.microsoft.com/en-us/azure/sap/workloads/sap-azure-files-nfs-encryption-in-transit-guide) insiste en la preparación de la cuenta de almacenamiento, la compartición NFS y el *private endpoint*. Y hace bien. Si esa base está mal planteada, el cifrado en tránsito no va a arreglar una conectividad pobre ni una superficie de exposición innecesaria.

La tercera es la observabilidad. Si añado una capa nueva de seguridad en el acceso al almacenamiento, quiero saber cómo se comporta bajo carga, qué latencia introduce en mi escenario y cómo voy a detectar fallos de montaje, degradaciones o regresiones. No porque espere desastre, sino porque prefiero medir antes de opinar (a veces incluso lo consigo).

La cuarta es el gobierno entre entornos. Si activas esta postura solo en producción, estás incubando diferencias de comportamiento que luego cuestan mucho diagnosticar. En almacenamiento, esas divergencias suelen ser especialmente desagradables, porque mezclan red, sistema operativo, controladores y comportamiento de aplicación.

La quinta es el rendimiento percibido por la aplicación. La documentación para SAP habla de [seguridad empresarial sin comprometer el rendimiento](https://learn.microsoft.com/en-us/azure/sap/workloads/sap-azure-files-nfs-encryption-in-transit-guide), pero yo siempre traduzco eso a una regla muy sencilla: mídelo en tu carga, con tus patrones y en tus ventanas de operación. Lo demás son buenas intenciones.

### El detalle operativo que no conviene perder de vista

En la guía de Microsoft aparece una pieza interesante: el uso del *helper* `aznfs` en Linux para montar Azure Files NFS con cifrado en tránsito en los escenarios documentados. Por ejemplo, se muestra una instalación como esta:

```bash
curl -sSL -O https://packages.microsoft.com/config/$(source /etc/os-release && echo "$ID/${VERSION_ID%%.*}")/packages-microsoft-prod.rpm
sudo rpm -i packages-microsoft-prod.rpm
rm packages-microsoft-prod.rpm           # limpia el artefacto temporal para no dejar basura en la imagen o la VM
sudo zypper refresh
sudo zypper install aznfs                # este paquete habilita el mount helper necesario para los escenarios EiT documentados
```

No te lo enseño para que vayas a ejecutarlo tal cual en AKS, porque la novedad en AKS se apoya en el [Azure File CSI driver](https://azure.microsoft.com/updates?id=567787), no en que tú entres a mano en cada nodo a montar nada. Lo traigo por otra razón, bastante más útil: detrás de la *feature* hay una implementación concreta. Y conviene recordar que el cifrado en tránsito para NFS no es una etiqueta de marketing simpática, sino una cadena de componentes, dependencias y decisiones técnicas bastante definida.

Dicho de otra forma: cuando una capacidad de plataforma te resuelve algo, sigue mereciendo la pena entender por debajo qué está resolviendo exactamente. Sobre todo si luego te toca operarlo, securizarlo o explicarlo en una revisión.

{{< figure src="/images/aks-ya-cifra-en-transito-azure-files-nfs-por-que-cambia-de-verdad-el-juego-para/source-4.png" alt="Diagrama conceptual de almacenamiento en AKS" caption="Conviene recordar que esta mejora se inserta en una arquitectura más amplia de volúmenes persistentes, claims y drivers en AKS. Fuente: [learn.microsoft.com](https://learn.microsoft.com/en-us/azure/sap/workloads/sap-azure-files-nfs-encryption-in-transit-guide)" >}}{{< /figure >}}

### Entonces, ¿qué historia cuenta ahora AKS para almacenamiento compartido?

Yo diría que una bastante más madura. El diagrama de [conceptos de almacenamiento en AKS](https://learn.microsoft.com/en-us/azure/sap/workloads/sap-azure-files-nfs-encryption-in-transit-guide) ya sitúa bien el papel de volúmenes persistentes, *claims* y *drivers* dentro del clúster. Con la disponibilidad general de EiT para Azure Files NFS, esa historia gana una pieza que faltaba para muchas organizaciones: un canal cifrado entre los pods y el *backend* de archivos compartidos.

Eso no convierte automáticamente a Azure Files NFS en mi opción por defecto para cualquier estado. Ni debería. Pero sí hace que entre mucho más en serio en la terna cuando necesito un sistema de archivos compartido administrado, integrado con Azure y razonablemente defendible delante de seguridad. Y en la práctica, eso puede ser la diferencia entre seguir peleándote con soluciones autogestionadas o apoyarte en un servicio con una operación bastante más sensata.

### Mi conclusión

Mi lectura es bastante clara: esta novedad no significa solo “más seguridad”, sino **menos fricción arquitectónica**. Y para equipos que viven muy pegados a Kubernetes, eso es muchísimo más valioso de lo que parece. Significa que ciertas cargas con estado pueden plantearse sobre AKS con una defensa técnica bastante más limpia delante de seguridad, compliance y plataforma.

Si tu organización ya usaba Azure Files NFS pero convivía con dudas sobre el tránsito, este GA mejora la postura de forma inmediata. Si no lo usabas precisamente por ese motivo, yo reabriría la evaluación. Y si estás diseñando una plataforma interna para equipos de producto, empezaría a tratar esta capacidad como parte del *baseline* y no como una excepción más que alguien tiene que justificar en cada proyecto.

Porque al final, en infraestructura, las mejoras que cambian decisiones no suelen ser las más vistosas. Son las que consiguen borrar un “sí, pero...” del diseño. Y aquí, sinceramente, creo que AKS acaba de quitar uno bastante importante.
