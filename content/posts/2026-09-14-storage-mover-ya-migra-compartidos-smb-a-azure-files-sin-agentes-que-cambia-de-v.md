---
title: 'Storage Mover ya migra compartidos SMB a Azure Files sin agentes: lo que cambia
  de verdad'
date: '2026-09-14T12:01:12+00:00'
draft: true
slug: storage-mover-ya-migra-compartidos-smb-a-azure-files-sin-agentes-que-cambia-de-v
description: Azure Storage Mover añade migración sin agentes para compartidos SMB
  hacia Azure Files. Te cuento qué cambia de verdad, cómo prepararlo y qué validaría
  yo antes del corte.
categories:
- Azure
- Infraestructura
- Arquitectura de Software
tags:
- Azure Storage Mover
- Azure Files
- SMB
- Migración
- Windows Server
image: /images/storage-mover-ya-migra-compartidos-smb-a-azure-files-sin-agentes-que-cambia-de-v/cover.png
comments: true
ai:
  assisted: true
  article_type: technical
  model: gpt-5.4
  prompt_version: 2026-08-21.1
  generated_at: '2026-09-14T12:01:12+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://azure.microsoft.com/updates?id=570910
    title: '[In preview] Public Preview: Agentless migration of on-premises SMB file
      shares to Azure Files (SMB)'
    published_date: '2026-09-11'
  - url: https://learn.microsoft.com/en-us/azure/storage/files/storage-files-introduction
    title: What is Azure Files? | Microsoft Learn
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/storage/files/storage-files-migration-overview
    title: Migration Overview for SMB Azure File Shares | Microsoft Learn
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/storage/files/migrate-files-storage-mover
    title: Migrate to Azure Files using Azure Storage Mover | Microsoft Learn
    published_date: null
---

