---
title: 'Azure Arc ya actualiza su agente solo: qué cambia de verdad en tus operaciones
  híbridas'
date: '2026-11-02T06:29:56+00:00'
draft: true
slug: azure-arc-ya-actualiza-su-agente-solo-que-cambia-de-verdad-en-tus-operaciones-hi
description: La actualización automática del agente de Azure Arc ya está disponible
  con carácter general. Te cuento qué cambia en el day-2, cómo activarla y cómo comprobarla
  con CLI y ARM.
categories:
- Azure
- Arquitectura de Software
- Operaciones
tags:
- Azure Arc
- Operaciones híbridas
- Servidores
- Azure CLI
- Infraestructura como código
image: /images/azure-arc-ya-actualiza-su-agente-solo-que-cambia-de-verdad-en-tus-operaciones-hi/cover.png
comments: true
ai:
  assisted: true
  article_type: technical
  model: gpt-5.4
  prompt_version: 2026-08-21.1
  generated_at: '2026-11-02T06:29:56+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://techcommunity.microsoft.com/t5/azure-arc-blog/simplify-azure-arc-agent-updates-with-automatic-agent-upgrade/ba-p/4568413
    title: Simplify Azure Arc agent updates with Automatic Agent Upgrade, now generally
      available
    published_date: '2026-10-30'
  - url: https://learn.microsoft.com/en-gb/azure/azure-arc/servers/automatic-agent-upgrade
    title: Automatically upgrade the Azure Connected Machine agent - Azure Arc | Microsoft
      Learn
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/azure-arc/servers/manage-agent
    title: Manage Azure Connected Machine agent versions - Azure Arc | Microsoft Learn
    published_date: null
---

