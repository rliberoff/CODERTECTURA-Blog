---
title: 'Azure Web PubSub Chat en vista previa pública: menos WebSockets a mano, más
  arquitectura de chat'
date: '2026-08-24T07:09:55+00:00'
draft: true
slug: azure-web-pubsub-chat-en-vista-previa-publica-menos-websockets-a-mano-mas-arquit
description: Azure Web PubSub Chat añade APIs de salas, miembros, mensajes y roles
  sobre el servicio en tiempo real. Te cuento por qué simplifica una arquitectura
  de chat real y cómo probarlo paso a paso.
categories:
- Azure
- Arquitectura de Software
- .NET
tags:
- Azure Web PubSub
- Chat en tiempo real
- Azure Functions
- Azure Static Web Apps
- Arquitectura
image: /images/azure-web-pubsub-chat-en-vista-previa-publica-menos-websockets-a-mano-mas-arquit/cover.png
comments: true
ai:
  assisted: true
  article_type: technical
  model: gpt-5.4
  prompt_version: 2026-08-21.1
  generated_at: '2026-08-24T07:09:55+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://techcommunity.microsoft.com/t5/apps-on-azure-blog/announcing-azure-web-pubsub-chat-in-public-preview/ba-p/4548907
    title: Announcing Azure Web PubSub chat in public preview
    published_date: '2026-08-21'
  - url: https://learn.microsoft.com/en-us/dotnet/api/overview/azure/microsoft.azure.functions.worker.extensions.webpubsub-readme?view=azure-dotnet
    title: Azure Web PubSub extension of isolated-process Azure Functions client library
      for .NET - Azure for .NET Developers | Microsoft Learn
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/azure-web-pubsub/tutorial-serverless-notification
    title: Tutorial - Create a serverless notification app using Azure Web PubSub
      service and Azure Functions | Microsoft Learn
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/azure-web-pubsub/tutorial-serverless-static-web-app
    title: Integrate - Create a chat app using Azure Web PubSub and deploy to Azure
      Static Web Apps | Microsoft Learn
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/azure-web-pubsub/overview
    title: What is Azure Web PubSub service? | Microsoft Learn
    published_date: null
---