Si llevas tiempo moviendo cargas de ficheros a Azure, esta novedad merece una pausa. Según [el anuncio de Azure](https://azure.microsoft.com/updates?id=570910), «Azure Storage Mover» ya soporta la migración sin agentes de compartidos SMB *on-premises* a Azure Files en vista previa pública. Y a mí lo que me interesa no es solo el titular, sino el cambio operativo que hay debajo.

Hasta ahora, hablar de «Storage Mover» para Azure Files solía empujarte a desplegar y mantener agentes cerca del origen. Eso no era necesariamente dramático, pero sí añadía una capa de trabajo bastante poco glamurosa: aprovisionar una VM, abrir conectividad, registrar el agente, vigilarlo, parchearlo y retirarlo después. Ahora aparece una ruta más simple para ciertos escenarios SMB, justo donde muchos equipos de infraestructura quieren reducir fricción, ventanas de mantenimiento y puntos de fallo.

La idea de este artículo es muy práctica: te voy a contar **qué problema resuelve de verdad**, dónde encaja frente a otras opciones, cómo prepararía yo una migración sensata y qué comprobaría antes de dar por bueno el corte. Porque en migraciones de ficheros el drama nunca está en la diapositiva; suele aparecer el lunes siguiente, cuando alguien intenta abrir su carpeta y ya no puede 😅

### Qué aporta exactamente esta novedad

Según [la actualización oficial del servicio](https://azure.microsoft.com/updates?id=570910), Storage Mover permite ahora migrar de forma *agentless* compartidos SMB locales hacia Azure Files. Traducido a lenguaje de operación diaria: puedes mover datos desde Windows Server o desde determinados NAS expuestos por SMB a Azure sin desplegar, registrar ni mantener un agente de migración en el origen.

Eso cambia bastante el coste real de la migración. No tanto por la copia en sí, sino por todo lo que la rodea. Cuando eliminas una pieza temporal de infraestructura, eliminas también parte de la coordinación entre redes, sistemas y operaciones. **Y menos piezas temporales suelen significar menos sorpresas**. No siempre, claro. Pero bastante menos.

Ahora bien, tampoco me parece buena idea idealizarlo. Que sea sin agentes no significa que desaparezcan mágicamente los requisitos de red, permisos o diseño del destino. [Azure Files](https://learn.microsoft.com/en-us/azure/storage/files/storage-files-introduction) sigue siendo un servicio de compartidos totalmente gestionado con acceso mediante SMB y NFS, y la migración sigue persiguiendo lo de siempre: mover contenido con la máxima fidelidad posible y con la menor indisponibilidad razonable.

{{< figure src="/images/storage-mover-ya-migra-compartidos-smb-a-azure-files-sin-agentes-que-cambia-de-v/body-1.png" alt="Diagrama comparando migración con agente y sin agente" caption="Comparativa visual entre el enfoque tradicional con agente y la nueva migración SMB sin agentes hacia Azure Files." >}}{{< /figure >}}

### Dónde encaja frente a otras rutas de migración

Si te vas a [la visión general de migración a compartidos SMB de Azure Files](https://learn.microsoft.com/en-us/azure/storage/files/storage-files-migration-overview), Microsoft insiste en dos ideas que a mí me parecen las correctas: preservar la fidelidad de los archivos y minimizar el *downtime*. Para decidir herramienta, yo empezaría exactamente ahí y no en el nombre del producto de moda.

Si tu escenario es una migración como tal y no quieres mantener caché local ni una convivencia híbrida a largo plazo, [Storage Mover para Azure Files](https://learn.microsoft.com/en-us/azure/storage/files/migrate-files-storage-mover) encaja muy bien. Si en cambio tu estrategia es híbrida y quieres seguir presentando el *namespace* local con caché caliente en oficina o CPD, entonces Azure File Sync sigue teniendo muchísimo sentido.

Mi lectura es bastante simple: **la novedad agentless reduce la fricción del “lift-and-shift” de file shares**, pero no reemplaza todas las estrategias híbridas. Si tu objetivo final es jubilar servidores de ficheros *on-premises* y quedarte con un servicio gestionado, esta capacidad te acerca bastante a ese destino.

{{< figure src="/images/storage-mover-ya-migra-compartidos-smb-a-azure-files-sin-agentes-que-cambia-de-v/source-2.png" alt="Diagrama de decisiones para migrar compartidos SMB a Azure Files" caption="Resumen visual de rutas de migración SMB hacia Azure Files según el origen y el enfoque de despliegue. Fuente: [learn.microsoft.com](https://learn.microsoft.com/en-us/azure/storage/files/storage-files-migration-overview)" >}}{{< /figure >}}

### Antes de empezar

Para plantear una migración como Dios manda (o, siendo más realistas, como la agenda y la red te dejen), yo partiría de estos prerrequisitos:

- Suscripción de Azure activa.
- Un grupo de recursos ya decidido para el proyecto.
- Una cuenta de almacenamiento con soporte para Azure Files y un compartido SMB de destino.
- Acceso de lectura al compartido SMB de origen.
- Permisos suficientes en Azure para crear o administrar recursos de Storage y Azure Files.
- Una decisión previa sobre identidad y acceso en el destino, porque eso condiciona cómo validarás permisos después.
- Conectividad de red correcta entre el origen y Azure, incluyendo los *endpoints* que correspondan.
- [Azure CLI 2.75 o superior](https://learn.microsoft.com/en-us/azure/storage/files/storage-files-introduction), que es la versión que asumo en los ejemplos.

Además, yo prepararía una muestra de datos realista antes del primer pase. Nada de una carpeta vacía con tres PDFs. Me refiero a carpetas con ACL distintas, ficheros antiguos, un árbol de directorios algo profundo y al menos una ruta sensible en la que se note enseguida si los permisos no cuadran. Ese pequeño laboratorio te ahorra muchas conclusiones falsas.

### Paso 1: preparar bien el destino en Azure Files

Aunque el foco esté en Storage Mover, el primer error habitual aparece bastante antes: un destino mal planteado. [Azure Files](https://learn.microsoft.com/en-us/azure/storage/files/storage-files-introduction) está pensado para compartir almacenamiento gestionado en la nube mediante protocolos estándar, así que yo empezaría creando una cuenta de almacenamiento dedicada al caso de uso y un file share con nombre estable, capacidad razonable y propósito claro.

Este ejemplo usa Azure CLI 2.75 y crea una cuenta de almacenamiento Standard con *large file shares* habilitado, además de un compartido SMB de 2 TiB:

```bash
# Azure CLI 2.75+
az group create \
  --name rg-storagemover-demo \
  --location westeurope

az storage account create \
  --name stcodermoverdemo01 \
  --resource-group rg-storagemover-demo \
  --location westeurope \
  --sku Standard_LRS \
  --kind StorageV2 \
  --enable-large-file-share true # Lo fijo de forma explícita para evitar depender de defaults o del contexto

az storage share-rm create \
  --resource-group rg-storagemover-demo \
  --storage-account stcodermoverdemo01 \
  --name corpfiles \
  --quota 2048 \
  --enabled-protocols SMB
```

La salida esperada es simple: los tres comandos deben terminar correctamente y el último debe devolverte el recurso del compartido. Si quieres comprobarlo de forma explícita, yo haría una consulta reducida a los campos que de verdad me interesan:

```bash
# Azure CLI 2.75+
az storage share-rm show \
  --resource-group rg-storagemover-demo \
  --storage-account stcodermoverdemo01 \
  --name corpfiles \
  --query "{name:name,protocol:enabledProtocols,quota:shareQuota}" \
  --output json
```

Y deberías ver algo equivalente a esto:

```json
{
  "name": "corpfiles",
  "protocol": "SMB",
  "quota": 2048
}
```

Parece un paso muy básico, pero aquí se evitan dos clásicos: lanzar una migración contra una cuenta improvisada y descubrir demasiado tarde que ni el *naming*, ni la capacidad ni el modelo de acceso encajan con producción.

### Paso 2: pensar la migración como dos copias y un corte

Si lees [la guía de migración SMB a Azure Files](https://learn.microsoft.com/en-us/azure/storage/files/storage-files-migration-overview), verás que el objetivo no es “copiar archivos” sin más. El objetivo es preservar datos y metadatos con una indisponibilidad mínima. Yo lo traduzco a un patrón muy sencillo:

1. Copia inicial amplia.
2. Copia incremental corta.
3. Corte controlado de escritura y validación final.

Ésa es, para mí, la forma sana de pensar una migración de este tipo. No como un gran evento mágico, sino como una secuencia controlada de aproximaciones. La parte interesante del modo *agentless* no es solo que quite un agente; es que hace más asumible ese patrón en entornos donde cada componente adicional complica la coordinación entre equipos.

{{< figure src="/images/storage-mover-ya-migra-compartidos-smb-a-azure-files-sin-agentes-que-cambia-de-v/body-3.png" alt="Esquema de fidelidad de archivos en una migración SMB" caption="Lo que conviene validar antes del corte: contenido, metadatos, ACL y marcas temporales." >}}{{< /figure >}}

### Paso 3: validar fidelidad de archivos y ACL antes del corte

Microsoft remarca en [su documentación sobre migración](https://learn.microsoft.com/en-us/azure/storage/files/storage-files-migration-overview) que la fidelidad del archivo importa: flujo de datos, atributos, permisos NTFS/ACL y marcas temporales, siempre dentro de lo que el destino soporta. También advierte de matices como los *alternate data streams*, que no se almacenan igual en Azure file shares. Y aquí es donde yo me pongo especialmente pesado.

Porque una migración puede “terminar” y aun así no estar bien. **Fin de copia no equivale a validación**. Si puedes montar el compartido SMB de Azure Files en un servidor Windows de validación, una comprobación comparativa te da mucha más tranquilidad que cualquier barra de progreso.

Este script en PowerShell 7.4 revisa una ruta concreta, compara número de archivos, tamaño total y una referencia temporal útil para detectar desviaciones obvias:

```powershell
# PowerShell 7.4
$sourcePath = "\\fs01\departamentos\finanzas"
$targetPath = "\\stcodermoverdemo01.file.core.windows.net\corpfiles\finanzas"

$sourceItems = Get-ChildItem -Path $sourcePath -Recurse -File -Force |
    Select-Object FullName, Length, CreationTimeUtc, LastWriteTimeUtc

$targetItems = Get-ChildItem -Path $targetPath -Recurse -File -Force |
    Select-Object FullName, Length, CreationTimeUtc, LastWriteTimeUtc

$sourceAcl = Get-Acl -Path $sourcePath
$targetAcl = Get-Acl -Path $targetPath

[pscustomobject]@{
    SourceFiles        = $sourceItems.Count
    TargetFiles        = $targetItems.Count
    SourceBytes        = ($sourceItems | Measure-Object -Property Length -Sum).Sum
    TargetBytes        = ($targetItems | Measure-Object -Property Length -Sum).Sum
    SourceAclEntries   = $sourceAcl.Access.Count
    TargetAclEntries   = $targetAcl.Access.Count
    SourceLastWriteUtc = ($sourceItems | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1).LastWriteTimeUtc
    TargetLastWriteUtc = ($targetItems | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1).LastWriteTimeUtc
}
```

¿Qué esperaría yo aquí? Recuentos idénticos o, como mínimo, una explicación muy clara de cualquier diferencia. Si el número de archivos, el volumen total o las ACL no cuadran, yo no seguiría al corte hasta entender el motivo. No me vale el clásico “seguro que luego aparece”.

Para una validación más precisa de ACL en una carpeta sensible, puedes comparar las reglas normalizadas a texto para detectar diferencias reales y no ruido de formato:

```powershell
# PowerShell 7.4
$sourceAclRules = (Get-Acl "\\fs01\departamentos\finanzas").Access |
    Select-Object IdentityReference, FileSystemRights, AccessControlType, IsInherited |
    Sort-Object IdentityReference, FileSystemRights, AccessControlType, IsInherited

$targetAclRules = (Get-Acl "\\stcodermoverdemo01.file.core.windows.net\corpfiles\finanzas").Access |
    Select-Object IdentityReference, FileSystemRights, AccessControlType, IsInherited |
    Sort-Object IdentityReference, FileSystemRights, AccessControlType, IsInherited

Compare-Object -ReferenceObject $sourceAclRules -DifferenceObject $targetAclRules
```

La salida esperada aquí es todavía más contundente: ninguna diferencia. Si PowerShell no devuelve filas, al menos para esa ruta concreta tienes una señal bastante buena.

### Paso 4: checklist de cutover con downtime mínimo

La parte delicada no suele ser copiar terabytes. Suele ser decidir cuándo paras escrituras y cuándo cambias a usuarios o aplicaciones al nuevo recurso compartido. Yo me llevaría este pequeño checklist operativo:

- Congelar cambios en el compartido origen durante la ventana acordada.
- Ejecutar la pasada incremental final en Storage Mover.
- Verificar recuento de ficheros y una muestra de ACL en carpetas críticas.
- Confirmar acceso al compartido de Azure Files desde un cliente representativo.
- Actualizar scripts de inicio de sesión, GPO, DFS Namespace o configuración de la aplicación para apuntar al nuevo destino.
- Mantener el origen en modo solo lectura durante un periodo corto de seguridad.

Si quieres comprobar desde línea de comandos que el nuevo compartido responde bien desde un cliente Windows, este ejemplo en PowerShell 7.4 monta el share y valida una carpeta concreta:

```powershell
# PowerShell 7.4
$accountName = "stcodermoverdemo01"
$shareName = "corpfiles"
$driveLetter = "Z"
$storageKey = (Get-AzStorageAccountKey -ResourceGroupName "rg-storagemover-demo" -Name $accountName)[0].Value

cmd.exe /c "cmdkey /add:$accountName.file.core.windows.net /user:Azure\$accountName /pass:$storageKey"

if (-not (Get-PSDrive -Name $driveLetter -ErrorAction SilentlyContinue)) {
    New-PSDrive -Name $driveLetter -PSProvider FileSystem -Root "\\$accountName.file.core.windows.net\$shareName" -Persist | Out-Null
}

Get-ChildItem "$($driveLetter):\finanzas" -Force |
    Select-Object Name, Length, LastWriteTime
```

Si el montaje falla o la carpeta no devuelve lo esperado, para mí el mensaje es clarísimo: todavía no estás en condiciones de dar por bueno el corte. Y sí, a veces esa conclusión fastidia la ventana de mantenimiento. Pero bastante más fastidia abrir producción con dudas.

### Lo que yo vigilaría especialmente en esta preview

Como esto está en [vista previa pública](https://azure.microsoft.com/updates?id=570910), yo sería prudente en tres frentes.

El primero es el alcance real del escenario *agentless*: tipos de origen SMB soportados, limitaciones regionales, requisitos de red y posibles diferencias frente al modo tradicional con agente. El segundo es la autenticación del destino, porque [Azure Files](https://learn.microsoft.com/en-us/azure/storage/files/storage-files-introduction) puede trabajar con distintos modelos de acceso y eso afecta directamente a la experiencia postmigración. El tercero es la validación de metadatos especiales y casos límite, porque una *preview* puede cubrir muy bien el camino principal y aún tener bordes por pulir.

Dicho eso, **la dirección del producto me parece la correcta**. Menos infraestructura temporal, menos fricción para mover file shares clásicos y una historia mucho más limpia para equipos que quieren modernizar sin convertir una migración en un proyecto paralelo de plataforma.

### Mi conclusión

Yo veo esta capacidad de migración SMB *agentless* hacia Azure Files como una mejora muy práctica, no como simple marketing. Encaja especialmente bien en equipos que quieren retirar servidores de ficheros *on-premises* sin añadir más piezas de las necesarias. Si tu objetivo es pasar de un compartido SMB tradicional a un servicio gestionado como [Azure Files](https://learn.microsoft.com/en-us/azure/storage/files/storage-files-introduction), esta novedad reduce bastante la complejidad operativa del trayecto.

Mi recomendación es muy concreta: pruébalo primero con un compartido acotado pero realista, valida permisos y tiempos de corte, y usa esa experiencia para decidir si escalas. En migraciones de ficheros, la herramienta importa, sí. Pero lo que de verdad marca la diferencia es otra cosa: que después del cambio todo siga funcionando como si nada. Y eso, en infraestructura, casi siempre es la mejor señal posible.
