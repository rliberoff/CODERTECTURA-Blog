---
title: 'Actualizaciones mayores in-place para PostgreSQL elastic clusters en Azure:
  por fin cambia el plan de mantenimiento'
date: '2026-10-05T13:43:20+00:00'
draft: true
slug: actualizaciones-mayores-in-place-para-postgresql-elastic-clusters-en-azure-por-f
description: Azure ya permite en preview actualizar la versión mayor de PostgreSQL
  en elastic clusters sin recrear el clúster. Te explico qué cambia, qué revisar antes
  y cómo validarlo con criterio.
categories:
- Azure
- Arquitectura de Software
- Bases de Datos
tags:
- PostgreSQL
- Azure Database for PostgreSQL
- Elastic Clusters
- Azure CLI
- Actualizaciones
- Mantenimiento
image: /images/actualizaciones-mayores-in-place-para-postgresql-elastic-clusters-en-azure-por-f/cover.png
comments: true
ai:
  assisted: true
  article_type: technical
  model: gpt-5.4
  prompt_version: 2026-08-21.1
  generated_at: '2026-10-05T13:43:20+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://azure.microsoft.com/updates?id=571504
    title: '[In preview] Public Preview: Major version upgrades (MVU) for Azure Database
      for PostgreSQL elastic clusters'
    published_date: '2026-10-02'
  - url: https://learn.microsoft.com/en-us/azure/postgresql/configure-maintain/concepts-version-policy
    title: Version Policy - Azure Database for PostgreSQL | Microsoft Learn
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/backup/backup-azure-database-postgresql-flex-overview
    title: About Azure Database for PostgreSQL Flexible server backup - Azure Backup
      | Microsoft Learn
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/postgresql/configure-maintain/concepts-major-version-upgrade
    title: Major Version Upgrades - Azure Database for PostgreSQL | Microsoft Learn
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/postgresql/release-notes/release-notes
    title: Release Notes for Azure Database for PostgreSQL flexible server - Azure
      Database for PostgreSQL | Microsoft Learn
    published_date: null
---

