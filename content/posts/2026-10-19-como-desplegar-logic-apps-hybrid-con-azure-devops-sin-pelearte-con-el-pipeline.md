---
title: Cómo desplegar Logic Apps Hybrid con Azure DevOps sin pelearte con el pipeline
date: '2026-10-19T06:28:09+00:00'
draft: true
slug: como-desplegar-logic-apps-hybrid-con-azure-devops-sin-pelearte-con-el-pipeline
description: Te muestro un flujo práctico para desplegar Logic Apps Hybrid en Kubernetes
  con Azure Arc y Azure DevOps, separando infraestructura, paquete y publicación.
categories:
- Azure
- Arquitectura de Software
tags:
- Logic Apps Hybrid
- Azure DevOps
- Azure Arc
- Kubernetes
- CI/CD
image: /images/como-desplegar-logic-apps-hybrid-con-azure-devops-sin-pelearte-con-el-pipeline/cover.png
comments: true
ai:
  assisted: true
  article_type: technical
  model: gpt-5.4
  prompt_version: 2026-08-21.1
  generated_at: '2026-10-19T06:28:09+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://techcommunity.microsoft.com/t5/azure-integration-services-blog/deploying-logic-apps-hybrid-through-an-azure-devops-pipeline/ba-p/4556246
    title: Deploying Logic Apps Hybrid through an Azure DevOps pipeline
    published_date: '2026-10-19'
  - url: https://learn.microsoft.com/en-us/azure/container-apps/azure-arc-overview
    title: Container Apps on Azure Arc Overview | Microsoft Learn
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/container-apps/azure-arc-plan
    title: Plan a Container Apps deployment on Azure Arc-enabled Kubernetes | Microsoft
      Learn
    published_date: null
---

Si estás mirando Logic Apps Hybrid, seguramente ya has visto la promesa: seguir diseñando y operando flujos con la experiencia de Logic Apps, pero ejecutándolos en tu propia infraestructura. Lo interesante empieza cuando intentas llevar eso a un proceso serio de despliegue. Ahí es donde mucha gente se atasca, porque ya no estás en el camino conocido de App Service ni en un despliegue *cloud-only*. En este artículo te voy a enseñar **el camino práctico que yo seguiría hoy** para desplegar Logic Apps Hybrid con Azure DevOps sobre un clúster Kubernetes habilitado con Azure Arc.

