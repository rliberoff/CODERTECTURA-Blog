---
title: Azure Backup ya permite recuperar archivos en VMs con Premium SSDv2 y Ultra
  Disk
date: '2026-10-26T06:35:21+00:00'
draft: true
slug: azure-backup-ya-cubre-la-recuperacion-a-nivel-de-archivo-en-vms-con-premium-ssdv
description: 'Azure Backup elimina una limitación muy concreta: ya puedes hacer item-level
  recovery en VMs con Premium SSDv2 y Ultra Disk. Te explico qué cambia de verdad
  y cómo lo validaría yo.'
categories:
- Azure
- Arquitectura de Software
- Infraestructura
tags:
- Azure Backup
- Máquinas virtuales
- Premium SSDv2
- Ultra Disk
- Recuperación
- Operaciones
image: /images/azure-backup-ya-cubre-la-recuperacion-a-nivel-de-archivo-en-vms-con-premium-ssdv/cover.png
comments: true
ai:
  assisted: true
  article_type: technical
  model: gpt-5.4
  prompt_version: 2026-08-21.1
  generated_at: '2026-10-26T06:35:21+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://azure.microsoft.com/updates?id=577963
    title: '[Launched] Generally Available: Item Level Recovery for Azure VMs with
      Premium SSDv2 and Ultra Disks in Azure Backup'
    published_date: '2026-10-23'
  - url: https://learn.microsoft.com/en-us/azure/backup/backup-azure-postgresql-flex-server-elastic-cluster-v2-overview
    title: About Azure Backup for PostgreSQL flexible server and elastic cluster (v2)
      - Azure Backup | Microsoft Learn
    published_date: null
---