Si trabajas con PostgreSQL distribuido en Azure, esta novedad me parece bastante más importante de lo que suena en un titular. Azure ha puesto en preview las **major version upgrades in-place para Azure Database for PostgreSQL elastic clusters**. Traducido a lenguaje de operaciones reales: ahora puedo subir de versión mayor sobre un clúster existente sin levantar otro clúster, sin migrar los datos distribuidos y sin tocar las cadenas de conexión, tal y como recoge el [anuncio de Azure Updates](https://azure.microsoft.com/updates?id=571504).

A mí lo que me interesa aquí no es solo la mecánica del upgrade. Lo relevante de verdad es que **cambia la conversación de mantenimiento**. Antes, una actualización mayor en un entorno distribuido se parecía demasiado a una mini-migración: más coordinación, más puntos de fallo y más tiempo invertido en proteger la operación que en validar la compatibilidad. Con este enfoque in-place, la parte ingrata baja mucho de intensidad y el esfuerzo vuelve a donde debería haber estado siempre: compatibilidad, validación y ventana de intervención.

### Qué cambia exactamente con esta preview

La idea base no es nueva en Azure, pero sí lo es su aterrizaje en elastic clusters. La [documentación de major version upgrades](https://learn.microsoft.com/en-us/azure/postgresql/configure-maintain/concepts-major-version-upgrade) explica para Azure Database for PostgreSQL que un upgrade mayor in-place conserva el nombre del servidor y otros ajustes, evita una migración de datos y reduce la disrupción frente a un reemplazo completo. Que eso llegue ahora al mundo de elastic clusters tiene bastante peso, porque aquí no hablo de una sola instancia, sino de una topología distribuida con coordinador, nodos y una arquitectura que suele estar bastante pegada a cómo funciona la aplicación.

En ese contexto, recrear plataforma nunca ha sido “solo una tarea de infraestructura”. Suele implicar revisar dependencias, retocar automatizaciones, revalidar conectividad y volver a pasar por una lista de comprobaciones que crece muy rápido en cuanto el sistema deja de ser trivial. **Lo que antes olía a proyecto operativo ahora se acerca mucho más a una intervención mantenible**.

{{< figure src="/images/actualizaciones-mayores-in-place-para-postgresql-elastic-clusters-en-azure-por-f/body-1.png" alt="Diagrama del camino de actualización mayor in-place en un elastic cluster" caption="La diferencia clave de esta preview: actualizar el mismo elastic cluster en lugar de recrearlo y migrar datos." >}}{{< /figure >}}

Eso sí, aquí conviene no autoengañarse. Que el upgrade sea in-place no lo convierte en inocuo. La propia [guía de Azure sobre actualizaciones mayores](https://learn.microsoft.com/en-us/azure/postgresql/configure-maintain/concepts-major-version-upgrade) recuerda que puede haber cambios no retrocompatibles y validaciones relacionadas con extensiones, replicación lógica, transacciones preparadas, *event triggers*, dependencias de objetos o configuraciones pendientes de reinicio. Es decir: el atajo operativo existe, pero el trabajo serio sigue ahí.

### Antes de empezar

Si yo tuviera que preparar esta operación, arrancaría por una lista bastante terrenal:

- Una suscripción de Azure activa.
- Un Azure Database for PostgreSQL elastic cluster ya desplegado.
- Permisos suficientes sobre el recurso para inspeccionarlo y ejecutar la actualización.
- Azure CLI instalada y razonablemente al día.
- Cliente `psql` para validar versión y ejecutar comprobaciones antes y después.
- Una batería mínima de consultas o pruebas representativas de tu aplicación.

También revisaría algo que a veces se deja para el final (y luego vienen las prisas): el horizonte de soporte. La [política de versiones de Azure Database for PostgreSQL](https://learn.microsoft.com/en-us/azure/postgresql/configure-maintain/concepts-version-policy) deja claro que Azure soporta cada versión mayor desde que la ofrece hasta su fin de soporte según la comunidad PostgreSQL. Eso significa que el destino no debería elegirse por impulso ni por la tentación del “ya que estamos, subimos a la última”. Yo intentaría cuadrar versión objetivo, soporte disponible y esfuerzo real de validación. No siempre coinciden, y ahí está precisamente el criterio.

### Paso 1: inspeccionar la versión actual y preparar la línea base

Lo primero que hago es confirmar qué recurso voy a tocar y qué versión tengo realmente en ejecución. Parece obvio, pero en operaciones de mantenimiento los errores más feos suelen empezar por una suposición tonta.

En Azure, una forma práctica de identificar el recurso es consultar directamente el `id` del elastic cluster:

```bash
az login
az account set --subscription "Plataforma-Produccion"

az resource show \
  --resource-group rg-data-prod \
  --name pg-elastic-orders \
  --resource-type "Microsoft.DBforPostgreSQL/serverGroupsv2" \
  --query "{id:id,name:name,location:location,type:type}" \
  --output json
```

Aquí lo importante no es el JSON bonito; lo importante es que te quedes con una referencia inequívoca del recurso sobre el que vas a operar. Si no aparece, yo pararía en seco. Normalmente significa nombre incorrecto, grupo de recursos incorrecto o permisos que no son los que creías tener.

Después validaría la versión desde PostgreSQL, que al final es la línea base que me sirve para comparar antes y después:

```bash
psql "host=pg-elastic-orders.postgres.database.azure.com port=5432 dbname=postgres user=platformadmin sslmode=require" \
  -v ON_ERROR_STOP=1 \
  -c "select version(), current_setting('server_version') as server_version;" # fuerzo error inmediato si la conexión o la consulta fallan
```

Me gusta añadir `-v ON_ERROR_STOP=1` porque evita el falso positivo cómodo: el script sigue, pero la comprobación en realidad no ha sido fiable. Y en este tipo de tareas, prefiero una ejecución que falle pronto a una que me deje una sensación de seguridad totalmente inmerecida.

{{< figure src="/images/actualizaciones-mayores-in-place-para-postgresql-elastic-clusters-en-azure-por-f/source-2.png" alt="Pantalla de Azure mostrando el estado de despliegue y actualización del elastic cluster" caption="La experiencia de Azure deja ver el avance de operaciones sobre elastic clusters, incluida la actualización de versión mayor. Fuente: [learn.microsoft.com](https://learn.microsoft.com/en-us/azure/postgresql/configure-maintain/concepts-major-version-upgrade)" >}}{{< /figure >}}

Con esa información ya puedo planificar el salto. La [política de versiones](https://learn.microsoft.com/en-us/azure/postgresql/configure-maintain/concepts-version-policy) deja claro que el destino debe seguir soportado por Azure en el momento del upgrade. Además, la [documentación de major upgrades](https://learn.microsoft.com/en-us/azure/postgresql/configure-maintain/concepts-major-version-upgrade) advierte de algo importante: el portal evita seleccionar versiones no soportadas, pero si apuntas por API o CLI a una versión retirada, la operación puede fallar. Mi recomendación aquí es poco glamourosa, pero funciona: decide el destino por soporte y compatibilidad, no por ansiedad tecnológica.

### Paso 2: comprobar si tu entorno ya expone la operación

Como esto está en preview, yo no daría por hecho que la superficie de CLI está cerrada o que se presenta igual en todos los entornos. Antes de pensar en lanzar nada, comprobaría si mi suscripción y mi CLI ya están viendo las operaciones del proveedor relacionadas con `serverGroupsv2`.

```bash
az provider operation show \
  --namespace Microsoft.DBforPostgreSQL \
  --query "resourceTypes[?resourceType=='serverGroupsv2'].operations[].name" \
  --output tsv
```

Esta consulta no ejecuta el upgrade, pero sí me da una pista valiosa: qué operaciones publica el proveedor para ese tipo de recurso en ese momento. Si ahí identificas la operación correspondiente al cambio de versión mayor, ya sabes que tu entorno al menos está viendo la capacidad. Si no aparece, yo no me pelearía con comandos inventados ni con forzar una sintaxis que quizá ha cambiado; usaría el portal y mantendría exactamente el mismo proceso de validación alrededor.

Y aquí está la parte importante: **la novedad no es el comando, sino el modelo operativo**. El upgrade se hace sobre el recurso actual, no sobre un reemplazo temporal que luego tengas que promover, reconectar y limpiar.

### Paso 3: ejecutar la actualización y asumir que habrá una ventana real

El [anuncio de Azure Updates](https://azure.microsoft.com/updates?id=571504) deja claro que el upgrade mayor puede hacerse in-place sobre un elastic cluster existente. Eso reduce mucha fricción, sí, pero no elimina el hecho de que sigue siendo una operación mayor. Yo contaría con una ventana de indisponibilidad asociada al proceso y lo trataría como una intervención planificada, no como una tarea de rutina lanzada entre reuniones.

La [documentación general sobre major version upgrades](https://learn.microsoft.com/en-us/azure/postgresql/configure-maintain/concepts-major-version-upgrade) explica además que este enfoque suele ser más rápido y con menos *downtime* que una migración basada en mover datos. Para mí, ese es el verdadero beneficio: no que desaparezca el riesgo, sino que el riesgo deja de estar repartido entre demasiadas piezas a la vez.

Si durante la preview la firma exacta en CLI cambia, mi consejo es sencillo: valida la ayuda disponible en tu entorno con `az -h`, confirma la operación soportada y evita automatizar a ciegas algo que todavía puede moverse. No hay épica en ser el primero en descubrir una variación de sintaxis en producción.

### Paso 4: verificar que el recurso sigue siendo el mismo y que la versión sí ha cambiado

Cuando termina el upgrade, yo compruebo tres cosas: identidad del recurso, versión del motor y salud funcional mínima. En ese orden.

Primero, vuelvo a inspeccionar Azure:

```bash
az resource show \
  --resource-group rg-data-prod \
  --name pg-elastic-orders \
  --resource-type "Microsoft.DBforPostgreSQL/serverGroupsv2" \
  --query "{id:id,name:name,location:location}" \
  --output json
```

Aquí no necesito arrastrar todas las `properties` si mi objetivo es confirmar identidad. Me basta con validar que sigo viendo el mismo `id`, el mismo nombre y el mismo recurso lógico. Y eso, precisamente, es una de las ventajas operativas de este enfoque: no cambio inventario, no cambio endpoint y no obligo a otros equipos a perseguir una reconfiguración que no aporta valor.

Después repito la validación en PostgreSQL:

```bash
psql "host=pg-elastic-orders.postgres.database.azure.com port=5432 dbname=postgres user=platformadmin sslmode=require" \
  -v ON_ERROR_STOP=1 \
  -c "select current_database(), current_setting('server_version') as server_version, version();"
```

La salida debería seguir apuntando a la misma base de datos y reflejar ya la nueva versión mayor. Si antes estabas en 15 y tu destino era 16, aquí es donde quiero verlo negro sobre blanco. Sin interpretaciones, sin “parece que sí”.

### Paso 5: validar compatibilidad de aplicación sin hacer teatro

Para mí, esta es la fase más importante. Que el upgrade haya terminado correctamente solo significa que la plataforma ha completado su parte. No significa que tu aplicación, tus *jobs* o tus integraciones estén felices.

La [guía de Azure sobre major version upgrades](https://learn.microsoft.com/en-us/azure/postgresql/configure-maintain/concepts-major-version-upgrade) menciona validaciones previas relacionadas con extensiones no soportadas, *logical replication slots*, *prepared transactions*, *event triggers*, dependencias de objetos y cambios pendientes de reinicio. Es una buena lista para no ir a ciegas, así que yo empezaría por unas comprobaciones SQL pequeñas pero útiles:

```sql
select current_setting('server_version') as server_version;

select extname, extversion
from pg_extension
order by extname;

select slot_name, plugin, slot_type, active
from pg_replication_slots
order by slot_name;

select gid, prepared, owner, database
from pg_prepared_xacts
order by prepared desc;
```

No es una batería exhaustiva, pero sí me da visibilidad rápida sobre varios puntos sensibles. Si aparecen *replication slots* lógicos, extensiones delicadas o transacciones preparadas que no esperabas, yo no cerraría la intervención todavía. Ahí toca contrastar con el comportamiento real de la aplicación y con cualquier integración que dependa de esos elementos.

{{< figure src="/images/actualizaciones-mayores-in-place-para-postgresql-elastic-clusters-en-azure-por-f/body-3.png" alt="Checklist visual de validación antes y después de una actualización mayor" caption="La parte crítica no es lanzar el upgrade, sino validar extensiones, replicación, transacciones preparadas y comportamiento real de la aplicación." >}}{{< /figure >}}

Luego haría la validación que de verdad me tranquiliza: consultas y operaciones de negocio representativas. Lecturas con `JOIN` sobre datos distribuidos, escrituras en tablas críticas, procesos batch, tareas que dependan de extensiones y cualquier flujo que históricamente te haya dado guerra. **La señal buena no es que PostgreSQL haya subido de versión; la señal buena es que tu sistema sigue comportándose como esperas**.

### Qué implica esto para tu estrategia de mantenimiento

Donde más valor le veo a esta preview es en equipos que ya daban por hecho que una major upgrade en un entorno distribuido equivalía a abrir un pequeño proyecto. Con este cambio, Azure reduce buena parte del coste operativo de mantenerse en versiones soportadas. Y eso encaja muy bien con la [política de versiones del servicio](https://learn.microsoft.com/en-us/azure/postgresql/configure-maintain/concepts-version-policy): las versiones mayores tienen fecha de fin de soporte, y posponer upgrades por pura fricción técnica suele salir más caro de lo que parece.

También me parece importante mirar el contexto más amplio del servicio. Las [release notes de Azure Database for PostgreSQL](https://learn.microsoft.com/en-us/azure/postgresql/release-notes/release-notes) muestran que la plataforma sigue evolucionando con nuevas capacidades, métricas y cambios operativos. Quedarte demasiado atrás no solo te acorta el margen de soporte; también te aleja de mejoras que, con el tiempo, simplifican observabilidad, rendimiento y operación diaria.

Y hay otro ángulo que no conviene separar artificialmente: backup y recuperación. La [documentación de Azure Backup para PostgreSQL](https://learn.microsoft.com/en-us/azure/backup/backup-azure-database-postgresql-flex-overview) indica que la solución v2 para flexible server y elastic cluster está en preview y se apoya en *snapshots* de disco gestionado en lugar de `pg_dump`. Yo aquí saco una conclusión bastante práctica: si vas a replantearte cómo haces actualizaciones mayores, aprovecha también para revisar cómo haces copias y cómo restauras. Mantenimiento y recuperación deberían formar parte de la misma conversación, no de dos reuniones distintas con dos hojas Excel distintas (sí, esas hojas existen).

{{< figure src="/images/actualizaciones-mayores-in-place-para-postgresql-elastic-clusters-en-azure-por-f/body-4.png" alt="Diagrama de estrategia de mantenimiento para PostgreSQL elastic clusters en Azure" caption="Con el upgrade in-place, la estrategia pasa de migrar infraestructura a gobernar versiones, compatibilidad y recuperación." >}}{{< /figure >}}

### Mi lectura práctica de esta preview

Yo no vendería esto como “ya no hay que preocuparse por las major upgrades”. Sería exagerar. Lo que sí creo es que **Azure ha quitado del medio la parte más pesada de la operación: recrear, migrar y reconfigurar**. Y eso, para un equipo que trabaja con PostgreSQL distribuido, no es una mejora cosmética precisamente.

A partir de aquí, el trabajo importante pasa a ser el que de verdad merece atención en sistemas maduros: gobernanza de versiones, pruebas de compatibilidad, ventanas de mantenimiento sensatas y validación funcional antes de dar por hecho que todo está bien. Y casi prefiero que sea así. Porque esa parte depende de tu contexto, de tu aplicación y de tus decisiones; la otra era, en gran medida, fricción de plataforma.

Si me preguntas por una hoja de ruta razonable, yo iría así: confirma versión actual, cruza el destino con la política de soporte, revisa las restricciones funcionales, prueba la operación en un entorno no productivo y solo después agenda la actualización in-place en producción. No hay magia. Pero, por una vez, **sí hay bastante menos sufrimiento operativo**.
