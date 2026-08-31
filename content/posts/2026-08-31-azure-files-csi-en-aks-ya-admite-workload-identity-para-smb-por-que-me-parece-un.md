---
title: 'Azure Files CSI en AKS ya admite Workload Identity para SMB: por qué me parece
  un cambio importante'
date: '2026-08-31T12:47:37+00:00'
draft: true
slug: azure-files-csi-en-aks-ya-admite-workload-identity-para-smb-por-que-me-parece-un
description: Te muestro qué cambia al montar Azure Files por SMB en AKS con Workload
  Identity a nivel de pod. Para mí, es un salto claro en aislamiento y permisos mínimos.
categories:
- Azure
- Arquitectura de Software
tags:
- AKS
- Azure Files
- Workload Identity
- Kubernetes
- Seguridad
- CSI
image: /images/azure-files-csi-en-aks-ya-admite-workload-identity-para-smb-por-que-me-parece-un/cover.png
comments: true
ai:
  assisted: true
  article_type: technical
  model: gpt-5.4
  prompt_version: 2026-08-21.1
  generated_at: '2026-08-31T12:47:37+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://azure.microsoft.com/updates?id=570120
    title: '[Launched] Generally Available: Workload identity support for Azure Files
      CSI driver (SMB) in Azure'
    published_date: '2026-08-28'
  - url: https://learn.microsoft.com/en-us/azure/aks/csi-storage-drivers
    title: Use Container Storage Interface (CSI) Drivers on Azure Kubernetes Service
      (AKS) - Azure Kubernetes Service | Microsoft Learn
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/aks/workload-identity-deploy-cluster
    title: Deploy and Configure an Azure Kubernetes Service (AKS) Cluster with Microsoft
      Entra Workload ID - Azure Kubernetes Service | Microsoft Learn
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/aks/create-volume-azure-files
    title: Create and Manage Persistent Volumes with Azure Files in Azure Kubernetes
      Service (AKS) - Azure Kubernetes Service | Microsoft Learn
    published_date: null
---