Si operas máquinas virtuales en Azure y ya habías dado el salto a **Premium SSDv2** o **Ultra Disk**, seguramente te sonaba esta pequeña-gran molestia: tenías copia de seguridad de la VM, sí, pero la recuperación granular de archivos no estaba al mismo nivel que en escenarios más clásicos. Eso ya no es así. Según el anuncio de [disponibilidad general de Azure Backup](https://azure.microsoft.com/updates?id=577963), ahora hay soporte de **Item-Level Recovery (ILR)** para VMs que usan Premium SSDv2 y Ultra Disk, tanto con sector lógico de **512 bytes** como de **4 KB**.

A mí aquí no me interesa tanto el titular bonito como la consecuencia práctica. Lo importante de verdad es que desaparece una brecha operativa bastante incómoda: cuando alguien te pide recuperar una carpeta, un script, un certificado o un fichero de configuración, ya no tienes que asumir de entrada una restauración más pesada o una maniobra alternativa. **La capacidad existe, sí; pero lo que realmente cambia es el procedimiento diario**. Y eso, cuando hay una incidencia de verdad, importa mucho más que cualquier matriz de compatibilidad.

En este artículo te voy a enseñar cómo enfocaría yo una prueba realista para validar esta novedad: qué comprobaría primero, cómo verificaría el tamaño de sector lógico y qué dejaría documentado en un *recovery drill* para no depender de la memoria de nadie cuando llegue el día malo.

### Qué cambia realmente para operaciones

Cuando aparece una capacidad nueva en Azure, es muy fácil quedarse en la lectura superficial de “ah, ahora también soporta esto”. Yo intento no quedarme ahí. En un equipo de operaciones, el valor no está en sumar una casilla más en el portal, sino en reducir fricción en tareas que antes obligaban a improvisar o a sobrerreaccionar.

Hasta ahora, si una VM crítica sobre Premium SSDv2 o Ultra Disk necesitaba recuperar un único archivo, el camino mental del operador podía torcerse rápido: restaurar discos completos, montar pasos adicionales, asumir más tiempo del necesario o simplemente evitar el ejercicio porque era demasiado aparatoso para una petición pequeña. Eso no es una limitación teórica; es una de esas cosas que degradan procesos poco a poco hasta que un día te explotan en producción.

Con este cambio, la conversación deja de ser “puedo restaurar la VM” y pasa a ser “puedo recuperar exactamente lo que necesito”. Parece un matiz, pero no lo es. **Reducir el alcance de una recuperación también reduce el riesgo operativo**: menos pasos, menos superficie para equivocarte y menos tentación de aplicar atajos raros cuando vas con prisa.

Además, el anuncio de [Azure Backup para ILR en Premium SSDv2 y Ultra Disk](https://azure.microsoft.com/updates?id=577963) menciona explícitamente el soporte para sectores lógicos de **512 bytes y 4 KB**. Ese detalle técnico no está ahí de adorno. Si yo tuviera que validar esta mejora en una plataforma corporativa, ese sería uno de mis primeros puntos de control, precisamente porque este tipo de diferencias lleva años dando guerra en compatibilidades, rendimiento y comportamiento de ciertas cargas.

{{< figure src="/images/azure-backup-ya-cubre-la-recuperacion-a-nivel-de-archivo-en-vms-con-premium-ssdv/body-1.png" alt="Diagrama del flujo de recuperación a nivel de archivo en Azure Backup" caption="Flujo conceptual de ILR: VM protegida, recovery point, montaje temporal y copia del archivo recuperado." >}}{{< /figure >}}

### Antes de empezar

Si quieres reproducir una prueba como esta, yo partiría de unos prerequisitos bastante simples, pero no negociables:

- Una suscripción de Azure con permisos suficientes sobre la VM, el Recovery Services vault y los recursos de backup.
- Una VM ya desplegada con **Premium SSDv2** o **Ultra Disk**.
- Azure CLI **2.75 o superior** instalada y autenticada.
- Azure PowerShell **Az 14.x o superior** si vas a apoyarte en PowerShell para inspección o automatización.
- Un **Recovery Services vault** ya creado y compatible con tu escenario.
- La VM registrada y protegida por Azure Backup.
- Acceso al sistema operativo invitado para crear un archivo de prueba y validar la recuperación.
- En Linux, permisos de superusuario si vas a usar el flujo de ILR basado en script y montaje temporal.

Mi recomendación aquí es sencilla: no hagas la prueba sobre cualquier VM “porque está a mano”. Hazla sobre una VM que represente tu realidad. Mismo tipo de disco, mismo sistema operativo y, si puedes, la misma política de backup que usarías en producción. Si ensayas sobre un entorno que no se parece al real, luego llegan las sorpresas (y esas siempre llegan en el peor momento).

### Paso 1: validar el tipo de discos y preparar un archivo de prueba

Antes de hablar de restauración, yo confirmaría que la VM está de verdad en el escenario que quiero validar. Con Azure CLI puedes inspeccionar su perfil de almacenamiento y ver los tipos de disco conectados:

```bash
# Azure CLI 2.75+
az vm show \
  --resource-group rg-backup-lab \
  --name vm-linux-restore-01 \
  --query "{vm:name, osDisk:storageProfile.osDisk.managedDisk.storageAccountType, dataDisks:storageProfile.dataDisks[].managedDisk.storageAccountType}" \
  --output json
```

La salida esperada será algo parecido a esto:

```json
{
  "dataDisks": [
    "PremiumV2_LRS"
  ],
  "osDisk": "Premium_LRS",
  "vm": "vm-linux-restore-01"
}
```

En este ejemplo, el disco de datos usa Premium SSDv2. Si tu escenario es Ultra Disk, verás el tipo correspondiente en la salida. Lo relevante no es el comando en sí, sino confirmar que estás probando exactamente el almacenamiento que te preocupa. Si no haces ese check al principio, todo lo demás pierde valor.

Después, yo crearía dentro de la VM un archivo de prueba fácil de identificar y fácil de verificar. No hace falta construir un laboratorio barroco: necesitas algo que puedas recuperar y contrastar sin ambigüedades.

```bash
# Ejecutado dentro de la VM Linux
sudo install -d -m 0750 /data/restore-demo
printf 'ILR validation %s\n' "$(date -Iseconds)" | sudo tee /data/restore-demo/appsettings.backup-test.txt >/dev/null
sudo sha256sum /data/restore-demo/appsettings.backup-test.txt  # Guarda este hash: será tu prueba de integridad al final
```

Ese hash SHA-256 es importante. Yo lo anotaría en el propio *drill* o en el ticket de prueba, porque luego te permite demostrar que no solo has recuperado “un archivo con ese nombre”, sino exactamente el mismo contenido.

### Paso 2: verificar si el sistema usa 512 bytes o 4 KB de sector lógico

Como el anuncio destaca de forma explícita el soporte para ambos tamaños de sector lógico, yo no dejaría esta parte a una suposición. La comprobaría. En Linux, `lsblk` te da la información de una forma bastante limpia:

```bash
# Ejecutado dentro de la VM Linux
lsblk -o NAME,PATH,PHY-SEC,LOG-SEC,SIZE,MOUNTPOINT
```

La salida puede verse así:

```text
NAME   PATH       PHY-SEC LOG-SEC SIZE MOUNTPOINT
sda    /dev/sda      4096     512   64G 
sda1   /dev/sda1     4096     512   63G /
sdc    /dev/sdc      4096    4096    8G 
sdc1   /dev/sdc1     4096    4096    8G /data
```

Aquí ves con claridad qué dispositivos están exponiendo 512 bytes y cuáles 4096 como sector lógico. Yo dejaría esta evidencia documentada en la prueba. No por obsesión burocrática, sino porque luego nadie discute qué validaste exactamente.

Si trabajas con Windows, la imagen de ejemplo de Microsoft sobre [sectores lógicos y físicos](https://learn.microsoft.com/en-us/azure/backup/backup-azure-postgresql-flex-server-elastic-cluster-v2-overview) encaja bastante bien con el tipo de comprobación que conviene hacer en este contexto.

{{< figure src="/images/azure-backup-ya-cubre-la-recuperacion-a-nivel-de-archivo-en-vms-con-premium-ssdv/source-2.png" alt="Ejemplo visual de información de tamaño de sector lógico y físico" caption="Verificar el tamaño de sector lógico es parte de la prueba, porque el soporte anunciado cubre 512 bytes y 4 KB. Fuente: [learn.microsoft.com](https://learn.microsoft.com/en-us/azure/backup/backup-azure-postgresql-flex-server-elastic-cluster-v2-overview)" >}}{{< /figure >}}

### Paso 3: comprobar que la VM está protegida y localizar un recovery point

La siguiente validación es la parte de backup propiamente dicha. Yo la separo en dos preguntas: primero, si la VM está realmente protegida; después, si existen recovery points útiles para la prueba.

Para listar el ítem protegido dentro del Recovery Services vault:

```bash
# Azure CLI 2.75+
az backup item list \
  --resource-group rg-backup-lab \
  --vault-name rsv-backup-lab-01 \
  --backup-management-type AzureIaasVM \
  --workload-type VM \
  --output table
```

Si tu VM no aparece aquí, no tiene sentido seguir hablando de ILR. Primero resuelves la protección; luego haces la prueba. Parece obvio, pero en este tipo de ejercicios siempre hay alguien que intenta empezar por el final.

Después, listaría los recovery points del ítem protegido:

```bash
# Azure CLI 2.75+
az backup recoverypoint list \
  --resource-group rg-backup-lab \
  --vault-name rsv-backup-lab-01 \
  --container-name "IaasVMContainer;iaasvmcontainerv2;rg-backup-lab;vm-linux-restore-01" \
  --item-name "vm-linux-restore-01" \
  --output table
```

Quédate con un recovery point posterior a la creación del archivo de prueba. Si eliges uno anterior, el archivo no existirá todavía y acabarás “validando” un falso negativo. Y eso es lo peor de estas pruebas: cuando falla el procedimiento por un detalle trivial, la gente concluye que la plataforma no sirve.

### Paso 4: lanzar un backup bajo demanda si quieres controlar la prueba

Si no quieres depender del horario de la política, yo haría una copia bajo demanda justo después de crear el archivo. Así reduces ruido y conviertes la prueba en algo mucho más determinista.

```bash
# Azure CLI 2.75+
az backup protection backup-now \
  --resource-group rg-backup-lab \
  --vault-name rsv-backup-lab-01 \
  --container-name "IaasVMContainer;iaasvmcontainerv2;rg-backup-lab;vm-linux-restore-01" \
  --item-name "vm-linux-restore-01" \
  --retain-until 2026-12-31T23:59:00Z
```

La llamada te devolverá los metadatos del trabajo. Después, yo comprobaría su estado antes de seguir:

```bash
# Azure CLI 2.75+
az backup job list \
  --resource-group rg-backup-lab \
  --vault-name rsv-backup-lab-01 \
  --operation Backup \
  --output table
```

Aquí no hay mucho misterio: si el trabajo sigue en `InProgress`, esperas; si falla, arreglas ese problema primero. **ILR no te va a salvar de un backup mal ejecutado**. Parece una obviedad, pero conviene recordarlo porque a veces el entusiasmo por probar una novedad hace que se mezclen demasiadas cosas a la vez.

{{< figure src="/images/azure-backup-ya-cubre-la-recuperacion-a-nivel-de-archivo-en-vms-con-premium-ssdv/source-3.png" alt="Pantalla del vault con puntos de restauración y opción de recuperación de archivos" caption="Antes de recuperar un archivo, yo compruebo que la VM tenga puntos de recuperación recientes y consistentes. Fuente: [learn.microsoft.com](https://learn.microsoft.com/en-us/azure/backup/backup-azure-postgresql-flex-server-elastic-cluster-v2-overview)" >}}{{< /figure >}}

### Paso 5: recuperación a nivel de archivo y qué conviene verificar de verdad

La parte importante llega ahora. El flujo de ILR para Azure VM Backup se basa en seleccionar un recovery point, descargar un script y ejecutarlo en una máquina con acceso suficiente para montar el punto de recuperación y extraer los ficheros. Microsoft muestra ese flujo visualmente en sus capturas de [file recovery desde Azure Backup](https://learn.microsoft.com/en-us/azure/backup/backup-azure-postgresql-flex-server-elastic-cluster-v2-overview).

Lo relevante, en el contexto de esta novedad, es que ese mismo procedimiento ahora también cubre VMs con Premium SSDv2 y Ultra Disk. Dicho de otra forma: **el runbook ya no debería bifurcarse por tipo de almacenamiento**. Para mí, esa es la ganancia operativa real. Menos excepciones, menos notas al pie y menos “esto funciona salvo si…”, que suele ser donde empiezan los dolores de cabeza.

En la práctica, desde el portal abrirías el vault, localizarías la VM, elegirías un recovery point y usarías la opción de recuperación de archivos. Azure te ofrecerá el script de montaje temporal. Una vez ejecutado, tendrás rutas montadas desde las que podrás copiar el archivo deseado. Microsoft también enseña ejemplos del resultado en Linux, incluyendo las [rutas de montaje durante la recuperación](https://learn.microsoft.com/en-us/azure/backup/backup-azure-postgresql-flex-server-elastic-cluster-v2-overview).

Y aquí yo haría una comprobación muy simple, pero muy valiosa: comparar el hash del archivo recuperado con el hash original.

```bash
# Ejecutado en la máquina donde has copiado el archivo recuperado
sha256sum /tmp/recovered/appsettings.backup-test.txt
```

La salida debe coincidir exactamente con el hash calculado antes del backup. Si coincide, has validado algo más útil que un simple “parece que funciona”: has demostrado que la recuperación es íntegra.

Por último, no me olvidaría de la limpieza. El desmontaje de los volúmenes temporales suele ser el paso que nadie documenta porque “ya lo haré luego”. Luego nunca llega. Y después vienen los entornos con residuos raros, montajes olvidados o dudas sobre qué dejó la prueba en la máquina. Si quieres dejar un procedimiento serio, sigue también el flujo de [desmontaje tras la recuperación](https://learn.microsoft.com/en-us/azure/backup/backup-azure-postgresql-flex-server-elastic-cluster-v2-overview).

{{< figure src="/images/azure-backup-ya-cubre-la-recuperacion-a-nivel-de-archivo-en-vms-con-premium-ssdv/source-4.png" alt="Ejemplo de rutas de montaje en Linux durante una recuperación de archivos" caption="En Linux, el flujo de ILR monta temporalmente los volúmenes para poder copiar solo los archivos necesarios. Fuente: [learn.microsoft.com](https://learn.microsoft.com/en-us/azure/backup/backup-azure-postgresql-flex-server-elastic-cluster-v2-overview)" >}}{{< /figure >}}

### Qué dejaría yo documentado en un recovery drill de producción

Cuando termino una prueba así, no me basta con concluir que “ha ido bien”. Eso sirve para una conversación de pasillo, no para una operación repetible. Lo que yo dejaría por escrito es esto:

- Tipo de disco de la VM: Premium SSDv2 o Ultra Disk.
- Sistema operativo y versión.
- Tamaño de sector lógico observado: 512 o 4K.
- Recovery Services vault y política aplicada.
- Tiempo real desde la solicitud hasta el acceso al archivo recuperado.
- Pasos exactos del portal o del script usados para ILR.
- Verificación de integridad mediante hash.
- Pasos de desmontaje y limpieza.
- Limitaciones o incidencias observadas durante la prueba.

Esto convierte una novedad de plataforma en un procedimiento usable. Y ahí es donde yo creo que está el valor de verdad: no en que Azure “soporte algo”, sino en que tú puedas ejecutarlo con confianza, repetirlo y enseñárselo a otra persona sin depender de explicación oral ni de memoria heroica.

### Mi lectura final

Yo veo esta mejora como una novedad pequeña en apariencia, pero importante en la práctica. Azure no está añadiendo solo una casilla más a una tabla de compatibilidad; está eliminando una fricción operativa en configuraciones de almacenamiento que ya son plenamente actuales. Cuando Microsoft confirma el soporte general para [Item-Level Recovery en Premium SSDv2 y Ultra Disk](https://azure.microsoft.com/updates?id=577963), lo que realmente está haciendo es cerrar una brecha que obligaba a convivir con procedimientos menos finos o con *workarounds*.

Si tú operas VMs críticas sobre estos discos, mi recomendación es bastante directa: **no te quedes en el anuncio; ejecuta un recovery drill esta misma semana**. Crea un archivo de prueba, fuerza un backup, recupera solo ese fichero y documenta el resultado. En backup, la distancia entre “está soportado” y “estoy listo para usarlo” casi siempre la marca un ensayo real. Y, sinceramente, prefiero descubrir los matices un martes tranquilo que durante una incidencia de verdad.