La buena noticia es que, según el artículo de [despliegue de Logic Apps Hybrid con Azure DevOps en TechCommunity](https://techcommunity.microsoft.com/t5/azure-integration-services-blog/deploying-logic-apps-hybrid-through-an-azure-devops-pipeline/ba-p/4556246), la extensión Azure Logic Apps (Standard) para Visual Studio Code ya puede generar los artefactos de infraestructura y los pipelines base. La noticia realmente importante, al menos para mí, no es que "te lo genere". Es entender qué genera, qué tienes que tocar y por qué Hybrid cambia tres piezas que en un Logic Apps Standard en Azure solemos dar por supuestas: la autenticación de conexiones, el runtime y el mecanismo de publicación.

### Antes de empezar

Para que puedas reproducir este recorrido de principio a fin, yo partiría de estos prerrequisitos:

- **Azure CLI 2.75 o superior** instalada y autenticada.
- **Bicep CLI** integrada en Azure CLI (`az bicep version`).
- **Visual Studio Code** con la extensión **Azure Logic Apps (Standard)**.
- Un proyecto de **Logic Apps Standard** ya creado en local.
- Un clúster **Kubernetes Linux** ya conectado con **Azure Arc**.
- La cadena de dependencias de Azure Container Apps en Arc preparada: **connected cluster**, **cluster extension**, **custom location** y **connected environment**, tal como describe la [visión general de Azure Container Apps en Azure Arc](https://learn.microsoft.com/en-us/azure/container-apps/azure-arc-overview) y la guía para [planificar despliegues en producción](https://learn.microsoft.com/en-us/azure/container-apps/azure-arc-plan).
- Una organización y un proyecto en **Azure DevOps**.
- Permisos suficientes en Azure para desplegar recursos y en Azure DevOps para crear pipelines y service connections.
- Una aplicación de **Microsoft Entra ID** con `tenantId`, `clientId` y `clientSecret` para las conexiones Hybrid.

Además, conviene que tengas claros dos límites del modelo, porque luego aparecen como "errores raros" cuando en realidad no lo son. El primero es que en Arc el clúster lo operas tú: capacidad, red, parches y almacenamiento siguen siendo tu responsabilidad, tal y como deja claro la [documentación de Azure Container Apps en Azure Arc](https://learn.microsoft.com/en-us/azure/container-apps/azure-arc-overview). El segundo es que **no puedes apoyarte en managed identity dentro del runtime Hybrid** para las conexiones de Logic Apps, así que la autenticación cambia respecto a un Standard puramente en Azure.

### Qué cambia de verdad en Logic Apps Hybrid

Antes de hablar de YAML, yo necesito tener claro el modelo mental correcto. Un Logic App Hybrid se despliega como un recurso `Microsoft.App/containerApps` con `kind: workflowapp`, enlazado a una `custom location` de un clúster Arc. El contenido del workflow vive en un recurso compartido SMB montado en `/home/site/wwwroot`, y la publicación del paquete no va por el mecanismo clásico de App Service, sino por un **endpoint ZIP deploy** específico del runtime Hybrid.

Eso explica por qué el pipeline tiene dos preocupaciones completamente distintas. Por un lado, desplegar o actualizar la infraestructura Azure que representa tu entorno híbrido. Por otro, empaquetar la aplicación y enviarla al endpoint de despliegue usando un token *bearer* obtenido mediante *client credentials*. **Si mezclas ambas cosas sin entenderlas, el pipeline funciona “a veces”; si las separas bien, el despliegue se vuelve predecible**.

La otra diferencia importante está en las conexiones. El artículo de [TechCommunity sobre Logic Apps Hybrid y Azure DevOps](https://techcommunity.microsoft.com/t5/azure-integration-services-blog/deploying-logic-apps-hybrid-through-an-azure-devops-pipeline/ba-p/4556246) explica que el proceso de build reescribe autenticaciones `ManagedServiceIdentity` a `ActiveDirectoryOAuth`, apoyándose en variables de entorno del Container App. A mí esto me parece una decisión especialmente buena, porque permite reutilizar el mismo paquete entre entornos y mover la variación al plano de configuración. Dicho de otro modo: el ZIP no debería llevar secretos ni decisiones de entorno incrustadas. Y eso, en un escenario híbrido, vale oro.

### Paso 1: validar el entorno Arc y el connected environment

Yo no empezaría por el pipeline. Empezaría por comprobar que la base híbrida está sana. Si la cadena `connected cluster > cluster extension > custom location > connected environment` falla en cualquiera de sus eslabones, el despliegue posterior te va a devolver errores difíciles de interpretar. La propia [visión general de Azure Container Apps en Azure Arc](https://learn.microsoft.com/en-us/azure/container-apps/azure-arc-overview) insiste en ese orden de dependencia, y no es un detalle menor.

Este comando con **Azure CLI 2.75** te sirve para verificar el connected environment que usará el workflow Hybrid:

```bash
az containerapp connected-env show \
  --name cae-hybrid-prod \
  --resource-group rg-hybrid-integration \
  --query "{name:name,location:location,provisioningState:properties.provisioningState,customLocationId:properties.customLocation.id}" \
  --output yaml
```

La salida esperada debería mostrar algo parecido a esto:

```yaml
customLocationId: /subscriptions/11111111-2222-3333-4444-555555555555/resourceGroups/rg-hybrid-integration/providers/Microsoft.ExtendedLocation/customLocations/cl-hybrid-madrid
location: westeurope
name: cae-hybrid-prod
provisioningState: Succeeded
```

Si aquí no ves `Succeeded`, yo no seguiría. Primero revisaría extensión, custom location, red y almacenamiento. La guía para [planificar Azure Container Apps en Arc](https://learn.microsoft.com/en-us/azure/container-apps/azure-arc-plan) deja bastante claro que balanceo, DNS, conectividad saliente y *storage* no son "detalles operativos", sino parte de la disponibilidad real de la plataforma. Y sí, ya sé que esto suena menos glamuroso que hablar del workflow (a mí también me pasa), pero aquí está la mitad del éxito.

### Paso 2: definir la infraestructura del workflow Hybrid con Bicep

Aunque Visual Studio Code puede generarte la plantilla, me parece útil ver qué piezas hay detrás. El recurso principal es el Container App con `kind: workflowapp`, apuntando al connected environment y a la custom location. En un despliegue real, yo parametrizaría secretos y configuración por entorno desde el principio, aunque estés todavía en una prueba de concepto. Luego siempre cuesta más arreglarlo.

Este ejemplo resume la parte esencial de la infraestructura:

```bicep
param location string = 'westeurope'
param logicAppName string = 'la-hybrid-orders-prod'
param connectedEnvironmentId string
param aadTenantId string
param aadClientId string
@secure()
param aadClientSecret string

resource workflowApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: logicAppName
  location: location
  kind: 'workflowapp'
  properties: {
    managedEnvironmentId: connectedEnvironmentId
    configuration: {
      ingress: {
        external: false
        targetPort: 80
      }
      secrets: [
        {
          name: 'aad-client-secret'
          value: aadClientSecret
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'logicapp'
          image: 'mcr.microsoft.com/azure-logic-apps/logicapps-container:latest'
          env: [
            {
              name: 'WORKFLOWAPP_AAD_TENANTID'
              value: aadTenantId
            }
            {
              name: 'WORKFLOWAPP_AAD_CLIENTID'
              value: aadClientId
            }
            {
              name: 'WORKFLOWAPP_AAD_CLIENTSECRET'
              secretRef: 'aad-client-secret' // El runtime resuelve la autenticación desde configuración, no desde el paquete
            }
          ]
        }
      ]
    }
  }
}
```

Lo que yo comprobaría aquí no es solo que compile, sino que refleja el patrón correcto: **las credenciales se inyectan como configuración del runtime y no van embebidas en el paquete**. Ese detalle es el que hace posible reutilizar el mismo artefacto en desarrollo, preproducción y producción sin tener que regenerarlo cada vez.

Para validarlo, ejecutaría el despliegue en modo `what-if`:

```bash
az deployment group what-if \
  --resource-group rg-hybrid-integration \
  --template-file infra/main.bicep \
  --parameters \
    logicAppName=la-hybrid-orders-prod \
    connectedEnvironmentId="/subscriptions/11111111-2222-3333-4444-555555555555/resourceGroups/rg-hybrid-integration/providers/Microsoft.App/connectedEnvironments/cae-hybrid-prod" \
    aadTenantId="72f988bf-86f1-41af-91ab-2d7cd011db47" \
    aadClientId="8a34d52b-6d9d-4f4c-a0ac-5f3f3a8d2811" \
    aadClientSecret="S3cureHybridSecret-2026"
```

La salida esperada debe indicar cambios previstos sobre `Microsoft.App/containerApps/la-hybrid-orders-prod`. Si ves errores sobre `managedEnvironmentId`, normalmente la pista está en la base Arc y no en Bicep. Y esto, una vez más, es muy Hybrid: el fallo parece de infraestructura declarativa, pero muchas veces viene de una dependencia previa que no estaba realmente lista.

{{< figure src="/images/como-desplegar-logic-apps-hybrid-con-azure-devops-sin-pelearte-con-el-pipeline/body-2.png" alt="Diagrama del flujo de despliegue de Logic Apps Hybrid con Azure DevOps" caption="Flujo recomendado: validar plataforma, empaquetar la app, desplegar infraestructura y publicar el ZIP en el runtime Hybrid." >}}{{< /figure >}}

### Paso 3: preparar el pipeline de build en Azure DevOps

Aquí es donde el enfoque práctico de la extensión de Visual Studio Code ayuda bastante. Según el artículo de [TechCommunity](https://techcommunity.microsoft.com/t5/azure-integration-services-blog/deploying-logic-apps-hybrid-through-an-azure-devops-pipeline/ba-p/4556246), la extensión puede generarte tanto la plantilla como los pipelines. Aun así, yo te recomiendo revisar el YAML con calma para entender tres salidas concretas: el ZIP de la aplicación, la plantilla de infraestructura y el fichero de parámetros.

Este ejemplo de **Azure DevOps YAML** separa empaquetado y publicación de artefactos de forma bastante limpia:

```yaml
trigger:
- main

pool:
  vmImage: ubuntu-latest

stages:
- stage: Build
  displayName: Build Logic Apps Hybrid
  jobs:
  - job: Package
    steps:
    - task: ArchiveFiles@2
      displayName: Empaquetar workflow app
      inputs:
        rootFolderOrFile: '$(Build.SourcesDirectory)/src/Orders.Hybrid.LogicApp'
        includeRootFolder: false # Evita una carpeta raíz extra dentro del ZIP, que luego rompe la publicación
        archiveType: zip
        archiveFile: '$(Build.ArtifactStagingDirectory)/logicapp-hybrid.zip'
        replaceExistingArchive: true

    - task: CopyFiles@2
      displayName: Copiar plantillas de infraestructura
      inputs:
        SourceFolder: '$(Build.SourcesDirectory)/infra'
        Contents: |
          **/*.bicep
          **/*.json
        TargetFolder: '$(Build.ArtifactStagingDirectory)/infra'

    - task: PublishBuildArtifacts@1
      displayName: Publicar artefactos
      inputs:
        PathtoPublish: '$(Build.ArtifactStagingDirectory)'
        ArtifactName: 'drop'
        publishLocation: 'Container'
```

¿Qué deberías ver al finalizar? Un artefacto `drop` con `logicapp-hybrid.zip`, la carpeta `infra` y los ficheros necesarios para la release. Parece obvio, pero yo comprobaría el contenido del ZIP al menos una vez. Si lleva una carpeta raíz extra, el runtime luego no encontrará bien el contenido. Es el típico error tonto que te roba una mañana completa (o una tarde, si tienes mala suerte).

### Paso 4: desplegar infraestructura y publicar el paquete Hybrid

La release tiene dos tareas naturales. Primero, desplegar la infraestructura con Azure Resource Manager o Bicep. Después, publicar el paquete al endpoint Hybrid. El punto clave aquí es que el despliegue del contenido **no usa publicación de App Service**, sino el endpoint ZIP deploy autenticado con *bearer token*, tal y como explica el artículo de [despliegue de Logic Apps Hybrid con Azure DevOps](https://techcommunity.microsoft.com/t5/azure-integration-services-blog/deploying-logic-apps-hybrid-through-an-azure-devops-pipeline/ba-p/4556246).

Yo lo estructuraría así en Azure DevOps:

```yaml
stages:
- stage: Release
  displayName: Deploy Hybrid Logic App
  jobs:
  - deployment: DeployToProd
    environment: hybrid-prod
    strategy:
      runOnce:
        deploy:
          steps:
          - download: current
            artifact: drop

          - task: AzureCLI@2
            displayName: Desplegar infraestructura con Azure CLI 2.75
            inputs:
              azureSubscription: 'sc-azure-rg-hybrid'
              scriptType: bash
              scriptLocation: inlineScript
              inlineScript: |
                set -euo pipefail

                az deployment group create \
                  --resource-group rg-hybrid-integration \
                  --template-file $(Pipeline.Workspace)/drop/infra/main.bicep \
                  --parameters @$(Pipeline.Workspace)/drop/infra/prod.parameters.json

          - task: AzureCLI@2
            displayName: Publicar ZIP al runtime Hybrid
            inputs:
              azureSubscription: 'sc-azure-rg-hybrid'
              scriptType: bash
              scriptLocation: inlineScript
              inlineScript: |
                set -euo pipefail

                DEPLOY_URL="https://la-hybrid-orders-prod.zipdeploy.hostruntime.contoso/api/zipdeploy"
                TOKEN=$(curl -sS -X POST \
                  -H "Content-Type: application/x-www-form-urlencoded" \
                  -d "client_id=$(hybridClientId)&client_secret=$(hybridClientSecret)&scope=https%3A%2F%2Fmanagement.core.windows.net%2F.default&grant_type=client_credentials" \
                  "https://login.microsoftonline.com/$(hybridTenantId)/oauth2/v2.0/token" | jq -er '.access_token')

                curl -sS --fail-with-body -X POST "$DEPLOY_URL" \
                  -H "Authorization: Bearer $TOKEN" \
                  -H "Content-Type: application/zip" \
                  --data-binary @$(Pipeline.Workspace)/drop/logicapp-hybrid.zip
```

Aquí hay dos matices importantes. El primero es que estoy mostrando el patrón de autenticación que describe la fuente: *client credentials* contra Entra ID y luego ZIP deploy. El segundo es que la URL exacta del endpoint y las tareas especializadas pueden venir de la extensión de Azure DevOps que menciona el artículo; si la tienes disponible, yo la prefiero, porque encapsula parte de la complejidad específica de Hybrid y reduce superficie de error.

La verificación esperada tras el despliegue es doble:

1. El comando `az deployment group create` debe devolver `provisioningState: Succeeded`.
2. La llamada al endpoint ZIP deploy debe responder con estado `200` o `202`, según la implementación del endpoint.

No tiene mucho misterio, pero sí tiene una consecuencia importante: si falla la segunda parte, **tu infraestructura puede estar perfecta y tu aplicación seguir sin publicar**. Por eso a mí me gusta tratar ambas fases como responsabilidades distintas y observables por separado.

{{< figure src="/images/como-desplegar-logic-apps-hybrid-con-azure-devops-sin-pelearte-con-el-pipeline/body-3.png" alt="Secuencia de autenticación y ZIP deploy para Logic Apps Hybrid" caption="La publicación del paquete Hybrid pasa por token de Entra ID y endpoint ZIP deploy, no por el modelo clásico de App Service." >}}{{< /figure >}}

### Paso 5: comprobar que la app arrancó y que la configuración se resolvió

Una vez desplegado, yo comprobaría que el runtime ha recibido la configuración esperada y que el contenedor está estable. En Hybrid esto importa más, porque el problema puede estar en Azure, en la extensión Arc, en la red o en el clúster. Vamos, que el radio de búsqueda crece bastante.

Con **Azure CLI 2.75**, puedes revisar el estado del Container App así:

```bash
az containerapp show \
  --name la-hybrid-orders-prod \
  --resource-group rg-hybrid-integration \
  --query "{name:name,kind:kind,latestRevisionName:properties.latestRevisionName,runningStatus:properties.runningStatus}" \
  --output table
```

La salida esperada debería indicar que el recurso existe como workflow app y está en ejecución:

```text
Kind         LatestRevisionName                     Name                        RunningStatus
-----------  ------------------------------------  --------------------------  -------------
workflowapp  la-hybrid-orders-prod--0000012        la-hybrid-orders-prod       Running
```

Si no arranca, yo revisaría en este orden: secretos, variables `WORKFLOWAPP_AAD_*`, acceso al *storage* montado y conectividad saliente. **En Hybrid, muchas incidencias “de aplicación” son en realidad incidencias de plataforma**. Y asumir eso pronto te ahorra bastante frustración.

### Qué me llevaría a producción y qué no

Si esto fuera un laboratorio, con lo anterior ya tendrías un flujo reproducible. Si me preguntas qué haría antes de llevarlo a producción, tengo bastante clara la lista:

- Separar pipelines de **build** y **release** con aprobaciones por entorno.
- Guardar secretos solo en mecanismos seguros de Azure DevOps o, mejor aún, en un *vault* integrado con el pipeline.
- Añadir validaciones previas del connected environment y del estado del clúster.
- Versionar explícitamente plantillas, parámetros y paquete ZIP en cada release.
- Definir *rollback* operativo, aunque sea manual, porque en híbrido la frontera entre plataforma y aplicación exige más disciplina.

La guía para [planificar Azure Container Apps en Azure Arc para producción](https://learn.microsoft.com/en-us/azure/container-apps/azure-arc-plan) insiste mucho en capacidad, red, certificados, DNS, *logging* y *upgrades*. Y me parece acertado. El éxito de Logic Apps Hybrid no depende solo del workflow, sino de que **tu plataforma Kubernetes esté tratada como producto**, no como una base improvisada para “que corra algo”.

### Mi conclusión

Yo veo Logic Apps Hybrid como una opción muy potente cuando quieres el modelo de diseño y gobierno de Logic Apps, pero el runtime debe quedarse cerca de tus sistemas, tus datos o tus restricciones operativas. La parte difícil no es crear el workflow; la parte difícil es industrializar el despliegue. Y precisamente por eso el soporte de generación de artefactos y pipelines que describe [Microsoft en TechCommunity](https://techcommunity.microsoft.com/t5/azure-integration-services-blog/deploying-logic-apps-hybrid-through-an-azure-devops-pipeline/ba-p/4556246) me parece tan valioso.

Si yo tuviera que resumirlo en una sola idea, sería esta: **trata Logic Apps Hybrid como una combinación de integración, plataforma y entrega continua**, no como un simple “publish” más. En cuanto haces ese cambio mental, Azure DevOps deja de ser un obstáculo y pasa a ser la pieza que te da repetibilidad, trazabilidad y control.

Si tú estás montando ahora mismo ese camino, yo empezaría exactamente por aquí: validar Arc, separar infraestructura de paquete, automatizar el ZIP deploy y comprobar cada paso con salidas verificables. No hay magia. Pero sí hay un orden correcto. Y en Hybrid, ese orden lo es casi todo.