Si trabajas con AKS y Azure Files, esta es una de esas novedades que, al menos para mí, **sí cambian una decisión de arquitectura** y no solo una casilla más del portal. Según el anuncio de disponibilidad general de [Workload identity support for Azure Files CSI driver (SMB)](https://azure.microsoft.com/updates?id=570120), ahora ya puedo autenticar un montaje SMB de Azure Files a nivel de pod en AKS, en lugar de depender de la identidad del nodo. Dicho así suena pequeño. En un clúster compartido, no lo es.

Hasta ahora, el patrón habitual con Azure Files en AKS me dejaba una sensación incómoda: demasiada dependencia del host o de credenciales con más alcance del que me gustaría tolerar. La guía de [Azure Files en AKS](https://learn.microsoft.com/en-us/azure/aks/create-volume-azure-files) venía reflejando históricamente ese contexto alrededor de SMB y autenticación basada en clave. Lo relevante ahora es el cambio de centro de gravedad: el acceso deja de vivir “cerca del nodo” y pasa a vivir “cerca del workload”. Y eso, en seguridad y en operación, importa bastante más de lo que parece a primera vista.

{{< figure src="/images/azure-files-csi-en-aks-ya-admite-workload-identity-para-smb-por-que-me-parece-un/body-1.png" alt="Diagrama de autenticación de Azure Files SMB con Workload Identity en AKS" caption="Paso conceptual clave: el pod obtiene identidad propia y el montaje SMB deja de depender de la identidad del nodo." >}}{{< /figure >}}

### Qué cambia realmente

La frase clave del anuncio no es solo que “soporta Workload Identity”, sino que habilita *pod-level authentication to SMB file shares*. Es decir: el flujo encaja con [Microsoft Entra Workload ID en AKS](https://learn.microsoft.com/en-us/azure/aks/workload-identity-deploy-cluster), donde el clúster expone un *issuer* OIDC, una `ServiceAccount` de Kubernetes se asocia a una identidad administrada y el workload obtiene tokens federados sin tener secretos persistidos en el manifiesto.

A mí esto me interesa por dos motivos muy concretos. El primero es el aislamiento: si la aplicación A necesita acceder a un recurso compartido y la B no, ya no tengo que asumir una identidad de nodo con permisos demasiado amplios para las dos. El segundo es la trazabilidad: cuando reviso permisos, asignaciones y responsabilidades, **veo una identidad asociada al workload que realmente consume el recurso**, no una identidad difusa del clúster que termina representando demasiado.

Además, este movimiento encaja con la dirección general que Azure lleva tiempo marcando. La documentación de [CSI storage drivers en AKS](https://learn.microsoft.com/en-us/azure/aks/csi-storage-drivers) deja bastante claro que el presente pasa por CSI frente a los *in-tree drivers*, y que el modelo moderno separa mejor almacenamiento, cómputo e identidad. Dicho de otra forma: menos acoplamiento implícito, más piezas explícitas. Yo, personalmente, compro esa idea sin demasiada resistencia.

### Antes de empezar

Si quieres reproducirlo de extremo a extremo, yo prepararía esto antes de tocar nada:

- Una suscripción de Azure activa.
- [Azure CLI 2.47.0 o superior](https://learn.microsoft.com/en-us/azure/aks/workload-identity-deploy-cluster). Yo asumiría 2.75 o superior para evitar sorpresas tontas.
- `Kubectl` instalado y apuntando a tu contexto correcto (sí, parece obvio; sí, me ha pasado más veces de las que me gusta admitir).
- Permisos para crear recursos en Azure y para hacer asignaciones de rol sobre la cuenta de almacenamiento.
- Un clúster AKS con *issuer* OIDC y Workload Identity habilitados, como describe [la guía de despliegue de Workload Identity en AKS](https://learn.microsoft.com/en-us/azure/aks/workload-identity-deploy-cluster).
- El driver [Azure Files CSI en AKS](https://learn.microsoft.com/en-us/azure/aks/csi-storage-drivers) habilitado.
- Una cuenta de almacenamiento y un recurso compartido de Azure Files accesible por SMB.

Para que el flujo sea reproducible, voy a usar estos nombres:

- Grupo de recursos: `rg-aks-files-wi`
- Clúster: `aks-files-wi-demo`
- Región: `westeurope`
- Cuenta de almacenamiento: `stfileswidemo01`
- File share: `teamdocs`
- Namespace: `apps`
- Service account: `files-wi-sa`
- Identidad administrada: `mi-aks-files-smb`

### Paso 1: crear AKS con OIDC y Workload Identity

Si arrancas desde cero, el primer paso es crear el clúster con OIDC y Workload Identity activados, exactamente en la línea de lo que explica [AKS con Microsoft Entra Workload ID](https://learn.microsoft.com/en-us/azure/aks/workload-identity-deploy-cluster).

```bash
# Azure CLI 2.75+
set -euo pipefail

RG="rg-aks-files-wi"
AKS_NAME="aks-files-wi-demo"
LOCATION="westeurope"

az group create \
  --name "$RG" \
  --location "$LOCATION"

az aks create \
  --resource-group "$RG" \
  --name "$AKS_NAME" \
  --location "$LOCATION" \
  --node-count 2 \
  --generate-ssh-keys \
  --enable-oidc-issuer \
  --enable-workload-identity

az aks get-credentials \
  --resource-group "$RG" \
  --name "$AKS_NAME" \
  --overwrite-existing
```

La salida esperada es la creación correcta del grupo y del clúster y, al final, algo parecido a `Merged "aks-files-wi-demo" as current context`.

Después yo comprobaría que el clúster quedó realmente preparado para federación. No por paranoia (bueno, un poco sí), sino porque aquí merece la pena fallar pronto.

```bash
# Azure CLI 2.75+
az aks show \
  --resource-group "$RG" \
  --name "$AKS_NAME" \
  --query "{oidcIssuer:oidcIssuerProfile.issuerUrl,workloadIdentity:securityProfile.workloadIdentity.enabled}" \
  -o json
```

La salida debería parecerse a esto:

```json
{
  "oidcIssuer": "https://westeurope.oic.prod-aks.azure.com/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/",
  "workloadIdentity": true
}
```

Si `workloadIdentity` sale a `true` y recibes una URL de *issuer*, vas por buen camino.

{{< figure src="/images/azure-files-csi-en-aks-ya-admite-workload-identity-para-smb-por-que-me-parece-un/body-2.png" alt="Flujo de configuración de AKS, identidad federada y permisos para Azure Files" caption="Configuración mínima para reproducir el escenario: AKS con OIDC, identidad administrada, credencial federada y rol sobre la cuenta de almacenamiento." >}}{{< /figure >}}

### Paso 2: crear almacenamiento, identidad y permisos

Ahora necesito tres piezas: la cuenta de almacenamiento con su `file share`, una identidad administrada y la federación entre esa identidad y la `ServiceAccount` que usará el pod.

```bash
# Azure CLI 2.75+
STORAGE_ACCOUNT="stfileswidemo01"
FILE_SHARE="teamdocs"
IDENTITY_NAME="mi-aks-files-smb"

az storage account create \
  --name "$STORAGE_ACCOUNT" \
  --resource-group "$RG" \
  --location "$LOCATION" \
  --sku Standard_LRS \
  --kind StorageV2

az storage share-rm create \
  --resource-group "$RG" \
  --storage-account "$STORAGE_ACCOUNT" \
  --name "$FILE_SHARE" \
  --quota 100

az identity create \
  --name "$IDENTITY_NAME" \
  --resource-group "$RG" \
  --location "$LOCATION"
```

La salida esperada incluye el `id`, `clientId` y `principalId` de la identidad administrada, además de la creación correcta del recurso compartido `teamdocs`.

Después recupero los valores que voy a reutilizar. Aquí yo no seguiría si alguna variable sale vacía; es la típica señal de que algo ya va torcido y te ahorras depurar media hora después.

```bash
# Azure CLI 2.75+
AKS_OIDC_ISSUER=$(az aks show \
  --resource-group "$RG" \
  --name "$AKS_NAME" \
  --query oidcIssuerProfile.issuerUrl -o tsv)

IDENTITY_CLIENT_ID=$(az identity show \
  --name "$IDENTITY_NAME" \
  --resource-group "$RG" \
  --query clientId -o tsv)

IDENTITY_PRINCIPAL_ID=$(az identity show \
  --name "$IDENTITY_NAME" \
  --resource-group "$RG" \
  --query principalId -o tsv)

STORAGE_ID=$(az storage account show \
  --name "$STORAGE_ACCOUNT" \
  --resource-group "$RG" \
  --query id -o tsv)

[ -n "$AKS_OIDC_ISSUER" ] && [ -n "$IDENTITY_CLIENT_ID" ] && [ -n "$IDENTITY_PRINCIPAL_ID" ] && [ -n "$STORAGE_ID" ] \
  || { echo "Faltan valores necesarios para continuar" >&2; exit 1; } # mejor cortar aquí que perseguir errores de autenticación después
```

Ahora creo el `namespace` y la `ServiceAccount`, anotando esta última con el `clientId` de la identidad administrada.

```bash
# kubectl 1.30+
kubectl create namespace apps --dry-run=client -o yaml | kubectl apply -f -

kubectl apply -f - <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: files-wi-sa
  namespace: apps
  annotations:
    azure.workload.identity/client-id: ${IDENTITY_CLIENT_ID} # esta anotación conecta la SA con la identidad federada que usará el pod
EOF
```

Y ahora creo la credencial federada que vincula esa `ServiceAccount` con la identidad:

```bash
# Azure CLI 2.75+
az identity federated-credential create \
  --name fic-files-wi-sa \
  --identity-name "$IDENTITY_NAME" \
  --resource-group "$RG" \
  --issuer "$AKS_OIDC_ISSUER" \
  --subject system:serviceaccount:apps:files-wi-sa \
  --audience api://AzureADTokenExchange
```

La salida esperada es un documento JSON con el nombre `fic-files-wi-sa`, lo que confirma que la federación existe.

Por último, asigno permisos sobre la cuenta de almacenamiento. Aquí la clave conceptual no es memorizar el rol, sino entender la intención: la identidad del workload necesita acceso al `file share`; los nodos del clúster, no necesariamente.

```bash
# Azure CLI 2.75+
az role assignment create \
  --assignee-object-id "$IDENTITY_PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal \
  --role "Storage File Data SMB Share Contributor" \
  --scope "$STORAGE_ID"
```

La salida debería incluir `Storage File Data SMB Share Contributor` como `roleDefinitionName`.

### Paso 3: crear el PVC y el pod con Workload Identity

Aquí es donde para mí se ve el cambio de verdad. Voy a crear un `PersistentVolumeClaim` usando Azure Files CSI y, después, un pod que se ejecuta con la `ServiceAccount` federada. La guía de [Azure Files en AKS](https://learn.microsoft.com/en-us/azure/aks/create-volume-azure-files) explica el uso de PV y PVC con `file.csi.azure.com`; yo lo aterrizo al escenario de Workload Identity para SMB.

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: azurefiles-pvc
  namespace: apps
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: azurefile-csi
  resources:
    requests:
      storage: 20Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: smb-wi-test
  namespace: apps
  labels:
    azure.workload.identity/use: "true"
spec:
  serviceAccountName: files-wi-sa
  containers:
    - name: app
      image: mcr.microsoft.com/oss/nginx/nginx:1.25.5
      command:
        - /bin/sh
        - -c
        - |
          set -eu
          echo "montaje con workload identity" > /mnt/files/health.txt
          test -s /mnt/files/health.txt # compruebo escritura real en el share, no solo que el directorio exista
          ls -la /mnt/files
          sleep 3600
      volumeMounts:
        - name: azurefiles
          mountPath: /mnt/files
  volumes:
    - name: azurefiles
      persistentVolumeClaim:
        claimName: azurefiles-pvc
```

Aplícalo así:

```bash
# kubectl 1.30+
kubectl apply -f azurefiles-workload-identity.yaml
kubectl get pvc,pod -n apps -w
```

La salida esperada es que el PVC pase a `Bound` y el pod a `Running`. Si el pod se queda en `ContainerCreating`, yo empezaría por revisar eventos y permisos antes de tocar nada más. En este tipo de escenarios, el problema suele estar antes en identidad o autorización que en Kubernetes “puro”.

### Paso 4: verificar que el montaje funciona

Cuando el pod ya está arriba, yo comprobaría dos cosas: que el volumen está montado y que el workload puede escribir realmente en el share.

```bash
# kubectl 1.30+
kubectl exec -n apps smb-wi-test -- \
  sh -c 'mount | grep /mnt/files && test -s /mnt/files/health.txt && cat /mnt/files/health.txt && ls -la /mnt/files'
```

La salida esperada debería mostrar una línea del sistema de ficheros montado sobre `/mnt/files`, el contenido `montaje con workload identity` y el archivo `health.txt` listado en el directorio.

Si quieres una comprobación adicional, inspecciona la `ServiceAccount` y el pod:

```bash
# kubectl 1.30+
kubectl get sa files-wi-sa -n apps -o yaml
kubectl describe pod smb-wi-test -n apps
```

Ahí deberías ver la anotación `azure.workload.identity/client-id` en la `ServiceAccount` y el pod asociado a `files-wi-sa`.

{{< figure src="/images/azure-files-csi-en-aks-ya-admite-workload-identity-para-smb-por-que-me-parece-un/body-3.png" alt="Comparativa entre identidad de nodo e identidad de workload para Azure Files en AKS" caption="La diferencia importante no es el volumen, sino quién se autentica para montarlo y con qué alcance de permisos." >}}{{< /figure >}}

### Comparativa rápida: identidad del nodo vs identidad del workload

Yo lo resumiría así, sin demasiado teatro:

- **Antes**: el acceso al share tendía a apoyarse en identidad del nodo o en credenciales con alcance amplio.
- **Ahora**: el acceso puede quedar ligado a la `ServiceAccount` y a la identidad federada del pod.
- **Antes**: separar permisos por aplicación era más incómodo y menos natural.
- **Ahora**: cada despliegue puede tener su propia identidad y su propia asignación de rol.
- **Antes**: en un clúster multi-tenant, un error de diseño podía salpicar a varios equipos con bastante facilidad.
- **Ahora**: el aislamiento es más razonable y también más fácil de auditar.

No digo que esto elimine toda la complejidad, porque no sería verdad. Sigues teniendo que diseñar bien `namespaces`, RBAC, `StorageClass` y permisos sobre la cuenta de almacenamiento. Pero **el modelo encaja bastante mejor con Kubernetes moderno**: identidad declarativa, federación OIDC y privilegios más cerca del principio de mínimo acceso.

### Qué revisaría antes de moverlo a producción

Aquí yo sería especialmente meticuloso.

Primero, revisaría qué aplicaciones comparten un mismo recurso SMB y cuáles deberían tener recursos distintos. La novedad mejora la autenticación, sí, pero no convierte mágicamente en buena idea compartir un volumen entre workloads que no deberían verse entre sí. Una mala frontera lógica sigue siendo una mala frontera lógica, por mucho OIDC que le pongas alrededor.

Segundo, limpiaría permisos heredados. Si activas Workload Identity pero mantienes asignaciones amplias en identidades de nodo, te queda un sistema más moderno por arriba y demasiado permisivo por abajo. Para mí, el valor real aparece cuando **retiro privilegios innecesarios del plano de cómputo** y los llevo al plano del workload, que es donde deberían haber estado desde el principio.

Tercero, probaría eventos reales de vida del clúster: reinicio de pod, reprogramación en otro nodo, escalado y recreación del despliegue. La documentación de [Azure Files con AKS](https://learn.microsoft.com/en-us/azure/aks/create-volume-azure-files) recuerda precisamente que Azure Files está pensado para persistencia compartida y para sobrevivir a reinicios, fallos de nodo y escalado. Yo en producción no me conformaría con que funcione una vez; querría que siguiera funcionando cuando Kubernetes haga cosas de Kubernetes (que, como sabes, a veces son muy educativas).

{{< figure src="/images/azure-files-csi-en-aks-ya-admite-workload-identity-para-smb-por-que-me-parece-un/body-4.png" alt="Checklist visual de endurecimiento para llevar Azure Files con Workload Identity a producción" caption="Antes de pasar a producción, yo revisaría permisos heredados, separación de shares, namespaces y comportamiento ante reprogramación." >}}{{< /figure >}}

### Mi conclusión

Este soporte general disponible me parece una mejora de esas que no hacen demasiado ruido, pero corrigen una incomodidad real de diseño. El anuncio de [GA para Workload Identity en Azure Files CSI driver (SMB)](https://azure.microsoft.com/updates?id=570120) acerca Azure Files en AKS al modelo que yo espero hoy de una plataforma *cloud-native*: el pod se identifica como workload, no como una sombra del nodo donde le ha tocado caer.

Si tu clúster AKS lo comparten varios equipos, o si te preocupa de verdad el aislamiento entre aplicaciones, yo le daría prioridad. No porque sea una moda de seguridad (ya tenemos suficientes modas en tecnología, gracias), sino porque **reduce acoplamiento entre almacenamiento y cómputo** y deja una arquitectura bastante más limpia. Y cuando una mejora de seguridad además simplifica el razonamiento operativo, a mí me cuesta mucho no prestarle atención.