Si alguna vez has montado un chat «de verdad», ya sabes que el problema nunca fue abrir un WebSocket. El problema era todo lo demás: salas, membresía, orden de mensajes, reconexión, historial, permisos y moderación. Por eso me parece relevante que [Azure Web PubSub Chat haya entrado en vista previa pública](https://techcommunity.microsoft.com/t5/apps-on-azure-blog/announcing-azure-web-pubsub-chat-in-public-preview/ba-p/4548907): no llega solo con otra API, sino con **un modelo de dominio de chat** encima de un servicio ya pensado para tiempo real a escala.

Mi lectura arquitectónica aquí es bastante directa. Si tu caso de uso principal es la conversación, esta novedad te permite dejar de cablear primitivas genéricas de mensajería y empezar desde conceptos que ya existen en tu negocio: `room`, `member`, `message`, `user` y `role`. Eso reduce código accidental, baja el riesgo de inconsistencias y deja tu backend donde, en mi opinión, siempre debió estar: identidad, gobierno y reglas de negocio.

{{< figure src="/images/azure-web-pubsub-chat-en-vista-previa-publica-menos-websockets-a-mano-mas-arquit/body-1.png" alt="Diagrama del modelo de chat sobre Azure Web PubSub" caption="El valor de la vista previa está en subir de primitivas de tiempo real a un modelo explícito de chat." >}}{{< /figure >}}

### Qué cambia exactamente con Web PubSub Chat

Según [la visión general de Azure Web PubSub](https://learn.microsoft.com/en-us/azure/azure-web-pubsub/overview), el servicio base sigue siendo la opción flexible cuando quieres diseñar tu propio modelo de eventos, grupos y mensajes. Pero la nueva capacidad de chat añade una capa superior específicamente orientada a conversación: creación de salas, gestión de miembros, envío de mensajes ordenados, historial persistente, roles y recuperación tras reconexión.

A mí esto me encaja mucho con una idea que repito bastante: **no toda flexibilidad es una ventaja**. Cuando construyes un chat sobre un servicio de tiempo real *raw*, heredas todas las decisiones incómodas. Cómo nombras eventos. Cómo serializas un mensaje. Cómo garantizas orden. Dónde guardas el histórico. Cómo resuelves el *rejoin* de un cliente que pierde conexión diez segundos. Si cada equipo responde a eso a su manera, el coste no aparece solo en desarrollo; aparece también en mantenimiento, en divergencias entre clientes y, por supuesto, en bugs bastante feos.

La [entrada oficial del anuncio](https://techcommunity.microsoft.com/t5/apps-on-azure-blog/announcing-azure-web-pubsub-chat-in-public-preview/ba-p/4548907) lo resume bien: Azure sigue gestionando la infraestructura de tiempo real, mientras tú trabajas con APIs de cliente y servidor centradas en chat. Además, el dato persistente del chat se conserva en una cuenta de Azure Storage elegida para el servicio. Y eso me parece importante porque separa con claridad la capa de transporte de la persistencia, que es justo el tipo de frontera arquitectónica que conviene no emborronar.

### Antes de empezar

Para reproducir el recorrido que te propongo, yo partiría de estos requisitos:

- Una suscripción de Azure con permisos para crear recursos.
- Un recurso de Azure Web PubSub ya creado.
- Una cuenta de Azure Storage asociada al escenario de chat persistente, tal y como indica el [anuncio de Azure Web PubSub Chat](https://techcommunity.microsoft.com/t5/apps-on-azure-blog/announcing-azure-web-pubsub-chat-in-public-preview/ba-p/4548907).
- Node.js 18 o superior, porque los tutoriales de Functions para Web PubSub usan esa base en la documentación de [serverless notification](https://learn.microsoft.com/en-us/azure/azure-web-pubsub/tutorial-serverless-notification).
- Azure Functions Core Tools v4 o superior.
- Azure CLI instalada.
- Si vas a probar el enfoque serverless clásico, una Function App y, opcionalmente, una Azure Static Web App.
- Para el ejemplo cliente, el paquete npm `@azure/web-pubsub-chat-client`, que Microsoft menciona en el anuncio de la vista previa pública.

Si vienes del enfoque clásico de Web PubSub, te recomiendo tener también a mano la guía de [chat serverless con Azure Static Web Apps](https://learn.microsoft.com/en-us/azure/azure-web-pubsub/tutorial-serverless-static-web-app), porque ahí se ve muy bien el contraste entre construir chat con primitivas genéricas y consumir un modelo de chat ya resuelto.

### Opción 1: probar el nuevo modelo de chat con el SDK de cliente

La primera prueba que yo haría es la más directa: crear una sala, escuchar mensajes y enviar uno. El propio anuncio enseña precisamente ese flujo con el SDK JavaScript `@azure/web-pubsub-chat-client`, y me parece la forma más rápida de entender el cambio de nivel de abstracción.

Primero preparo un proyecto Node mínimo:

```bash
mkdir webpubsub-chat-preview
cd webpubsub-chat-preview
npm init -y
npm install @azure/web-pubsub-chat-client
```

Lo esperable tras ese comando es lo de siempre: `package.json`, `node_modules` y cero drama (si `npm` decide colaborar, claro).

Ahora creo un archivo `chat-demo.mjs` con un flujo pequeño pero realista. Este ejemplo apunta al SDK JavaScript `@azure/web-pubsub-chat-client` citado en el [anuncio oficial](https://techcommunity.microsoft.com/t5/apps-on-azure-blog/announcing-azure-web-pubsub-chat-in-public-preview/ba-p/4548907):

```javascript
import { ChatClient } from "@azure/web-pubsub-chat-client";

const endpoint = process.env.CHAT_CLIENT_URL;

if (!endpoint) {
  throw new Error("Falta la variable CHAT_CLIENT_URL con la URL firmada de conexión");
}

const client = new ChatClient(endpoint);

try {
  client.on("message", ({ message }) => {
    console.log(`[mensaje] ${message.createdBy}: ${message.content.text}`);
  });

  await client.start();

  const room = await client.createRoom("Project Falcon", ["bob", "carol"]);
  console.log(`[room] creada ${room.roomId}`);

  await client.sendToRoom(room.roomId, "Bienvenido a la sala de proyecto");
  console.log("[send] mensaje enviado");

  for await (const item of client.listMessages(room.roomId)) {
    console.log(`[history] ${item.message.createdBy}: ${item.message.content.text}`);
    break; // Solo verifico que el historial responde y corto la iteración
  }
} finally {
  await client.stop().catch(() => undefined); // Evito dejar la conexión abierta si falla algún paso intermedio
}
```

Si todo va bien, deberías ver algo conceptualmente parecido a esto en consola:

```text
[room] creada 9f2c1d6e-3b8a-4b6a-a1d8-7e4a0f2d11ab
[send] mensaje enviado
[mensaje] alice: Bienvenido a la sala de proyecto
[history] alice: Bienvenido a la sala de proyecto
```

Aquí está la parte importante. Yo no estoy definiendo eventos `roomCreated`, `joinRequested` o `chatMessagePosted`, ni diseñando a mano un esquema de almacenamiento para que el cliente pueda hacer *scroll* hacia atrás sin romperse. Estoy consumiendo operaciones orientadas a chat. **Ese salto semántico es justo el valor del producto**.

{{< figure src="/images/azure-web-pubsub-chat-en-vista-previa-publica-menos-websockets-a-mano-mas-arquit/source-2.png" alt="Arquitectura serverless con Static Web Apps, Functions y Web PubSub" caption="El patrón serverless sigue siendo útil: cliente ligero, backend confiable y servicio gestionado para tiempo real. Fuente: [learn.microsoft.com](https://learn.microsoft.com/en-us/azure/azure-web-pubsub/tutorial-serverless-static-web-app)" >}}{{< /figure >}}

### Opción 2: mantener el backend en Functions y dejar el tiempo real al servicio gestionado

Aunque el nuevo modelo de chat resuelve mucho trabajo de *plumbing*, eso no elimina el backend. En mi opinión, lo recoloca donde toca: emisión de tokens de conexión, autenticación, autorización, moderación y reglas de negocio. En la documentación de [Azure Web PubSub con Azure Functions](https://learn.microsoft.com/en-us/azure/azure-web-pubsub/tutorial-serverless-notification) y en la [integración con Static Web Apps](https://learn.microsoft.com/en-us/azure/azure-web-pubsub/tutorial-serverless-static-web-app) se ve muy bien ese patrón serverless.

Primero creo una Function App local con el modelo Node para generar un endpoint de conexión. El objetivo aquí no es reinventar el chat, sino exponer el punto de entrada confiable que el cliente necesita para conectarse sin repartir secretos como si no hubiera un mañana.

```bash
func init chat-functions --worker-runtime node --model V4
cd chat-functions
func new --name negotiate --template "HTTP trigger" --authlevel anonymous
npm install @azure/web-pubsub
```

Deberías ver que Azure Functions Core Tools crea la estructura del proyecto y una función HTTP llamada `negotiate`.

Después, en `local.settings.json`, defino la conexión del servicio. La documentación de [Azure Web PubSub con Azure Functions](https://learn.microsoft.com/en-us/azure/azure-web-pubsub/tutorial-serverless-notification) insiste en algo que conviene tomarse en serio: las cadenas de conexión que aparecen en ejemplos son solo para demostración y en producción hay que protegerlas bien.

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "node",
    "WebPubSubConnectionString": "Endpoint=https://<tu-servicio>.webpubsub.azure.com;AccessKey=<clave>;Version=1.0;"
  }
}
```

Ahora implemento una negociación simple en `src/functions/negotiate.js`. El ejemplo usa el patrón serverless documentado para Web PubSub: el backend emite al cliente una URL de conexión en lugar de revelar claves.

```javascript
const { app } = require("@azure/functions");
const { WebPubSubServiceClient } = require("@azure/web-pubsub");

app.http("negotiate", {
  methods: ["GET"],
  authLevel: "anonymous",
  handler: async (request) => {
    const connectionString = process.env.WebPubSubConnectionString;

    if (!connectionString) {
      return {
        status: 500,
        jsonBody: { error: "Falta WebPubSubConnectionString" }
      };
    }

    const userId = request.query.get("user")?.trim() || "alice";
    const serviceClient = new WebPubSubServiceClient(connectionString, "chat");
    const token = await serviceClient.getClientAccessToken({ userId });

    return {
      jsonBody: {
        userId,
        url: token.url // El cliente recibe una URL firmada; la clave nunca sale del backend
      }
    };
  }
});
```

Al arrancar la función en local:

```bash
func start
```

verás algo como esto:

```text
Functions:
        negotiate: [GET] http://localhost:7071/api/negotiate
```

Y si pruebas el endpoint:

```bash
curl "http://localhost:7071/api/negotiate?user=alice"
```

la respuesta esperada será un JSON con `userId` y una `url` de conexión firmada:

```json
{
  "userId": "alice",
  "url": "wss://codertectura-chat.webpubsub.azure.com/client/hubs/chat?..."
}
```

Esta pieza me parece clave desde el punto de vista de arquitectura. El cliente gestiona la experiencia interactiva; el backend gestiona confianza. Esa separación ya estaba en el modelo serverless clásico de Web PubSub, pero con Chat ahora puedes combinarla con un dominio bastante más expresivo para la conversación.

### La diferencia real frente al enfoque WebSocket «hazlo tú mismo»

Si comparas esto con el tutorial clásico de [chat serverless con Static Web Apps y Web PubSub](https://learn.microsoft.com/en-us/azure/azure-web-pubsub/tutorial-serverless-static-web-app), el enfoque anterior sigue siendo válido, pero está más cerca de una caja de herramientas que de un producto de chat. Tienes conexiones, eventos, *bindings* y funciones para reaccionar a mensajes; después ya montas tus grupos, tus flujos y tu lógica de presencia.

Con la nueva capacidad, Microsoft está diciendo algo importante: hay escenarios donde la abstracción correcta no es «mensajería en tiempo real», sino «chat». Y cuando eliges esa abstracción, todo encaja mejor en la arquitectura:

- El front habla en términos de sala, miembro e historial.
- El backend se reserva identidad y reglas.
- La persistencia deja de ser un añadido improvisado.
- La reconexión y la recuperación de mensajes pasan a ser capacidades esperables del sistema.

{{< figure src="/images/azure-web-pubsub-chat-en-vista-previa-publica-menos-websockets-a-mano-mas-arquit/body-3.png" alt="Comparativa entre Web PubSub base y Web PubSub Chat" caption="La diferencia no es solo técnica: cambia el nivel de abstracción con el que diseñas la solución." >}}{{< /figure >}}

Yo no interpretaría esto como que el servicio base ya no importe. Al revés: sigue siendo la base adecuada para notificaciones, *dashboards*, *streaming* de tokens de IA o colaboración con modelos de evento propios, como explica [la visión general de Web PubSub](https://learn.microsoft.com/en-us/azure/azure-web-pubsub/overview). Pero si tu aplicación principal es conversación humana —o incluso conversación asistida por IA—, **seguir montando toda la semántica de chat sobre primitivas genéricas empieza a parecer trabajo evitable**.

### Dónde encaja mejor esta vista previa pública

A mí me parece especialmente interesante en cuatro tipos de soluciones:

- Portales de soporte con conversación persistente por caso.
- Aplicaciones colaborativas con salas de proyecto o equipo.
- *Marketplaces* o plataformas con mensajería entre usuarios.
- Experiencias de IA con historial conversacional y tiempo real.

El anuncio menciona precisamente dominios como soporte, colaboración, *gaming*, *marketplaces*, salud, servicios financieros y aplicaciones impulsadas por IA. Tiene sentido: en todos ellos no basta con empujar bytes por un socket. Lo que necesitas es un sistema que entienda la conversación como una entidad de primer nivel.

### Mi conclusión

Mi impresión es que Azure Web PubSub Chat llega en el momento correcto. No sustituye al servicio base; lo especializa para un problema que muchas veces acababa resuelto a medias dentro de cada equipo. Si me preguntas por el valor arquitectónico, yo lo resumiría así: **menos *plumbing* de WebSocket, más modelo de negocio reutilizable**.

Y eso, sinceramente, suele ser una buena noticia. Porque donde antes invertías tiempo en cableado técnico, ahora puedes dedicarlo a lo que de verdad diferencia tu producto: identidad, moderación, experiencia, reglas y contexto.

{{< figure src="/images/azure-web-pubsub-chat-en-vista-previa-publica-menos-websockets-a-mano-mas-arquit/source-4.png" alt="Flujo de interacción entre cliente, Web PubSub y Azure Functions" caption="Azure Functions encaja como punto confiable de autenticación y negociación sin exponer secretos al cliente. Fuente: [learn.microsoft.com](https://learn.microsoft.com/en-us/azure/azure-web-pubsub/tutorial-serverless-notification)" >}}{{< /figure >}}

Si estás evaluando una nueva aplicación de chat en Azure, yo probaría esta vista previa cuanto antes. Aunque solo sea para confirmar una sospecha bastante sana: que quizá ya no necesitas construir tú la parte aburrida.
