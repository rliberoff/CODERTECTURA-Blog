---
title: 'Azure SQL ya puede usar identidad administrada a nivel de base de datos: adiós
  a los secretos en OPENROWSET'
date: '2026-11-02T06:26:16+00:00'
draft: true
slug: azure-sql-ya-puede-usar-identidad-administrada-a-nivel-de-base-de-datos-adios-a
description: Te enseño cómo usar la nueva identidad administrada a nivel de base de
  datos en Azure SQL para leer de Blob Storage sin SAS ni contraseñas.
categories:
- Azure
- .NET
- Arquitectura de Software
tags:
- Azure SQL Database
- Managed Identity
- Seguridad
- T-SQL
- Azure Blob Storage
image: /images/azure-sql-ya-puede-usar-identidad-administrada-a-nivel-de-base-de-datos-adios-a/cover.png
comments: true
ai:
  assisted: true
  article_type: technical
  model: gpt-5.4
  prompt_version: 2026-08-21.1
  generated_at: '2026-11-02T06:26:16+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://azure.microsoft.com/updates?id=577491
    title: '[In preview] Public Preview: Support database-level managed identity (including
      FIC) in Create Database Scoped Credential T-SQL'
    published_date: '2026-10-30'
  - url: https://learn.microsoft.com/ar-sa/sql//t-sql/statements/create-credential-transact-sql?view=azuresqldb-mi-current
    title: CREATE CREDENTIAL (Transact-SQL) - SQL Server | Microsoft Learn
    published_date: null
---