Si trabajas con Azure Arc de verdad, sabes que el problema casi nunca está en el *onboarding* inicial. Lo incómodo llega después: mantener una flota de servidores conectados, con versiones coherentes del agente y sin convertir cada actualización en una pequeña campaña manual. Por eso me parece relevante que la [actualización automática del agente de Azure Arc ya esté disponible con carácter general](https://techcommunity.microsoft.com/t5/azure-arc-blog/simplify-azure-arc-agent-updates-with-automatic-agent-upgrade/ba-p/4568413). No es una novedad vistosa, pero sí una de esas capacidades que **mejoran de verdad el day-2** en entornos híbridos.

Lo interesante no es solo que Microsoft gestione las nuevas versiones del Azure Connected Machine agent. Lo importante es el cambio operativo que introduce: pasas de perseguir servidores para aplicar *upgrades* a declarar una intención de plataforma. Según la [documentación de Azure Arc sobre actualización automática del agente](https://learn.microsoft.com/en-gb/azure/azure-arc/servers/automatic-agent-upgrade), los despliegues se realizan por lotes, por regiones y durante horas de baja actividad, con reintentos si algo no termina bien. En una flota híbrida, esa diferencia pesa bastante más que un botón nuevo en el portal.

### Qué cambia exactamente en el modelo operativo

Hasta ahora, si querías mantener el agente al día, tenías que apoyarte en procesos manuales, automatizaciones propias o revisiones periódicas del estado de la flota. La [guía de gestión de versiones del agente](https://learn.microsoft.com/en-us/azure/azure-arc/servers/manage-agent) deja claro que esas tareas de mantenimiento existen y que el agente se actualiza con correcciones, mejoras de estabilidad y nuevas capacidades. En unas pocas máquinas, eso es asumible. En decenas o cientos, empieza a convertirse en deuda operativa con bastante facilidad.

Yo lo resumiría así: con la actualización automática, Microsoft asume el ciclo de vida del agente una vez que tú habilitas la capacidad. Eso no elimina tu gobierno ni tu responsabilidad sobre el entorno, pero sí reduce mucha fricción diaria. **Dejas de gestionar versiones una a una y pasas a gestionar una política de actualización.** En operaciones híbridas, ese cambio es más profundo de lo que parece a primera vista.

{{< figure src="/images/azure-arc-ya-actualiza-su-agente-solo-que-cambia-de-verdad-en-tus-operaciones-hi/body-1.png" alt="Diagrama del flujo de actualización automática del agente en Azure Arc" caption="La actualización automática desplaza la responsabilidad del despliegue del agente desde la operación manual hacia un modelo administrado desde Azure Arc." >}}{{< /figure >}}

Además, hay un detalle práctico que para muchos equipos marca la diferencia: la [documentación oficial](https://learn.microsoft.com/en-gb/azure/azure-arc/servers/automatic-agent-upgrade) indica que no hace falta reiniciar el servidor para instalar o actualizar el agente. Ese punto, por sí solo, baja bastante el miedo inicial a activarlo. También conviene tener presentes los requisitos: necesitas la versión 1.67 o superior del agente; en Windows la política de ejecución de PowerShell no puede estar en `Restricted`; y en Linux debe existir y estar en ejecución el servicio `cron`.

### Antes de empezar

Si quieres reproducir lo que te muestro aquí de punta a punta, yo dejaría preparada esta base:

- Una máquina ya conectada a Azure Arc como servidor habilitado para Arc.
- [Azure Connected Machine agent en versión 1.67 o posterior](https://learn.microsoft.com/en-gb/azure/azure-arc/servers/automatic-agent-upgrade).
- `Azcmagent` instalado en la máquina Arc.
- Azure CLI 2.75 o superior en tu equipo de administración, con sesión iniciada en la suscripción correcta.
- Permisos para leer y actualizar el recurso `Microsoft.HybridCompute/machines` en el grupo de recursos donde vive la máquina Arc.
- En Linux, el servicio `cron` instalado y arrancado.
- En Windows, una política de PowerShell compatible; la [documentación oficial](https://learn.microsoft.com/en-gb/azure/azure-arc/servers/automatic-agent-upgrade) indica que `Restricted` no está soportado.

Si la máquina todavía no está en una versión compatible del agente, primero tendrás que llevarla a una versión reciente con alguno de los [métodos de gestión del agente que documenta Microsoft](https://learn.microsoft.com/en-us/azure/azure-arc/servers/manage-agent). Aquí no hay magia: la automatización empieza a ayudarte a partir de 1.67, no antes.

### Opción 1: habilitar la actualización automática desde la propia máquina

La forma más directa de empezar es hacerlo en el servidor Arc mediante `azcmagent`. La [documentación](https://learn.microsoft.com/en-gb/azure/azure-arc/servers/automatic-agent-upgrade) explica que la actualización automática puede habilitarse durante el *onboarding* con `--enable-automatic-upgrade`, pero si la máquina ya está conectada, hay un paso muy útil: asegurarte de que el bloqueo local no impida la gestión automática.

Yo empezaría comprobando el estado actual del agente y su versión:

```bash
# Azure Connected Machine agent 1.67+ en la máquina Arc
azcmagent version
azcmagent config list
```

Lo esperable es ver la versión instalada del agente y la configuración actual. Si en la salida aparece `automaticupgrade`, ya tienes una referencia clara del punto de partida.

Después, quitaría el bloqueo local:

```bash
# Azure Connected Machine agent 1.67+
azcmagent config set automaticupgrade.blocklocally false
```

Ese `false` es la línea importante, porque **evita que el propio host bloquee** el mecanismo administrado desde Azure. No activa por sí solo toda la experiencia de gobierno centralizado, pero sí elimina una fricción bastante habitual.

Para confirmarlo:

```bash
# Azure Connected Machine agent 1.67+
azcmagent config get automaticupgrade.blocklocally
```

La salida que espero aquí es esta:

```text
automaticupgrade.blocklocally: false
```

Este paso, por sí solo, no sustituye la configuración del recurso en Azure cuando quieres gobernarlo de forma centralizada. Aun así, me parece importante porque representa la parte *host-level* del cambio: el servidor deja de oponerse localmente al modelo administrado.

### Opción 2: activar `enableAutomaticUpgrade` en el recurso de Azure Arc con ARM y `az rest`

Aquí está la parte realmente interesante si gestionas flotas. La capacidad también se puede activar sobre el recurso `Microsoft.HybridCompute/machines`, y eso encaja mucho mejor con automatización, gobierno y despliegues repetibles. La propia publicación de disponibilidad general insiste en que ahora es más sencillo adoptarlo a escala, y tratarlo como configuración del recurso en Azure es, en mi opinión, el camino natural.

Primero, localiza tu máquina Arc para confirmar nombre, grupo de recursos y suscripción:

```bash
# Azure CLI 2.75+
az connectedmachine list --resource-group rg-arc-prod-weu --output table
```

La salida debería mostrar al menos una fila con el nombre de la máquina, su ubicación y su identificador. Si no aparece nada, normalmente el problema no es Azure Arc (aunque apetezca culparlo), sino que estás en la suscripción o en el grupo de recursos equivocados.

Una vez identificado el recurso, yo aplicaría el cambio con `az rest` contra la API de `Microsoft.HybridCompute`:

```bash
# Azure CLI 2.75+
SUBSCRIPTION_ID=$(az account show --query id --output tsv)
RESOURCE_GROUP="rg-arc-prod-weu"
MACHINE_NAME="srv-bilbao-01"
API_VERSION="2025-02-19-preview"

az rest \
  --method PATCH \
  --url "https://management.azure.com/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.HybridCompute/machines/${MACHINE_NAME}?api-version=${API_VERSION}" \
  --headers "Content-Type=application/json" \
  --body @- <<'JSON'
{
  "properties": {
    "agentUpgrade": {
      "enableAutomaticUpgrade": true
    }
  }
}
JSON
```

He preferido enviar el cuerpo con un *heredoc* porque reduce errores tontos de *escaping* al automatizar scripts o pipelines. Si todo va bien, recibirás un documento JSON del recurso actualizado. Lo importante es que en la respuesta aparezca `properties.agentUpgrade.enableAutomaticUpgrade` con valor `true`.

Para comprobarlo de forma limpia:

```bash
# Azure CLI 2.75+
az rest \
  --method GET \
  --url "https://management.azure.com/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.HybridCompute/machines/${MACHINE_NAME}?api-version=${API_VERSION}" \
  --query "properties.agentUpgrade" \
  --output json
```

La salida que deberías ver será conceptualmente parecida a esta:

```json
{
  "enableAutomaticUpgrade": true
}
```

{{< figure src="/images/azure-arc-ya-actualiza-su-agente-solo-que-cambia-de-verdad-en-tus-operaciones-hi/body-2.png" alt="Diagrama de parcheo ARM del recurso Microsoft.HybridCompute/machines" caption="Activar la capacidad en el recurso de Azure permite gobernarla como configuración de plataforma, no solo como ajuste local del servidor." >}}{{< /figure >}}

Aquí está la idea importante: cuando activas esto en el recurso, estás moviendo la configuración al plano de control de Azure. Eso abre la puerta a gestionarlo con política, con inventario, con remediación y con revisiones de cumplimiento. **Para una flota híbrida, ese es el momento en el que una opción útil se convierte en una capacidad de plataforma.**

### Cómo verificar el estado en una flota, no solo en una máquina

Activarlo en un solo servidor está bien para probar. Pero el valor real aparece cuando quieres ver cuántas máquinas lo tienen activado y en qué versión de agente están. La publicación de GA menciona precisamente el escenario de escala y el uso de Azure Policy para remediar máquinas no configuradas, y eso encaja muy bien con una comprobación periódica del estado de la flota.

Con Azure CLI puedes sacar una vista rápida de varias máquinas dentro de un grupo de recursos:

```bash
# Azure CLI 2.75+
az connectedmachine list \
  --resource-group rg-arc-prod-weu \
  --query "[].{machine:name, location:location, os:properties.osName, agentVersion:properties.agentVersion, automaticUpgrade:properties.agentUpgrade.enableAutomaticUpgrade}" \
  --output table
```

La salida esperada es una tabla donde cada máquina muestra, como mínimo, nombre, sistema operativo, versión del agente y si `automaticUpgrade` está en `true` o `false`.

Un resultado típico se vería así:

```text
Machine         Location     Os                AgentVersion    AutomaticUpgrade
--------------  -----------  ----------------  --------------  -----------------
srv-bilbao-01   westeurope   Windows Server    1.67.02881.123  true
srv-malaga-02   westeurope   Ubuntu 22.04      1.67.02881.123  true
srv-sevilla-03  westeurope   Windows Server    1.66.02710.090  false
```

Esa tabla da una foto muy útil del estado real. Si ves agentes por debajo de 1.67, ya sabes que primero tendrás que actualizarlos con alguno de los [métodos manuales o asistidos que recoge la documentación de gestión del agente](https://learn.microsoft.com/en-us/azure/azure-arc/servers/manage-agent). Si ves `false` en la columna de actualización automática, puedes remediarlo con ARM, con Azure Policy o integrarlo en tu proceso de *onboarding* para que no vuelva a ocurrir.

{{< figure src="/images/azure-arc-ya-actualiza-su-agente-solo-que-cambia-de-verdad-en-tus-operaciones-hi/body-3.png" alt="Esquema de verificación de una flota de máquinas Arc con versión de agente y actualización automática" caption="La verificación a nivel de flota es donde esta capacidad gana sentido operativo: versión, cumplimiento y remediación dejan de revisarse máquina a máquina." >}}{{< /figure >}}

### Mi lectura práctica: menos trabajo repetitivo, más gobierno explícito

A mí esta capacidad me gusta por una razón muy simple: ataca una tarea poco glamurosa pero muy costosa. Mantener agentes al día rara vez entra en la lista de prioridades vistosas del trimestre, pero cuando se descuida, termina apareciendo como riesgo operativo, inconsistencia de soporte o pérdida de funcionalidades nuevas. La [documentación oficial](https://learn.microsoft.com/en-gb/azure/azure-arc/servers/automatic-agent-upgrade) deja claro que la finalidad es mantener el agente al día con correcciones, estabilidad y nuevas capacidades, sin tener que desplegar manualmente cada versión.

También me parece acertado el enfoque de *rollout* por lotes y en horas valle que describen tanto el [anuncio de disponibilidad general](https://techcommunity.microsoft.com/t5/azure-arc-blog/simplify-azure-arc-agent-updates-with-automatic-agent-upgrade/ba-p/4568413) como la [guía de Microsoft Learn](https://learn.microsoft.com/en-gb/azure/azure-arc/servers/automatic-agent-upgrade). Eso reduce el típico miedo a una actualización masiva y simultánea. No elimina la necesidad de observabilidad —ojalá—, pero sí baja bastante el riesgo de operación torpe.

Si me preguntas por una hoja de ruta sensata, yo iría por aquí:

1. Verificar qué máquinas ya están en la versión 1.67 o superior del agente.
2. Quitar bloqueos locales con `azcmagent config set automaticupgrade.blocklocally false`.
3. Activar `enableAutomaticUpgrade` en el recurso Arc de una muestra pequeña.
4. Revisar el comportamiento durante unos días.
5. Extenderlo por grupos de recursos o suscripciones, idealmente con la política integrada que menciona Microsoft.

### Conclusión

La actualización automática del agente de Azure Arc no cambia tu arquitectura híbrida de un día para otro, pero sí cambia algo importante: **reduce trabajo manual en una capa crítica de operación continua**. Y eso, en *day-2*, suele valer bastante más que muchas novedades más llamativas.

Mi consejo es que no lo mires como una simple comodidad. Yo lo veo como una forma de formalizar el mantenimiento del plano de conexión entre tus servidores y Azure. Si Azure Arc forma parte de tu plataforma híbrida, tener ese agente actualizado de manera consistente no es un detalle menor; es parte de la fiabilidad del conjunto.
