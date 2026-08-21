---
title: 'Azure SQL y formato SQL en VS Code: menos fricción, más flujo real con la
  extensión MSSQL'
date: '2026-08-21T11:35:41+00:00'
draft: true
slug: azure-sql-y-formateo-sql-en-vs-code-menos-friccion-mas-flujo-real-con-la-extensi
description: La extensión MSSQL para VS Code ya me deja aprovisionar Azure SQL Database
  y formatear T-SQL sin salir del editor. Te enseño un flujo simple, verificable y
  muy útil en el día a día.
categories:
- Azure
- .NET
- Arquitectura de Software
tags:
- VS Code
- Azure SQL Database
- MSSQL
- SQL
- T-SQL
- Herramientas de desarrollo
image: /images/azure-sql-y-formateo-sql-en-vs-code-menos-friccion-mas-flujo-real-con-la-extensi/cover.png
comments: true
ai:
  assisted: true
  article_type: technical
  model: gpt-5.4
  prompt_version: 2026-08-21.1
  generated_at: '2026-08-21T11:35:41+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://devblogs.microsoft.com/azure-sql/upgrade-from-sql-server-express-to-azure-sql-database/
    title: Outgrowing SQL Server Express? Upgrade to Azure SQL Database Free Tier
      in 3 Steps
    published_date: '2026-08-19'
  - url: https://learn.microsoft.com/en-us/azure/azure-sql/database/connect-query-vscode?view=azuresql
    title: Use Visual Studio Code to connect and query - Azure SQL Database & SQL
      Managed Instance | Microsoft Learn
    published_date: null
  - url: https://learn.microsoft.com/en-us/ssms/release-notes-22
    title: Release Notes for SQL Server Management Studio (SSMS)
    published_date: null
  - url: https://devblogs.microsoft.com/azure-sql/vscode-mssql-august2026
    title: 'MSSQL Extension for VS Code: SQL Formatter, Azure SQL Database Provisioning,
      and More'
    published_date: null
  - url: https://learn.microsoft.com/en-us/sql/tools/visual-studio-code-extensions/mssql/mssql-extension-visual-studio-code?view=sql-server-ver17
    title: Overview - MSSQL Extension for Visual Studio Code
    published_date: null
---

Hay actualizaciones que, sobre el papel, parecen menores. Luego las pruebas en un día normal de trabajo y piensas: «vale, esto sí me ahorra tiempo de verdad». Eso es exactamente lo que me pasa con lo nuevo de la extensión **MSSQL para VS Code**: ahora puedo **aprovisionar Azure SQL Database desde el propio editor** y además **formatear SQL** sin andar saltando entre herramientas porque sí.