Si trabajas con Azure SQL Database y alguna vez has tenido que leer ficheros en Blob Storage o en ADLS Gen2, seguramente ya conoces el peaje: **guardar un secreto dentro de SQL para poder salir de SQL**. SAS tokens, claves, rotaciones manuales, credenciales que caducan justo cuando menos gracia te hace. Pues bien, eso empieza a cambiar de verdad. Según el anuncio del [soporte en vista previa para identidad administrada a nivel de base de datos en `CREATE DATABASE SCOPED CREDENTIAL`](https://azure.microsoft.com/updates?id=577491), ahora puedo asociar una identidad administrada asignada por el usuario a cada base de datos de Azure SQL Database y usarla para acceder a Azure Blob Storage o Azure Data Lake Storage Gen2 desde `OPENROWSET` y tablas externas.

Lo interesante no es solo la sintaxis. Lo importante es el cambio de modelo: en vez de inyectar secretos en la base, delego la autenticación en Entra ID y en una *managed identity* que gestiono desde Azure. Y esto, aunque sobre el papel parezca una mejora pequeña, en operación diaria me parece bastante más importante de lo que sugiere el nombre de la característica.

### Qué cambia exactamente

Hasta ahora, en muchos escenarios de acceso a almacenamiento externo desde Azure SQL Database, lo normal era crear una credencial con un SAS o con otro secreto. La propia documentación de [credenciales en Transact-SQL](https://learn.microsoft.com/ar-sa/sql//t-sql/statements/create-credential-transact-sql?view=azuresqldb-mi-current) deja claro cuál es el papel de estas credenciales y también distingue entre `CREATE CREDENTIAL` a nivel de servidor y `CREATE DATABASE SCOPED CREDENTIAL` cuando el ámbito correcto es la base de datos.

La novedad anunciada por Azure es que esa credencial de ámbito de base de datos puede apoyarse en una **user-assigned managed identity ligada a esa base concreta**. En la práctica, esto encaja muy bien cuando tienes varias bases dentro del mismo *logical server* y no quieres que compartan la misma identidad ni, por tanto, el mismo permiso de acceso al almacenamiento.

{{< figure src="/images/azure-sql-ya-puede-usar-identidad-administrada-a-nivel-de-base-de-datos-adios-a/body-1.png" alt="Diagrama del flujo entre Azure SQL Database, identidad administrada y Blob Storage" caption="La idea clave: la base de datos usa una identidad administrada propia para acceder al almacenamiento sin secretos." >}}{{< /figure >}}

Yo lo resumiría en tres ventajas bastante tangibles:

- **Menos superficie de secreto**: elimino SAS tokens de scripts, despliegues y configuraciones.
- **Mejor aislamiento**: cada base puede tener su propia identidad y sus propios permisos.
- **Operación más limpia**: la rotación deja de depender de actualizar secretos almacenados en la base.

Y sí, dicho así suena casi demasiado razonable. Precisamente por eso creo que merece atención.

### Antes de empezar

Para reproducir este escenario, yo partiría de un inventario mínimo bastante simple:

- Una suscripción de Azure donde puedas crear recursos.
- [Azure CLI](https://azure.microsoft.com/updates?id=577491) instalada y funcionando, con una versión reciente.
- Un Azure SQL Database existente: *logical server* y base de datos de prueba.
- Una identidad administrada asignada por el usuario ya creada en Azure, o permiso para crearla.
- Una cuenta de Storage con Blob Storage o ADLS Gen2 y un contenedor con al menos un CSV.
- Permisos para asignar identidades y roles en Azure, administrar la base de datos y conceder acceso al almacenamiento.
- Un cliente SQL para ejecutar T-SQL, por ejemplo Azure Data Studio o SQL Server Management Studio.

En mi ejemplo voy a usar estos nombres, para que el flujo se entienda a la primera:

- Resource group: `rg-codertectura-data`
- SQL server: `sql-codertectura-demo`
- Database: `salesdb`
- User-assigned managed identity: `mi-salesdb-reader`
- Storage account: `stcodertecturadata`
- Container: `imports`
- Fichero: `sales-2026-10.csv`

### Paso 1: preparar la identidad y darle acceso al Storage

Lo primero que necesito es una identidad administrada asignada por el usuario y permisos sobre el contenedor o la cuenta de almacenamiento. Para un escenario de lectura con `OPENROWSET`, un rol como `Storage Blob Data Reader` es un punto de partida razonable.

```bash
az login
az account set --subscription "Visual Studio Enterprise"

az identity create \
  --resource-group rg-codertectura-data \
  --name mi-salesdb-reader \
  --location westeurope

az identity show \
  --resource-group rg-codertectura-data \
  --name mi-salesdb-reader \
  --query principalId \
  --output tsv
# Este valor es el que necesitas en --assignee-object-id; no uses el resource id por error.

az role assignment create \
  --assignee-object-id 11111111-2222-3333-4444-555555555555 \
  --assignee-principal-type ServicePrincipal \
  --role "Storage Blob Data Reader" \
  --scope /subscriptions/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee/resourceGroups/rg-codertectura-data/providers/Microsoft.Storage/storageAccounts/stcodertecturadata
```

La primera orden crea la identidad. Después recupero su `principalId`, que es el dato correcto para la asignación de rol. Y luego concedo acceso al Storage. Este detalle parece pequeño, pero no lo es: **si confundes `principalId` con `id`, te vas a regalar una tarde bastante tonta**.

La salida esperada tras crear la identidad será algo parecido a esto:

```json
{
  "clientId": "6a6b6c6d-1234-4567-89ab-0f1e2d3c4b5a",
  "id": "/subscriptions/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee/resourcegroups/rg-codertectura-data/providers/Microsoft.ManagedIdentity/userAssignedIdentities/mi-salesdb-reader",
  "location": "westeurope",
  "name": "mi-salesdb-reader",
  "principalId": "11111111-2222-3333-4444-555555555555",
  "resourceGroup": "rg-codertectura-data"
}
```

Si la asignación de rol sale bien, Azure CLI te devolverá un JSON donde verás `roleDefinitionName` con el valor `Storage Blob Data Reader`. Con eso, al menos en la parte de Azure RBAC, ya has dejado el terreno preparado.

### Paso 2: asociar la identidad a la base de datos y crear la credencial

Aquí está el corazón de la novedad. El anuncio de Azure habla explícitamente de [usar una user-assigned managed identity por base de datos para consultar ficheros en Blob Storage y ADLS Gen2 mediante tablas externas y `OPENROWSET`](https://azure.microsoft.com/updates?id=577491). La pieza visible en T-SQL es `CREATE DATABASE SCOPED CREDENTIAL`.

No voy a complicarlo todavía con una tabla externa. Para validar la idea, yo prefiero empezar por el camino más directo: crear la credencial de base de datos y un `EXTERNAL DATA SOURCE` contra el contenedor.

```sql
-- Ejecuta esto conectado a salesdb
CREATE DATABASE SCOPED CREDENTIAL SalesLakeCredential
WITH IDENTITY = 'Managed Identity';
GO

CREATE EXTERNAL DATA SOURCE SalesImports
WITH (
    TYPE = BLOB_STORAGE,
    LOCATION = 'https://stcodertecturadata.blob.core.windows.net/imports',
    CREDENTIAL = SalesLakeCredential -- reutilizo una identidad sin almacenar ningún secreto en la base
);
GO
```

Aquí lo esperable es ver dos mensajes de `Command(s) completed successfully.`. Si falla en este punto, yo no me pondría creativo todavía: revisaría primero si la identidad está correctamente asociada al contexto de la base y si tiene permisos suficientes sobre el Storage. Casi siempre el problema está ahí, no en la sintaxis.

{{< figure src="/images/azure-sql-ya-puede-usar-identidad-administrada-a-nivel-de-base-de-datos-adios-a/source-2.png" alt="Esquema de credenciales de SQL con identidad administrada" caption="Las credenciales de SQL actúan como puente de autenticación hacia recursos externos; esta vista previa lleva esa idea al ámbito de base de datos con managed identity. Fuente: [learn.microsoft.com](https://learn.microsoft.com/ar-sa/sql//t-sql/statements/create-credential-transact-sql?view=azuresqldb-mi-current)" >}}{{< /figure >}}

Hay un matiz que me parece especialmente importante. Si lees la documentación de [credenciales de SQL](https://learn.microsoft.com/ar-sa/sql//t-sql/statements/create-credential-transact-sql?view=azuresqldb-mi-current), verás mucho contexto sobre credenciales con secreto, SAS o contraseñas. **Precisamente por eso esta vista previa importa**: el patrón mental deja de ser “guardo cómo autenticarme” y pasa a ser “declaro con qué identidad corporativa salgo”. En términos de seguridad operativa, para mí eso es un salto serio.

### Paso 3: leer un CSV desde Blob Storage con `OPENROWSET`

Con la credencial y el `EXTERNAL DATA SOURCE` creados, ya puedo probar la lectura real del fichero. Voy a usar un CSV sencillo porque es la forma más rápida de verificar el extremo a extremo: autenticación, acceso al blob y lectura desde SQL sin secretos embebidos.

```sql
SELECT TOP (10)
    OrderId,
    CustomerName,
    Amount,
    Region
FROM OPENROWSET(
    BULK 'sales-2026-10.csv',
    DATA_SOURCE = 'SalesImports',
    FORMAT = 'CSV',
    PARSER_VERSION = '2.0', -- fuerzo el parser moderno para evitar diferencias de comportamiento con CSV reales
    FIRSTROW = 2
)
WITH (
    OrderId int,
    CustomerName varchar(100),
    Amount decimal(10,2),
    Region varchar(50)
) AS rows;
GO
```

Si todo está bien, verás un conjunto de resultados con las primeras filas del CSV. Algo parecido a esto:

```text
OrderId  CustomerName     Amount    Region
-------  ---------------  --------  -------
1001     Contoso Retail   1499.95   ES-North
1002     Fabrikam Food    230.00    ES-East
1003     Alpine Sports    899.50    ES-Center
```

Si recibes un error de acceso denegado al blob, yo revisaría en este orden:

1. Que la identidad tenga realmente el rol correcto en la cuenta o en el contenedor,
2. Que el `LOCATION` del `EXTERNAL DATA SOURCE` apunte al contenedor correcto,
3. Que el fichero exista con ese nombre exacto,
4. Que estés usando la capacidad en vista previa descrita por Azure.

Ese orden importa. Antes de tocar T-SQL, primero confirmo permisos y rutas. Muchas veces SQL solo está siendo el mensajero de un problema de RBAC.

### Cómo comparo esto con el enfoque clásico de SAS

El enfoque antiguo con SAS funcionaba, y sigue funcionando en muchos escenarios, pero arrastra varios costes escondidos. El primero es obvio: el token es un secreto. El segundo suele aparecer meses después, cuando alguien lo dejó pegado en un pipeline, en un script de despliegue o en un runbook que nadie quería volver a abrir. El tercero es arquitectónico: si varias bases comparten el mismo SAS, en la práctica comparten más confianza de la que deberían.

Con identidad administrada a nivel de base de datos, puedo diseñar algo mucho más fino. Por ejemplo, una base `salesdb` con acceso solo al contenedor `imports`, y otra base `financedb` con otra identidad distinta y acceso a otro contenedor. **No solo reduzco secretos; también reduzco el blast radius**. Y esto, cuando pasan cosas raras, se nota muchísimo.

{{< figure src="/images/azure-sql-ya-puede-usar-identidad-administrada-a-nivel-de-base-de-datos-adios-a/body-3.png" alt="Comparativa visual entre SAS tokens e identidad administrada" caption="Comparación práctica: menos secretos que rotar y mejor aislamiento por base de datos." >}}{{< /figure >}}

Eso sí, tampoco lo vendería como magia (porque no lo es). Cambias gestión de secretos por gestión de identidades y permisos RBAC. En mi experiencia, ese intercambio merece la pena casi siempre, pero exige disciplina con la nomenclatura, el *ownership* y la revisión de roles. Si haces eso bien, ganas bastante. Si no, simplemente mueves el desorden de sitio.

### Un patrón práctico que sí recomiendo

Si vas a adoptar esta capacidad, yo seguiría una pauta muy concreta:

- Una user-assigned managed identity por base de datos que realmente necesite acceso externo;
- Permisos mínimos en Storage, mejor a nivel de contenedor que de cuenta cuando sea posible;
- Nombres explícitos para credenciales y `EXTERNAL DATA SOURCE`;
- Validación con `OPENROWSET` antes de montar tablas externas o procesos más elaborados.

Ese orden evita un error bastante común: complicar el diseño antes de verificar la autenticación básica. Yo primero compruebo que la base sale con la identidad correcta. Luego ya modelo consumo, tablas externas o lo que toque.

### Limitaciones y cautelas de esta vista previa

Como el anuncio habla de [public preview](https://azure.microsoft.com/updates?id=577491), yo sería prudente en producción crítica. No porque tenga que ir mal, sino porque una vista previa puede venir con limitaciones regionales, cambios de comportamiento o requisitos adicionales de configuración. Antes de meter esto en un flujo sensible, yo revisaría muy bien el alcance de soporte y haría pruebas de permisos, auditoría y observabilidad.

También conviene recordar que esta capacidad está enfocada a Azure SQL Database y a acceso a Storage en escenarios como `OPENROWSET` y tablas externas. No la interpretaría como un reemplazo universal de cualquier secreto en cualquier integración. Donde encaja, encaja muy bien. Fuera de ese perímetro, toca seguir evaluando caso por caso.

### Mi conclusión

A mí esta mejora me parece de las que sí cambian el día a día. No porque añada una palabra clave espectacular ni porque venga envuelta en marketing brillante, sino porque elimina una fricción muy real: **persistir secretos allí donde en realidad solo necesito identidad**. Si trabajas con ingestión ligera, lectura puntual de ficheros o federación sencilla entre Azure SQL y Storage, esta novedad te da un camino bastante más limpio.

Mi recomendación es simple: pruébalo en una base de laboratorio, monta un contenedor con un CSV real y valida el flujo con `OPENROWSET`. Si ves que el acceso queda estable y que el modelo de permisos te encaja, estarás sustituyendo uno de esos pequeños riesgos heredados que casi nadie discute… hasta que caduca un token un viernes por la tarde 😅
