---
title: 'Runners efímeros y seguros de GitHub Actions en Azure Container Apps: mi patrón
  práctico'
date: '2026-11-02T06:21:12+00:00'
draft: true
slug: runners-efimeros-y-seguros-de-github-actions-en-azure-container-apps-mi-patron-p
description: Te enseño un patrón reproducible para ejecutar runners self-hosted de
  GitHub Actions en Azure Container Apps, con escala a cero, OIDC y secretos privados.
categories:
- Azure
- Arquitectura de Software
- DevOps
tags:
- GitHub Actions
- Azure Container Apps
- KEDA
- Key Vault
- OIDC
- Platform Engineering
image: /images/runners-efimeros-y-seguros-de-github-actions-en-azure-container-apps-mi-patron-p/cover.png
comments: true
ai:
  assisted: true
  article_type: technical
  model: gpt-5.4
  prompt_version: 2026-08-21.1
  generated_at: '2026-11-02T06:21:12+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://techcommunity.microsoft.com/t5/azure-infrastructure-blog/building-secure-ephemeral-github-actions-runners-on-azure/ba-p/4569209
    title: Building Secure, Ephemeral GitHub Actions Runners on Azure Container Apps
    published_date: '2026-11-01'
  - url: https://learn.microsoft.com/en-gb/azure/azure-arc/servers/automatic-agent-upgrade
    title: Automatically upgrade the Azure Connected Machine agent - Azure Arc | Microsoft
      Learn
    published_date: null
---

Si alguna vez has intentado llevar workflows de GitHub Actions a una red privada, con herramientas corporativas o con un perímetro algo más serio, seguramente has acabado mirando los *self-hosted runners*. Y ahí es justo donde, en mi experiencia, empieza la parte fea: máquinas virtuales siempre encendidas, coste en vacío, parcheo, secretos demasiado cerca del runtime y una superficie de ataque mayor de la que parece a simple vista. Yo llevo tiempo dándole vueltas a una idea muy concreta: **el runner ideal no se administra**. Aparece, ejecuta un único trabajo y desaparece.

