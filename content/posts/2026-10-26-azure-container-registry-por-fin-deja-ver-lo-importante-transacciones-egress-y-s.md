---
title: 'Azure Container Registry por fin deja ver lo importante: transacciones, egress
  y señales que sí escalan'
date: '2026-10-26T06:28:29+00:00'
draft: true
slug: azure-container-registry-por-fin-deja-ver-lo-importante-transacciones-egress-y-s
description: Azure Container Registry añade métricas de Transactions y Data Transfer,
  y eso cambia de verdad cómo observo despliegues, throttling y tráfico entre regiones.
categories:
- Azure
- Arquitectura de Software
- Observabilidad
tags:
- Azure Container Registry
- Observabilidad
- Azure Monitor
- Grafana
- Contenedores
- Plataforma
image: /images/azure-container-registry-por-fin-deja-ver-lo-importante-transacciones-egress-y-s/cover.png
comments: true
ai:
  assisted: true
  article_type: technical
  model: gpt-5.4
  prompt_version: 2026-08-21.1
  generated_at: '2026-10-26T06:28:29+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://techcommunity.microsoft.com/t5/apps-on-azure-blog/making-azure-container-registry-activity-visible-at-scale/ba-p/4567301
    title: Making Azure Container Registry Activity Visible at Scale
    published_date: '2026-10-23'
  - url: https://azure.microsoft.com/updates?id=577963
    title: '[Launched] Generally Available: Item Level Recovery for Azure VMs with
      Premium SSDv2 and Ultra Disks in Azure Backup'
    published_date: '2026-10-23'
  - url: https://learn.microsoft.com/en-us/azure/container-registry/monitor-container-registry
    title: Monitor Azure Container Registry - Azure Container Registry | Microsoft
      Learn
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/container-registry/monitor-container-registry-reference
    title: Monitoring Data Reference for Azure Container Registry - Azure Container
      Registry | Microsoft Learn
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/container-registry/container-registry-dashboards-with-grafana?view=azuremgmtiothub-1.1.0
    title: Use Grafana dashboards in Azure Container Registry
    published_date: null
---