A mí este cambio me interesa por una razón muy concreta: cierra un hueco bastante molesto entre escribir código, preparar datos, validar consultas y moverme a un entorno gestionado. La [actualización de la extensión MSSQL](https://devblogs.microsoft.com/azure-sql/vscode-mssql-august2026) va justo en esa dirección, y encaja muy bien con la [guía oficial para conectar y consultar Azure SQL desde VS Code](https://learn.microsoft.com/en-us/azure/azure-sql/database/connect-query-vscode?view=azuresql) y con la [visión general de la propia extensión](https://learn.microsoft.com/en-us/sql/tools/visual-studio-code-extensions/mssql/mssql-extension-visual-studio-code?view=sql-server-ver17).

### Lo que cambia de verdad en el trabajo diario

Hasta ahora, el flujo era más disperso de lo que debería. Yo podía escribir T-SQL en VS Code sin problema, pero en cuanto tocaba crear o ajustar una base en Azure, acababa en el portal, en SSMS o en scripts manuales. Y eso, aunque parezca una tontería, rompe el ritmo. **Cuanto más cambio de contexto, peor pienso y más lento avanzo**.

Con esta actualización, la extensión acerca dos tareas muy frecuentes al sitio donde ya estoy trabajando: crear una Azure SQL Database y mantener un estilo coherente de SQL con el formateador. Además, esto no aparece en el vacío. También se nota una intención parecida en otras herramientas; por ejemplo, las [release notes de SSMS 22](https://learn.microsoft.com/en-us/ssms/release-notes-22) muestran cambios orientados a simplificar la experiencia de creación y conexión. Mi lectura es bastante clara: Microsoft está afinando la experiencia para desarrolladores de aplicaciones, no solo para perfiles puramente de administración.

{{< figure src="/images/azure-sql-y-formateo-sql-en-vs-code-menos-friccion-mas-flujo-real-con-la-extensi/source-1.webp" alt="Creación de Azure SQL Database desde VS Code" caption="La extensión MSSQL ya expone un flujo de creación de Azure SQL Database dentro de VS Code, reduciendo el salto entre desarrollo y aprovisionamiento. Fuente: [devblogs.microsoft.com](https://devblogs.microsoft.com/azure-sql/vscode-mssql-august2026)" >}}{{< /figure >}}

### Antes de empezar

Si quieres reproducir el flujo de este artículo, yo prepararía esto:

- **Visual Studio Code** instalado.
- La **extensión MSSQL para VS Code**, como explica la [documentación oficial de la extensión](https://learn.microsoft.com/en-us/sql/tools/visual-studio-code-extensions/mssql/mssql-extension-visual-studio-code?view=sql-server-ver17).
- **Azure CLI 2.75 o superior** disponible en terminal.
- Una **suscripción de Azure** activa.
- Permisos suficientes para crear recursos SQL en Azure, incluyendo servidor lógico, base de datos y, si hace falta, reglas de firewall.
- Sesión iniciada con `az login`.
- Si vas a ejecutar consultas al momento, acceso permitido desde tu IP o la configuración equivalente que te proponga el asistente.

Antes de tocar nada, yo comprobaría dos cosas: que Azure CLI responde y que estás autenticado en la suscripción correcta. Parece obvio, sí, pero es el tipo de obviedad que te roba veinte minutos cuando falla.

```bash
az version
az account show --output table  # Me asegura qué suscripción está activa antes de crear nada
```

La primera orden debe devolverte la versión instalada de Azure CLI. La segunda debería mostrar, al menos, el nombre de la suscripción activa y su identificador.

```text
Name               CloudName    SubscriptionId                        TenantId
-----------------  -----------  ------------------------------------  ------------------------------------
Visual Studio Dev  AzureCloud   11111111-2222-3333-4444-555555555555  66666666-7777-8888-9999-000000000000
```

### Paso 1: aprovisionar Azure SQL Database desde VS Code

La novedad más visible es esta: ya no necesito salir del editor para crear una base nueva en Azure. En la [entrada del equipo de Azure SQL sobre esta actualización](https://devblogs.microsoft.com/azure-sql/vscode-mssql-august2026) se enseña precisamente ese flujo dentro de VS Code. Si vienes de prototipos locales o de instalaciones ligeras, conecta bastante bien con el escenario que describen en [cómo pasar de SQL Server Express a Azure SQL Database Free Tier](https://devblogs.microsoft.com/azure-sql/upgrade-from-sql-server-express-to-azure-sql-database/): empiezas con algo cercano y barato, pero cuando necesitas un servicio gestionado, el salto deja de ser una pequeña ceremonia burocrática.

En VS Code, abre la paleta de comandos y busca la acción de la extensión MSSQL para crear una nueva base de datos de Azure SQL. El asistente te irá pidiendo la suscripción, el grupo de recursos, el servidor lógico, el nombre de la base y la configuración básica. Mi consejo aquí es bastante terrenal: si estás validando una aplicación, crea un entorno pequeño pero realista. No intentes “simular producción” en el minuto uno, porque normalmente eso solo añade ruido.

Yo suelo acompañar ese flujo con una verificación rápida desde Azure CLI. No porque no me fíe del asistente, sino porque me gusta separar interfaz y realidad. Si el recurso existe de verdad, CLI me lo va a decir sin adornos.

```bash
az sql server list \
  --resource-group rg-codertectura-sql \
  --output table  # Verifico que el servidor lógico existe realmente en el grupo esperado
```

Si el aprovisionamiento ha ido bien, deberías ver una fila con el nombre del servidor lógico, su ubicación y el grupo de recursos.

```text
Name                    ResourceGroup         Location     AdministratorLogin
----------------------  --------------------  -----------  ------------------
sql-codertectura-dev    rg-codertectura-sql  westeurope   sqladmincoder
```

Después haría lo mismo con la base de datos:

```bash
az sql db list \
  --resource-group rg-codertectura-sql \
  --server sql-codertectura-dev \
  --output table  # Así confirmo que la base quedó asociada al servidor correcto
```

La salida debería incluir el nombre de la base y su estado.

```text
Name                 Status    Location
-------------------  --------  -----------
appdb-catalog        Online    westeurope
```

### Paso 2: conectar desde VS Code y ejecutar una consulta útil

Crear la base desde el editor está bien, pero lo importante viene justo después: seguir trabajando sin romper el flujo. La [guía oficial para conectar y consultar Azure SQL Database o SQL Managed Instance desde VS Code](https://learn.microsoft.com/en-us/azure/azure-sql/database/connect-query-vscode?view=azuresql) explica el recorrido base, y aquí es donde la extensión MSSQL me parece más práctica para desarrollo real de aplicaciones.

En VS Code, crea una conexión nueva desde la extensión. Introduce el servidor, la base de datos y el método de autenticación que corresponda a tu caso. Si vas a reutilizarla, guárdala. Y si estás trabajando desde una red o una IP nueva, ten presente que puede que necesites permitir el acceso en el firewall del servidor SQL.

Yo también suelo comprobar esa parte desde terminal. Me ayuda a distinguir entre “la base existe” y “mi entorno actual puede hablar con ella”. No es lo mismo, y conviene no mezclarlo.

```bash
MY_IP=$(curl -s https://api.ipify.org)
az sql server firewall-rule create \
  --resource-group rg-codertectura-sql \
  --server sql-codertectura-dev \
  --name vscode-client \
  --start-ip-address "$MY_IP" \
  --end-ip-address "$MY_IP"  # Uso la misma IP de inicio y fin para limitar el acceso a mi cliente actual
```

Si todo va bien, verás un JSON con la regla creada y la IP aplicada.

```json
{
  "endIpAddress": "83.45.120.18",
  "id": "/subscriptions/11111111-2222-3333-4444-555555555555/resourceGroups/rg-codertectura-sql/providers/Microsoft.Sql/servers/sql-codertectura-dev/firewallRules/vscode-client",
  "name": "vscode-client",
  "startIpAddress": "83.45.120.18"
}
```

{{< figure src="/images/azure-sql-y-formateo-sql-en-vs-code-menos-friccion-mas-flujo-real-con-la-extensi/source-2.webp" alt="Consulta SQL ejecutándose en la extensión MSSQL" caption="Con la conexión abierta en VS Code, puedo consultar Azure SQL Database y navegar objetos sin cambiar de herramienta. Fuente: [devblogs.microsoft.com](https://devblogs.microsoft.com/azure-sql/vscode-mssql-august2026)" >}}{{< /figure >}}

Una vez conectada la base en VS Code, yo haría una prueba pequeña pero con valor real: crear una tabla, insertar datos y consultar resultados. Nada de una query de adorno para sacar un `SELECT 1` y darnos palmadas en la espalda (que eso lo hemos hecho todos).

Crea un archivo `catalog-check.sql` y ejecuta algo como esto:

```sql
IF OBJECT_ID(N'dbo.ProductCatalog', N'U') IS NOT NULL
    DROP TABLE dbo.ProductCatalog;
GO

CREATE TABLE dbo.ProductCatalog (
    ProductId INT NOT NULL PRIMARY KEY,
    Name NVARCHAR(100) NOT NULL,
    MonthlyPrice DECIMAL(10,2) NOT NULL,
    IsActive BIT NOT NULL,
    CONSTRAINT CK_ProductCatalog_MonthlyPrice_NonNegative
        CHECK (MonthlyPrice >= 0) -- Evita datos inválidos ya en esta prueba mínima
);
GO

INSERT INTO dbo.ProductCatalog (ProductId, Name, MonthlyPrice, IsActive)
VALUES
    (1, N'Starter API', 19.90, 1),
    (2, N'Team API', 49.90, 1),
    (3, N'Legacy Sync', 9.90, 0);
GO

SELECT Name, MonthlyPrice
FROM dbo.ProductCatalog
WHERE IsActive = 1
ORDER BY MonthlyPrice DESC;
GO
```

Si todo está correcto, la extensión debería mostrar la ejecución satisfactoria de los lotes y, al final, una rejilla de resultados con dos filas: `Team API` y `Starter API`.

### Paso 3: usar el nuevo SQL Formatter y dejar de discutir por estilo

La otra novedad es menos espectacular en una demo, pero en un repositorio real puede tener un impacto inmediato: el nuevo **SQL Formatter**. La [actualización de agosto de la extensión MSSQL](https://devblogs.microsoft.com/azure-sql/vscode-mssql-august2026) menciona tanto la llegada del formateador como sus opciones de configuración. Y eso, si trabajas con migraciones, scripts de soporte o consultas que acaban pasando por revisión de código, importa bastante más de lo que parece.

Mi opinión aquí es muy simple: **formatear SQL no es estética, es legibilidad operativa**. Cuando una query está mal estructurada, cuesta más revisar joins, filtros, ordenaciones y condiciones. Y cuando cada persona escribe con un criterio distinto, Git se llena de diffs ruidosos que no cuentan nada útil.

Yo prefiero dejar esta configuración explícita en el espacio de trabajo para que el criterio sea compartido. En `.vscode/settings.json`, con la extensión MSSQL instalada, una base razonable sería esta:

```json
{
  "mssql.format.enabled": true,
  "mssql.format.keywordCase": "upper",
  "mssql.format.placeSelectStatementReferencesOnNewLine": true,
  "mssql.format.placeWhereClauseConditionsOnNewLine": true
}
```

Después, abre un script desordenado y ejecuta el comando de formateo desde la paleta de VS Code. Lo interesante aquí no es solo el resultado visual: también cambia mucho cómo revisas la intención de la consulta.

Por ejemplo, parte de algo así:

```sql
select p.ProductId,p.Name,p.MonthlyPrice from dbo.ProductCatalog p inner join dbo.ProductCatalog p2 on p.ProductId=p2.ProductId where p.IsActive=1 and p.MonthlyPrice>10 order by p.MonthlyPrice desc;
```

Tras aplicar el formateador, deberías ver algo muy parecido a esto:

```sql
SELECT
    p.ProductId,
    p.Name,
    p.MonthlyPrice
FROM dbo.ProductCatalog p
INNER JOIN dbo.ProductCatalog p2
    ON p.ProductId = p2.ProductId
WHERE
    p.IsActive = 1
    AND p.MonthlyPrice > 10
ORDER BY p.MonthlyPrice DESC;
```

{{< figure src="/images/azure-sql-y-formateo-sql-en-vs-code-menos-friccion-mas-flujo-real-con-la-extensi/source-3.webp" alt="Opciones del SQL Formatter en VS Code" caption="El nuevo formateador de SQL añade configuración desde VS Code para normalizar estilo y mejorar la legibilidad de las consultas. Fuente: [devblogs.microsoft.com](https://devblogs.microsoft.com/azure-sql/vscode-mssql-august2026)" >}}{{< /figure >}}

Y aquí está la parte interesante: una vez ordenada, la consulta te “habla” mejor. Ves enseguida que ese `JOIN` sobre la misma tabla y la misma clave probablemente sobra, o al menos merece una segunda mirada. **Un buen formateo no arregla una mala query, pero sí la deja sin escondites**.

### Un detalle práctico: atajos para tareas repetidas

La [visión general de la extensión MSSQL](https://learn.microsoft.com/en-us/sql/tools/visual-studio-code-extensions/mssql/mssql-extension-visual-studio-code?view=sql-server-ver17) también deja ver que la extensión incluye opciones pensadas para productividad, como accesos directos y configuraciones rápidas. Esto me parece especialmente útil cuando haces siempre las mismas comprobaciones: abrir una consulta nueva, explorar objetos, refrescar el explorador o trabajar sobre una conexión guardada.

No es la típica funcionalidad con nombre rimbombante de presentación comercial. Pero sí es de esas mejoras que, sumadas, hacen que la herramienta moleste menos. Y cuando estoy depurando una aplicación, cualquier cosa que reduzca clics tontos y errores de contexto me parece bienvenida.

{{< figure src="/images/azure-sql-y-formateo-sql-en-vs-code-menos-friccion-mas-flujo-real-con-la-extensi/body-4.png" alt="Diagrama del flujo de trabajo con MSSQL en VS Code" caption="Resumen del flujo recomendado: crear la base en Azure, abrir acceso, conectar desde VS Code, ejecutar T-SQL y aplicar formato al script." >}}{{< /figure >}}

### Dónde encaja esto en una aplicación real

Si me preguntas quién se beneficia más de esta actualización, yo no pensaría primero en el DBA clásico. Pensaría en el desarrollador de backend o en quien mantiene una plataforma de aplicación. El caso habitual es bastante reconocible: empiezas con una base local, validas un modelo, montas unas cuantas consultas, y en cuanto la cosa deja de ser una prueba aislada necesitas un destino más serio. Ahí es donde tiene sentido lo que plantea [el salto desde SQL Server Express a Azure SQL Database](https://devblogs.microsoft.com/azure-sql/upgrade-from-sql-server-express-to-azure-sql-database/).

El cambio de fondo, para mí, es este: VS Code deja de ser solo el sitio donde escribo consultas y pasa a ser también el punto desde el que creo, conecto, verifico y mantengo el SQL de trabajo. **Menos herramienta satélite, más continuidad mental**. Y eso, en el día a día, vale bastante.

### Mi conclusión

Yo no vendería esto como una revolución. No hace falta exagerar para que sea útil. Pero sí me parece una mejora muy bien enfocada: aprovisionar Azure SQL Database desde VS Code elimina un salto innecesario en el momento justo, y el formateador de SQL ataca un problema pequeño, constante y muy real, que es el deterioro del SQL con el paso del tiempo.

Si ya usas VS Code para tu backend en .NET, para APIs o para utilidades internas, creo que merece la pena probar este flujo cuanto antes. Empieza por algo pequeño: crea una base en Azure, conecta desde la extensión, ejecuta un script real y formatea un par de consultas del repositorio. En media hora sabrás si encaja contigo.

Mi apuesta es que sí.

Y si vienes de una etapa de prototipos locales, este puede ser justo el empujón práctico que faltaba para pasar de «funciona en mi máquina» a «funciona en un servicio gestionado» sin convertirlo en una ceremonia.