Ese patrón encaja sorprendentemente bien con Azure Container Apps Jobs, KEDA, autenticación con GitHub App, Key Vault privado y despliegues a Azure con OIDC, tal como se explica en esta [arquitectura práctica de runners efímeros en Azure Container Apps](https://techcommunity.microsoft.com/t5/azure-infrastructure-blog/building-secure-ephemeral-github-actions-runners-on-azure/ba-p/4569209). Y eso es justo lo que quiero aterrizar aquí: no una demo bonita para una presentación, sino un enfoque que yo consideraría razonable para platform engineering de verdad.

Mi objetivo en este artículo es muy sencillo. Quiero enseñarte cómo montaría yo el contenedor, cómo lo conectaría con GitHub sin PATs, cómo sacaría los secretos desde Key Vault con identidad administrada y cómo permitiría que el workflow desplegara en Azure sin credenciales largas. Porque, al final, lo importante no es solo que funcione: **lo importante es que nazca ya con menos deuda operativa**.

### Qué patrón estoy construyendo exactamente

La idea de base es bastante directa. Un workflow entra en cola en GitHub, KEDA detecta que hay trabajo para un runner con una etiqueta concreta, Azure Container Apps Event Job levanta un contenedor, ese contenedor recupera el material de la GitHub App desde Key Vault, genera credenciales de corta duración, registra un runner efímero a nivel de repositorio, ejecuta un único job y termina. Si no hay más cola, todo vuelve a cero.

Lo interesante aquí no es solo la secuencia, sino el reparto de confianza. GitHub se encarga de detectar y despachar trabajo. Azure Container Apps fija el límite de ejecución. Key Vault conserva el material sensible. La identidad administrada del job lee esos secretos sin meter claves en la imagen. Y el propio workflow, si necesita tocar Azure, usa [GitHub OIDC con federación en Entra ID](https://techcommunity.microsoft.com/t5/azure-infrastructure-blog/building-secure-ephemeral-github-actions-runners-on-azure/ba-p/4569209) en lugar de vivir atado a un secreto eterno. A mí, sinceramente, me parece un reparto bastante sano.

{{< figure src="/images/runners-efimeros-y-seguros-de-github-actions-en-azure-container-apps-mi-patron-p/body-1.png" alt="Diagrama de arquitectura de runners efímeros en Azure Container Apps" caption="Arquitectura de extremo a extremo: GitHub Actions encola trabajo, KEDA activa el Event Job, el runner obtiene secretos desde Key Vault y el workflow usa OIDC para Azure." >}}{{< /figure >}}

### Antes de empezar

Si quieres reproducirlo, yo partiría de estos prerrequisitos concretos:

- **Azure CLI 2.75 o superior** con la extensión `containerapp` instalada.
- **GitHub CLI 2.x** opcional, pero útil para validar el repositorio y los workflows.
- Una **suscripción de Azure** donde puedas crear:
  - Resource Group
  - Azure Container Apps Environment
  - Azure Key Vault
  - User Assigned Managed Identity
  - Microsoft Entra App Registration para la federación OIDC
- Permisos suficientes en Azure para asignar RBAC y crear *federated credentials*.
- Un **repositorio de GitHub** en el que puedas crear una **GitHub App** instalada en ese repositorio.
- Una imagen de runner basada en el runner oficial de GitHub o compatible, publicada en un registro accesible por Container Apps.

Además, conviene que tengas a mano estos valores reales:

- `GitHub App ID`
- `GitHub App Installation ID`
- Clave privada PEM de la GitHub App
- Nombre del `owner` y del `repo`
- Etiqueta del runner, por ejemplo `aca-ephemeral`

### Paso 1: crear la base en Azure para el job efímero

Yo prefiero separar desde el principio el entorno de ejecución, la identidad y el almacén de secretos. Es una manía mía, sí, pero una de las útiles. Empiezo creando el grupo de recursos, Log Analytics, el entorno de Container Apps, el Key Vault y una identidad administrada de usuario.

```bash
# Azure CLI 2.75+
set -euo pipefail

RG="rg-gha-runners-we"
LOC="westeurope"
LAW="log-gha-runners-we"
ENV="acae-gha-runners-we"
KV="kvgharunnerswe01"
IDENTITY="uami-gha-runner"

az group create --name "$RG" --location "$LOC"
az monitor log-analytics workspace create --resource-group "$RG" --workspace-name "$LAW" --location "$LOC"

LAW_ID=$(az monitor log-analytics workspace show \
  --resource-group "$RG" \
  --workspace-name "$LAW" \
  --query customerId -o tsv)

LAW_KEY=$(az monitor log-analytics workspace get-shared-keys \
  --resource-group "$RG" \
  --workspace-name "$LAW" \
  --query primarySharedKey -o tsv)

az containerapp env create \
  --name "$ENV" \
  --resource-group "$RG" \
  --location "$LOC" \
  --logs-workspace-id "$LAW_ID" \
  --logs-workspace-key "$LAW_KEY"

az identity create --name "$IDENTITY" --resource-group "$RG" --location "$LOC"
az keyvault create --name "$KV" --resource-group "$RG" --location "$LOC" --enable-rbac-authorization true
```

Lo esperable aquí es ver `Succeeded` en el `provisioningState` del entorno de Container Apps, de la identidad y del Key Vault. Si algo falla en esta fase, yo no seguiría adelante “a ver si luego se arregla” (spoiler: no suele hacerlo).

Ahora asigno a la identidad permiso para leer secretos en Key Vault:

```bash
# Azure CLI 2.75+
PRINCIPAL_ID=$(az identity show --name "$IDENTITY" --resource-group "$RG" --query principalId -o tsv)
KV_ID=$(az keyvault show --name "$KV" --resource-group "$RG" --query id -o tsv)

az role assignment create \
  --assignee-object-id "$PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal \
  --role "Key Vault Secrets User" \
  --scope "$KV_ID"
```

La salida debería devolverte una asignación RBAC válida sobre el scope del Key Vault. No tiene más épica que esa, pero es un punto importante: el contenedor no necesita conocer secretos previos para poder arrancar y recuperar lo que necesita.

### Paso 2: guardar el material sensible en Key Vault, no en la imagen

Según la [guía de referencia de esta arquitectura](https://techcommunity.microsoft.com/t5/azure-infrastructure-blog/building-secure-ephemeral-github-actions-runners-on-azure/ba-p/4569209), el contenedor arranca, accede a Key Vault de forma privada y recupera el material de la GitHub App para generar credenciales de corta duración. A nivel práctico, yo guardaría tres secretos: `github-app-id`, `github-app-installation-id` y `github-app-private-key`.

```bash
# Azure CLI 2.75+
az keyvault secret set --vault-name "$KV" --name github-app-id --value "1234567"
az keyvault secret set --vault-name "$KV" --name github-app-installation-id --value "7654321"
az keyvault secret set --vault-name "$KV" --name github-app-private-key --file ./github-app-private-key.pem
```

Cada comando debería devolverte el `id` del secreto y `attributes.enabled` a `true`. Hasta aquí, nada especialmente exótico. Pero sí quiero insistir en una idea que para mí cambia bastante el diseño: **si el runner vive minutos, tus secretos no deberían vivir cómodamente pegados a la imagen durante meses**.

En un entorno productivo, yo endurecería esto más: *private endpoint* para Key Vault, DNS privado y restricciones de red. No lo desarrollo aquí porque me desviaría del hilo principal, pero me parece un matiz importante. El patrón no gana solo por ser efímero; gana cuando la efimeridad se acompaña de límites claros alrededor de los secretos.

{{< figure src="/images/runners-efimeros-y-seguros-de-github-actions-en-azure-container-apps-mi-patron-p/body-2.png" alt="Flujo de acceso privado a Key Vault desde el runner" caption="Secuencia de arranque del runner: identidad administrada, lectura de secretos desde Key Vault y registro efímero en GitHub." >}}{{< /figure >}}

### Paso 3: preparar el contenedor del runner para registro efímero

Aquí está uno de los puntos donde más merece la pena ser explícito. El contenedor no debería quedarse esperando trabajos indefinidamente. Tiene que registrarse como runner efímero, atender un solo job y salir. Para eso, la imagen necesita el runner de GitHub y un *entrypoint* que obtenga secretos desde Key Vault usando la identidad administrada disponible dentro del contenedor.

Este ejemplo usa `curl`, el endpoint de identidad administrada y la API de Key Vault. He endurecido un poco el script para que falle rápido, valide respuestas y no siga adelante con valores vacíos. Porque sí, el script de ejemplo “bonito” funciona en una diapositiva; el que detecta estados rotos es el que quiero en producción.

```bash
#!/usr/bin/env bash
# entrypoint.sh - imagen Linux del runner
set -euo pipefail

KV_NAME="kvgharunnerswe01"
REPO_URL="https://github.com/codertectura/platform-runners"
RUNNER_NAME="aca-runner-$(hostname)"
LABELS="aca-ephemeral"

require_env() {
  local name="$1"
  [[ -n "${!name:-}" ]] || { echo "Falta la variable $name" >&2; exit 1; }
}

get_kv_secret() {
  local secret_name="$1"
  curl -fsS \
    -H "Authorization: Bearer ${MI_TOKEN}" \
    "https://${KV_NAME}.vault.azure.net/secrets/${secret_name}?api-version=7.4" | jq -er '.value'
}

require_env IDENTITY_ENDPOINT
require_env IDENTITY_HEADER

MI_TOKEN=$(curl -fsS \
  -H "X-IDENTITY-HEADER: ${IDENTITY_HEADER}" \
  "${IDENTITY_ENDPOINT}?resource=https://vault.azure.net&api-version=2019-08-01" | jq -er '.access_token')

GITHUB_APP_ID=$(get_kv_secret github-app-id)
GITHUB_INSTALLATION_ID=$(get_kv_secret github-app-installation-id)
GITHUB_APP_PRIVATE_KEY=$(get_kv_secret github-app-private-key)

pem_file=$(mktemp)
trap 'rm -f "$pem_file"' EXIT
printf '%s' "$GITHUB_APP_PRIVATE_KEY" > "$pem_file"

# Esta línea es la clave: el token de registro se genera en runtime y dura poco.
REGISTRATION_TOKEN=$(./get-token.sh "$GITHUB_APP_ID" "$GITHUB_INSTALLATION_ID" "$pem_file")

./config.sh \
  --url "$REPO_URL" \
  --token "$REGISTRATION_TOKEN" \
  --name "$RUNNER_NAME" \
  --labels "$LABELS" \
  --ephemeral \
  --unattended

exec ./run.sh
```

¿Qué deberías ver en los logs? Recuperación correcta de secretos, registro del runner, ejecución del job y salida del proceso al terminar. **Y como puedes apreciar, no hay magia**: solo una secuencia de confianza bastante mejor repartida.

No he metido aquí la implementación completa de `get-token.sh`, porque depende de cómo empaquetes OpenSSL, `jq` y la llamada a GitHub. Pero el patrón de seguridad no cambia: el material sensible vive en Key Vault, el acceso se hace con identidad administrada y el token final de runner es efímero.

### Paso 4: crear el Container Apps Job con escala desde cero y KEDA

La [arquitectura publicada en Azure Tech Community](https://techcommunity.microsoft.com/t5/azure-infrastructure-blog/building-secure-ephemeral-github-actions-runners-on-azure/ba-p/4569209) se apoya en un Event Job de Azure Container Apps y en el escalador `github-runner` de KEDA. Esa combinación es la que permite que solo haya ejecución cuando realmente existe un workflow en cola con la etiqueta adecuada.

El siguiente ejemplo crea el job y le asocia la identidad administrada. Aquí la clave no es tanto el contenedor en sí como el hecho de que el job nazca ya con `Event` y con mínimo de ejecuciones a cero.

```bash
# Azure CLI 2.75+ con extensión containerapp
ENV="acae-gha-runners-we"
JOB="job-gha-runner"
IDENTITY_ID=$(az identity show --name "$IDENTITY" --resource-group "$RG" --query id -o tsv)

az containerapp job create \
  --name "$JOB" \
  --resource-group "$RG" \
  --environment "$ENV" \
  --trigger-type Event \
  --replica-timeout 3600 \
  --replica-retry-limit 1 \
  --parallelism 1 \
  --replica-completion-count 1 \
  --min-executions 0 \
  --max-executions 5 \
  --image mcr.microsoft.com/azurelinux/base/core:latest \
  --cpu 1.0 \
  --memory 2Gi \
  --user-assigned "$IDENTITY_ID"
```

La salida debería reflejar `triggerType: Event` y `minExecutions: 0`. Para mí, esa es la pista de que de verdad estás construyendo algo que puede volver a dormir cuando no hay trabajo.

Después, la configuración más fina del *scaler* suele quedar mejor en YAML. Yo la prefiero así porque puedo versionar la intención de plataforma sin esconderla detrás de demasiados parámetros de CLI.

```yaml
properties:
  configuration:
    triggerType: Event
    replicaRetryLimit: 1
    replicaTimeout: 3600
    eventTriggerConfig:
      scale:
        minExecutions: 0
        maxExecutions: 5
        pollingInterval: 30
        rules:
          - name: github-runner-queue
            type: github-runner
            metadata:
              owner: codertectura
              runnerScope: repo
              repos: platform-runners
              labels: aca-ephemeral
              targetWorkflowQueueLength: "1"
```

¿Qué verificaría yo? Que el escalado está realmente asociado a la cola del repositorio y a la etiqueta `aca-ephemeral`. Si lanzas un workflow con `runs-on: [self-hosted, aca-ephemeral]`, deberías ver cómo aparece una ejecución del job cuando KEDA detecta cola.

{{< figure src="/images/runners-efimeros-y-seguros-de-github-actions-en-azure-container-apps-mi-patron-p/body-3.png" alt="Esquema de escalado con KEDA para runners de GitHub" caption="KEDA activa ejecuciones del job solo cuando detecta trabajos en cola con la etiqueta configurada, y vuelve a cero cuando desaparece la demanda." >}}{{< /figure >}}

### Paso 5: evitar credenciales largas en el workflow con GitHub OIDC

Para mí, aquí está la diferencia entre “esto funciona” y “esto está bien diseñado”. Si el workflow que corre dentro del runner necesita desplegar en Azure, yo no quiero un secreto estático guardado en GitHub. Quiero OIDC y federación con Entra ID, justo como recomienda el patrón de referencia al hablar de [despliegue a Azure sin secretos persistentes](https://techcommunity.microsoft.com/t5/azure-infrastructure-blog/building-secure-ephemeral-github-actions-runners-on-azure/ba-p/4569209).

Primero creo la aplicación de Entra y su *service principal*:

```bash
# Azure CLI 2.75+
APP_NAME="gha-oidc-deployer"
APP_ID=$(az ad app create --display-name "$APP_NAME" --query appId -o tsv)
az ad sp create --id "$APP_ID"
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

az role assignment create \
  --assignee "$APP_ID" \
  --role Contributor \
  --scope "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RG}"
```

La salida debería mostrar el `appId` creado y una asignación RBAC sobre tu resource group. A partir de ahí, añado la credencial federada para un repositorio y rama concretos.

```bash
# Azure CLI 2.75+
cat > federated-credential.json <<'JSON'
{
  "name": "main-branch",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:codertectura/platform-runners:ref:refs/heads/main",
  "description": "GitHub Actions main branch",
  "audiences": [
    "api://AzureADTokenExchange"
  ]
}
JSON

OBJECT_ID=$(az ad app show --id "$APP_ID" --query id -o tsv)
az ad app federated-credential create --id "$OBJECT_ID" --parameters @federated-credential.json
```

Lo importante aquí es que el `issuer` sea el de GitHub Actions y que el `subject` coincida exactamente con el repositorio y la rama que quieres autorizar. Si eso no casa, luego llegan los errores de autenticación “misteriosos” que en realidad no tienen nada de misterioso.

Y este sería el workflow mínimo para autenticar contra Azure desde el runner efímero:

```yaml
name: deploy-infra

on:
  workflow_dispatch:

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: [self-hosted, aca-ephemeral]
    steps:
      - uses: actions/checkout@v4

      - name: Login en Azure con OIDC
        uses: azure/login@v2
        with:
          client-id: 11111111-2222-3333-4444-555555555555
          tenant-id: 00000000-1111-2222-3333-444444444444
          subscription-id: 99999999-8888-7777-6666-555555555555

      - name: Verificar identidad
        run: az account show --output table
```

Cuando este job corra bien, `azure/login` obtendrá el token sin secretos almacenados en GitHub y `az account show` devolverá la suscripción autenticada. Y eso, aunque suene pequeño, es uno de esos cambios que merecen mucho la pena.

### Cómo verifico que de verdad es efímero

Aquí yo no me conformaría con que el workflow termine correctamente. Comprobaría, como mínimo, estas tres cosas:

1. En GitHub, el runner aparece asociado al repositorio solo durante la ejecución.
2. En Azure Container Apps Jobs, se crea una ejecución por job y luego finaliza.
3. No quedan réplicas en marcha cuando la cola vuelve a cero.

Ese último punto es crucial. **Si el runner sigue vivo después del trabajo, ya no tienes un patrón efímero**; tienes un servidor disfrazado de contenedor. Y eso cambia completamente la conversación de coste, seguridad y operaciones.

### Lo que más me gusta de este diseño, y lo que vigilaría

Lo que más valor le veo a este enfoque es la combinación de aislamiento y elasticidad. Ganas acceso a red privada, herramientas corporativas y control del perímetro, pero sin arrastrar automáticamente el modelo clásico de “VM por runner”. Además, el uso de autenticación con GitHub App mejora claramente frente a PATs, porque trabajas con credenciales de vida corta y con un alcance más definido, tal como subraya la [implementación de referencia sobre Azure Container Apps y KEDA](https://techcommunity.microsoft.com/t5/azure-infrastructure-blog/building-secure-ephemeral-github-actions-runners-on-azure/ba-p/4569209).

Ahora bien, tampoco lo vendería como una panacea. Hay varias cosas que yo vigilaría desde el minuto uno. La primera es el tiempo de arranque del contenedor: si metes demasiadas herramientas en runtime, cada ejecución se convierte en una pequeña penalización. La segunda es la observabilidad: necesitas logs lo bastante claros como para distinguir entre un fallo al registrar el runner, un fallo al leer Key Vault o un fallo del propio workflow. Y la tercera es el scope. Yo empezaría con runners a nivel de repositorio, no de organización, salvo que tengas muy claro el modelo de gobierno.

### Mi recomendación final

Si me preguntas por una hoja de ruta sensata, yo iría así: primero probaría este patrón en un único repositorio, con una sola etiqueta de runner y con despliegues acotados a un resource group mediante OIDC. Después endurecería red y Key Vault. Y solo entonces escalaría a varios equipos o varios repositorios.

Porque la clave aquí no es simplemente “mover runners a contenedores”. La clave es cambiar el contrato operativo. El runner deja de ser una mascota persistente y pasa a ser **una unidad de ejecución desechable, auditable y de confianza mínima**. En mi experiencia, ese cambio vale bastante más que cualquier ahorro puntual de infraestructura.