Durante bastante tiempo, observar Azure Container Registry era suficiente si solo querías una foto general: cuántos *pulls* había, cuántos *pushes* y cuánto almacenamiento usabas. Pero si de verdad te importaba entender **qué estaba pasando debajo de ese número**, la visibilidad se quedaba corta. Ahora eso cambia con la llegada de las métricas **Transactions** y **Data Transfer**, que según [el anuncio técnico de Azure Container Registry](https://techcommunity.microsoft.com/t5/apps-on-azure-blog/making-azure-container-registry-activity-visible-at-scale/ba-p/4567301) permiten ver qué operaciones sirve el registro, en qué región y cuántos datos de salida mueven.

A mí esta novedad no me parece un retoque cosmético del portal. Me parece una mejora seria de plataforma. Si trabajas con AKS, *pipelines* de build, escáneres de seguridad, geo-replicación o despliegues repartidos, por fin puedes distinguir un pico legítimo de tráfico de un bucle de reintentos, una ola de *throttling* o una distribución regional desequilibrada. Y eso convierte la observabilidad del registry en algo accionable, no en una colección de gráficas bonitas.

### Qué cambia exactamente y por qué me parece importante

Hasta ahora, si yo veía subir los *pulls*, sabía que algo estaba descargando más imágenes, pero no necesariamente entendía el motivo. Tal como explica [Microsoft en su publicación sobre visibilidad de actividad a escala](https://techcommunity.microsoft.com/t5/apps-on-azure-blog/making-azure-container-registry-activity-visible-at-scale/ba-p/4567301), con estas métricas ya no me quedo en el resumen: puedo separar transacciones por tipo de operación, región y resultado, y además observar el egress real con **Data Transfer**.

Eso cambia por completo el tipo de preguntas que puedo responder. Ya no es solo «¿hay más tráfico?», sino «¿son descargas de blobs o lecturas de manifiestos?», «¿vienen de West Europe o de North Europe?», «¿están fallando o siendo *throttled*?», «¿sube el número de peticiones o suben los bytes por petición?». **Ese salto, de contar eventos a explicar comportamiento, es justo lo que espero de una plataforma madura.**

{{< figure src="/images/azure-container-registry-por-fin-deja-ver-lo-importante-transacciones-egress-y-s/body-1.png" alt="Esquema de métricas de Azure Container Registry por operación y región" caption="Las nuevas métricas permiten pasar de un contador global a una lectura por operación, región y volumen de datos." >}}{{< /figure >}}

Si te mueves en arquitectura, esto tiene consecuencias muy poco teóricas. Un despliegue sano de Kubernetes suele dejar un patrón muy distinto al de un *scanner* agresivo o al de un cliente mal configurado que repite solicitudes sin control. También ayuda a detectar un problema de afinidad regional: a veces la réplica existe, sí, pero el tráfico no está yendo donde tú creías. Y cuando pagas salida de datos o sufres latencia entre regiones, entender por dónde se mueve el tráfico deja de ser una curiosidad para convertirse en una decisión de diseño.

### Antes de empezar

Si quieres reproducir lo que te enseño, esto es lo que yo tendría preparado:

- Una suscripción de Azure activa.
- Un registro de Azure Container Registry ya creado.
- Si quieres analizar por región, una configuración con geo-replicación en ACR ayuda mucho.
- Permisos para leer métricas del recurso. En la práctica, yo usaría al menos acceso de lectura sobre el recurso y capacidad para crear alertas o *dashboards* si luego quieres automatizarlo.
- [Azure CLI](https://learn.microsoft.com/en-us/azure/container-registry/monitor-container-registry) instalado y actualizado. En este artículo doy por hecho **Azure CLI 2.75 o superior**.
- Acceso al portal de Azure y, si quieres seguir la parte visual, a la experiencia de [dashboards con Grafana para Azure Container Registry](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-dashboards-with-grafana?view=azuremgmtiothub-1.1.0).
- Que el registry haya tenido actividad reciente. Si no hay tráfico, las métricas existirán, pero verás series vacías o completamente planas.

No parece una lista complicada, pero conviene decirlo. Muchas veces el problema no es que la métrica no funcione, sino que estamos mirando un registro sin actividad o con un rango temporal que no dice nada. Y luego vienen los «esto no devuelve nada» (que casi siempre son un clásico).

### Lo primero que haría: pintar Transactions por ApiName y Region

La forma más rápida de validar que esto te aporta valor es consultar la métrica y dividirla por dimensiones. La [referencia de monitorización de Azure Container Registry](https://learn.microsoft.com/en-us/azure/container-registry/monitor-container-registry-reference) deja claro que el servicio expone métricas de plataforma con dimensiones para análisis y segmentación, y ahí está justo la gracia de esta mejora.

Yo empezaría obteniendo el identificador del registry y consultando métricas desde Azure CLI. Este ejemplo está pensado para **Azure CLI 2.75+**.

```bash
# Azure CLI 2.75+
az login
az account set --subscription "Plataforma-Produccion"

ACR_ID=$(az acr show \
  --name codertecturaregistry \
  --resource-group rg-platform-prod \
  --query id \
  --output tsv)

az monitor metrics list \
  --resource "$ACR_ID" \
  --metric Transactions \
  --interval PT1H \
  --aggregation Total \
  --output json
```

La salida esperada es un JSON con la definición de la métrica y una colección de series temporales. Si tu registro ha tenido actividad, verás puntos con valores agregados por hora.

```json
{
  "cost": 0,
  "interval": "PT1H",
  "namespace": "Microsoft.ContainerRegistry/registries",
  "resourceregion": "westeurope",
  "value": [
    {
      "displayDescription": "Registry transactions",
      "name": {
        "localizedValue": "Transactions",
        "value": "Transactions"
      },
      "timeseries": [
        {
          "data": [
            {
              "timeStamp": "2026-10-26T09:00:00Z",
              "total": 1842
            }
          ]
        }
      ]
    }
  ]
}
```

Con eso validas que la métrica existe y devuelve datos. Pero donde de verdad gana valor es al dividir por dimensión en el portal o en Grafana. En la guía para [monitorizar Azure Container Registry](https://learn.microsoft.com/en-us/azure/container-registry/monitor-container-registry), Microsoft destaca precisamente el uso de paneles para ver tendencias de transacciones, transferencia de datos, *throttling* y almacenamiento.

Mi recomendación práctica es muy simple: crea un gráfico de líneas o de barras apiladas con **Transactions**, agregación **Total**, rango de tiempo de 24 horas, y separa por **ApiName** y **Region**. Si el portal no te deja ver ambas dimensiones a la vez como tú querrías, crea dos visualizaciones complementarias: una por operación y otra por región. Lo importante no es la estética. Lo importante es que puedas responder rápido qué patrón ha cambiado.

{{< figure src="/images/azure-container-registry-por-fin-deja-ver-lo-importante-transacciones-egress-y-s/body-2.png" alt="Diagrama de gráfico de Transactions dividido por ApiName y Region" caption="Dividir Transactions por ApiName y Region es la forma más rápida de detectar qué cambió de verdad en el registry." >}}{{< /figure >}}

### Cómo leer ese gráfico sin engañarte

Aquí es donde, en mi experiencia, mucha gente se queda a medio camino. Ver más transacciones no implica automáticamente más despliegues. Un aumento de descargas de `blob` puede significar más *pulls* reales, sí, pero también puede indicar una tormenta de reintentos, nodos efímeros rehaciendo caché o un componente preguntando demasiado y demasiado a menudo.

Por eso me gusta cruzar dos ejes: transacciones y datos transferidos. Si suben mucho las operaciones pero **Data Transfer** apenas se mueve, yo sospecharía antes de tráfico de control, metadatos o reintentos fallidos que de un incremento real en la distribución de imágenes. En cambio, si las transacciones se mantienen y el egress sube, probablemente no estás haciendo más peticiones: estás moviendo capas más pesadas o artefactos mayores.

Ese cruce de señales es, para mí, el valor real de esta novedad. Antes podía intuir. Ahora puedo comprobar. Y eso cambia bastante la conversación entre «creo que pasa algo raro» y «sé qué está cambiando y dónde».

### Segunda comprobación: medir Data Transfer y comparar regiones

La otra métrica nueva es la que más me interesa cuando pienso en coste, latencia y topología: **Data Transfer**. El [artículo técnico de Microsoft](https://techcommunity.microsoft.com/t5/apps-on-azure-blog/making-azure-container-registry-activity-visible-at-scale/ba-p/4567301) la describe como la forma de ver cuántos datos de salida mueve el registry, incluida la perspectiva regional en registros con geo-replicación.

Puedes consultarla también con Azure CLI. De nuevo, este ejemplo apunta a **Azure CLI 2.75+**.

```bash
# Azure CLI 2.75+
az monitor metrics list \
  --resource "$ACR_ID" \
  --metric "Data Transfer" \
  --interval PT1H \
  --aggregation Total \
  --start-time 2026-10-25T00:00:00Z \
  --end-time 2026-10-26T00:00:00Z \
  --output json  # JSON es más útil si luego quieres separar, filtrar o llevarte la serie a otra herramienta
```

La salida esperada no siempre será especialmente amable si la pides en tabla, así que yo aquí prefiero `json` desde el principio. Un resultado simplificado puede parecerse a esto:

```text
Cost    Interval    Namespace                                 Metric         Time Grain    Total
------  ----------  ----------------------------------------  -------------  ------------  --------
0       PT1H        Microsoft.ContainerRegistry/registries    Data Transfer  PT1H          12884901888
```

A partir de ahí, yo me iría a los [dashboards con Grafana para Azure Container Registry](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-dashboards-with-grafana?view=azuremgmtiothub-1.1.0). No porque el portal no sirva, sino porque comparar tendencias por región y cruzarlas con otras señales resulta bastante más cómodo ahí. La documentación habla de *dashboards* predefinidos y personalizables para entender patrones de uso, *throttling*, almacenamiento y transferencia de datos, y a mí me parece la vía más práctica para convertir estas métricas en una rutina operativa.

Si ves, por ejemplo, que West Europe concentra casi todo el egress mientras North Europe está infrautilizada, tienes una pista muy clara para revisar tu estrategia de réplica o la afinidad de tus *clusters*. **No es solo monitorización: es *feedback* directo sobre el diseño de tu plataforma.**

{{< figure src="/images/azure-container-registry-por-fin-deja-ver-lo-importante-transacciones-egress-y-s/body-3.png" alt="Comparación visual de Data Transfer entre regiones en Azure Container Registry" caption="Comparar Data Transfer entre regiones ayuda a validar si la geo-replicación está repartiendo el tráfico como esperas." >}}{{< /figure >}}

### Tercer paso: levantar una alerta útil de verdad

Las métricas están muy bien, pero donde se vuelven operativas de verdad es en las alertas. Y aquí yo intentaría no caer en la alerta genérica de «ha subido el tráfico». Prefiero alertas que apunten a síntomas concretos: un pico de egress fuera de patrón o una subida de respuestas *throttled*, que en el contexto del anuncio de Microsoft aparece como uno de los casos de uso más claros para entender cambios de comportamiento.

Para automatizarlo, puedes crear una regla de alerta de métricas con Azure CLI. Este ejemplo está pensado para **Azure CLI 2.75+** y crea una alerta sencilla sobre `Transactions`. Si en tu entorno observas que cierto patrón de *throttling* se refleja en una dimensión concreta, puedes afinar después la regla desde el portal con filtros y segmentación.

```bash
# Azure CLI 2.75+
ACTION_GROUP_ID=$(az monitor action-group create \
  --name ag-acr-platform \
  --resource-group rg-platform-prod \
  --short-name acrplat \
  --action email PlataformaOps platformops@codertectura.local \
  --query id \
  --output tsv)

az monitor metrics alert create \
  --name acr-transactions-spike \
  --resource-group rg-platform-prod \
  --scopes "$ACR_ID" \
  --condition "total Transactions > 5000" \
  --window-size 15m \
  --evaluation-frequency 5m \
  --severity 2 \
  --description "Pico inesperado de transacciones en Azure Container Registry" \
  --action "$ACTION_GROUP_ID"
```

La salida esperada es la confirmación de creación de la regla. Si todo va bien, Azure CLI devolverá un objeto JSON con el identificador completo de la alerta y su estado aprovisionado.

```json
{
  "id": "/subscriptions/11111111-2222-3333-4444-555555555555/resourceGroups/rg-platform-prod/providers/microsoft.insights/metricAlerts/acr-transactions-spike",
  "location": "global",
  "name": "acr-transactions-spike",
  "type": "Microsoft.Insights/metricAlerts"
}
```

Aquí el umbral de `5000` no tiene nada de mágico. Es solo un ejemplo reproducible. Lo correcto es ajustarlo a tu línea base. Si tienes un registry muy activo, ese valor será ridículo; si tienes un entorno pequeño, quizá sea demasiado alto. Lo importante es otra cosa: **ya puedes construir alertas sobre señales mucho más expresivas que un contador grueso de *pulls*.**

### Qué haría yo en producción con estas métricas

Si me preguntas por una hoja de ruta sensata, yo iría por aquí:

1. **Separar *dashboards* operativos y de capacidad**. Uno para incidencias rápidas: transacciones por operación, región y *throttling*. Otro para tendencias: egress, crecimiento y distribución regional.
2. **Definir una línea base por entorno**. Producción no se parece a preproducción, y un registry central compartido no se comporta igual que uno dedicado por dominio.
3. **Cruzar ACR con el resto de la plataforma**. Si suben las descargas de blobs, compáralo con despliegues de AKS, escalados de nodos o *jobs* de seguridad.
4. **Revisar la geo-replicación con datos reales**. No des por hecho que una réplica ayuda solo porque exista; verifica que el tráfico de esa región la está usando.
5. **Alertar síntomas, no ruido**. Yo prefiero dos o tres alertas buenas sobre *throttling*, egress anómalo y cambio brusco de patrón, antes que diez alertas genéricas que nadie mira.

{{< figure src="/images/azure-container-registry-por-fin-deja-ver-lo-importante-transacciones-egress-y-s/body-4.png" alt="Flujo de alerta de Azure Monitor sobre métricas de Azure Container Registry" caption="La observabilidad se vuelve operativa cuando conviertes métricas expresivas en alertas con contexto." >}}{{< /figure >}}

El matiz importante aquí es que estas métricas no sustituyen al resto de tu observabilidad. No reemplazan logs, ni trazas, ni eventos de despliegue. Lo que hacen es darte una capa intermedia muy valiosa: una forma de ver el comportamiento del registry como servicio compartido. Y cuando ACR está en medio de builds, despliegues, *runtimes* y escáneres, esa capa intermedia suele ser justo la que faltaba.

### Mi conclusión

Esta mejora de Azure Container Registry me parece una de esas novedades que no hacen demasiado ruido fuera del mundo plataforma, pero que sí tienen impacto real en el día a día. La observabilidad útil no consiste en tener más gráficas: consiste en poder explicar un cambio, localizarlo y decidir qué hacer. Y eso es exactamente lo que aportan **Transactions** y **Data Transfer**.

Si ya usas ACR como pieza central de tu distribución de artefactos, mi consejo es muy simple: no te quedes en el *overview*. Abre las métricas, separa por operación y región, mira el egress y levanta alertas con intención. Porque cuando tu plataforma crece, **lo que no distingues, no lo puedes gobernar**.

Y aquí, por fin, ACR empieza a distinguir lo que de verdad importa.
