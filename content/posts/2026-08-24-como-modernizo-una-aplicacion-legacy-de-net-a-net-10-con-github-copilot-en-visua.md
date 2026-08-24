---
title: Cómo modernizo una aplicación legacy de .NET a .NET 10 con GitHub Copilot en
  Visual Studio
date: '2026-08-24T06:57:52+00:00'
draft: true
slug: como-modernizo-una-aplicacion-legacy-de-net-a-net-10-con-github-copilot-en-visua
description: Te muestro cómo afronto la modernización de una solución en .NET Framework
  a .NET 10 con GitHub Copilot en Visual Studio, revisando el plan y validando los
  cambios de verdad.
categories:
- .NET
- Arquitectura de Software
- Azure
tags:
- GitHub Copilot
- Visual Studio
- .NET 10
- Modernización
- .NET Framework
- Migración
image: /images/como-modernizo-una-aplicacion-legacy-de-net-a-net-10-con-github-copilot-en-visua/cover.png
comments: true
ai:
  assisted: true
  article_type: technical
  model: gpt-5.4
  prompt_version: 2026-08-21.1
  generated_at: '2026-08-24T06:57:52+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://devblogs.microsoft.com/visualstudio/today-i-will-modernize-a-net-application/
    title: Today I will… Modernize a .NET application
    published_date: '2026-08-21'
  - url: https://learn.microsoft.com/en-us/dotnet/core/porting/github-copilot-upgrade/scenarios-and-skills
    title: GitHub Copilot upgrade scenarios and skills - .NET Core
    published_date: null
  - url: https://learn.microsoft.com/en-us/dotnet/azure/migration/appmod/faq
    title: GitHub Copilot modernization for .NET FAQ | Microsoft Learn
    published_date: null
  - url: https://learn.microsoft.com/en-us/dotnet/core/porting/github-copilot-upgrade/overview
    title: GitHub Copilot upgrade overview
    published_date: null
  - url: https://learn.microsoft.com/en-us/dotnet/core/porting/github-copilot-upgrade/install
    title: Install GitHub Copilot upgrade - .NET Core | Microsoft Learn
    published_date: null
---

Modernizar una aplicación legacy de .NET ya no va solo de cambiar el `TargetFramework` y pasarte dos semanas peleándote con errores de compilación. Lo interesante del nuevo enfoque con GitHub Copilot en Visual Studio es otra cosa: **convierte la migración en un flujo guiado**, con evaluación, plan, ejecución y validación dentro del propio IDE. Si tú sigues manteniendo soluciones en .NET Framework y nunca encuentras el momento para actualizarlas sin romper algo importante, aquí es donde yo sí veo valor inmediato.

En este artículo te voy a enseñar un recorrido práctico y realista: cómo arranco la modernización desde Visual Studio, qué le pido exactamente al agente, cómo reviso el plan de salto a .NET 10, qué cambios espero ver en los proyectos y cómo dejo la solución mejor preparada para un paso posterior hacia Azure. Me voy a centrar en el flujo dentro de Visual Studio, apoyándome en lo que Microsoft explica sobre [GitHub Copilot upgrade](https://learn.microsoft.com/en-us/dotnet/core/porting/github-copilot-upgrade/overview), en sus [escenarios y *skills*](https://learn.microsoft.com/en-us/dotnet/core/porting/github-copilot-upgrade/scenarios-and-skills) y en la [FAQ de modernización para .NET y Azure](https://learn.microsoft.com/en-us/dotnet/azure/migration/appmod/faq).

### Antes de empezar

Para reproducir este flujo, yo partiría de unos requisitos bastante concretos:

- Windows.
- [Visual Studio 2026 o Visual Studio 2022 17.14.17 o superior](https://learn.microsoft.com/en-us/dotnet/core/porting/github-copilot-upgrade/install).
- El workload **.NET desktop development** con los componentes opcionales **GitHub Copilot** y **GitHub Copilot app modernization** habilitados, tal y como indica la guía de [instalación de GitHub Copilot upgrade](https://learn.microsoft.com/en-us/dotnet/core/porting/github-copilot-upgrade/install).
- Una suscripción válida de GitHub Copilot; según la [FAQ de modernización](https://learn.microsoft.com/en-us/dotnet/azure/migration/appmod/faq), puede ser Free, Pro, Pro+, Business o Enterprise, según versión y entorno.
- Haber iniciado sesión en Visual Studio con una cuenta de GitHub con acceso a Copilot.
- Una solución legacy escrita en C# o Visual Basic, idealmente bajo Git local. La propia [FAQ](https://learn.microsoft.com/en-us/dotnet/azure/migration/appmod/faq) deja claro que el agente trabaja sobre una rama dentro de un repositorio Git local.
- El SDK de .NET 10 instalado para compilar y validar el resultado fuera del IDE.

Yo suelo comprobar esto último antes de tocar nada. No porque sea sofisticado, sino porque me ahorro una cantidad absurda de tiempo evitando diagnósticos falsos.

```bash
# Verifico que el SDK de .NET 10 está instalado y disponible para la compilación real del upgrade
 dotnet --list-sdks
```

La salida debería incluir una línea con la versión 10.x del SDK, por ejemplo:

```text
8.0.xxx [C:\Program Files\dotnet\sdk]
10.0.xxx [C:\Program Files\dotnet\sdk]
```

### Qué hace realmente Copilot durante la modernización

Aquí hay un matiz importante. No estás invocando un autocompletado con esteroides, sino un agente con escenarios de upgrade. Según la [visión general de GitHub Copilot upgrade](https://learn.microsoft.com/en-us/dotnet/core/porting/github-copilot-upgrade/overview), el flujo se organiza alrededor de evaluación, recomendaciones, correcciones de código y validación. Y cuando tú pides algo tan directo como “Upgrade my solution to .NET 10”, el agente encadena las *skills* adecuadas en función de lo que encuentre.

Eso me parece clave por una razón muy simple: en una solución corporativa casi nunca falla solo el framework. Suelen aparecer proyectos antiguos en formato no SDK, paquetes NuGet obsoletos, referencias a `System.Configuration`, serialización heredada, acceso a datos con proveedores viejos o dependencias que bloquean la compilación a mitad de camino. **El valor no está en automatizar el clic; está en automatizar el diagnóstico con contexto.**

{{< figure src="/images/como-modernizo-una-aplicacion-legacy-de-net-a-net-10-con-github-copilot-en-visua/body-1.png" alt="Diagrama del flujo de modernización en Visual Studio" caption="Flujo práctico de modernización: evaluación, plan, ejecución de cambios y validación en Visual Studio con Copilot." >}}{{< /figure >}}

Además, la [referencia de escenarios y *skills*](https://learn.microsoft.com/en-us/dotnet/core/porting/github-copilot-upgrade/scenarios-and-skills) describe justo ese modelo: los escenarios gestionan el flujo de extremo a extremo, y las *skills* se activan para tareas concretas, como convertir a SDK-style o actualizar `SqlClient`. Traducido a lenguaje de trinchera: yo no tengo que memorizar el nombre exacto de cada herramienta interna; le explico la intención y el agente decide por dónde empezar. Y sí, eso está bastante bien pensado.

### Paso 1: abrir la solución y arrancar el escenario de modernización

Una vez tengo la solución abierta en Visual Studio, puedo empezar de dos formas, tal como recoge la [documentación de instalación](https://learn.microsoft.com/en-us/dotnet/core/porting/github-copilot-upgrade/install):

- Clic derecho sobre el proyecto en **Solution Explorer** → **Modernize**.
- O abrir **GitHub Copilot Chat** y escribir `@Modernize`.

Yo prefiero el chat porque me deja ser mucho más explícito con lo que quiero y con el orden en el que quiero hacerlo. Un prompt razonable para una solución en .NET Framework que quiero llevar a .NET 10 sería este:

```text
@Modernize Upgrade my solution to .NET 10. Start with an assessment, propose a plan, convert legacy project files to SDK-style if needed, and highlight breaking changes before applying fixes.
```

Lo que yo esperaría ver a continuación es:

- Un resumen de la solución analizada,
- Una propuesta de escenario de modernización,
- Una lista de tareas o fases,
- Y normalmente la sugerencia de trabajar en una rama específica.

Según la [FAQ de modernización](https://learn.microsoft.com/en-us/dotnet/azure/migration/appmod/faq), el agente analiza proyectos, propone un plan, ejecuta tareas, corrige incidencias automáticamente y te deja acceso a logs y cambios. Ese detalle para mí importa mucho, porque **no te obliga a tragarte una caja negra**. Puedes revisar qué toca antes de consolidarlo, que en una solución empresarial no es un lujo: es higiene básica.

### Paso 2: revisar el plan antes de tocar código

Mi consejo aquí es bastante directo: no lances la transformación “a ver qué pasa”. Primero revisa el plan. En este tipo de upgrades, el ahorro real no está en correr más, sino en separar bien los cambios:

1. Conversión estructural del proyecto,
2. Salto de framework,
3. Actualización de paquetes,
4. Corrección de incompatibilidades,
5. Validación.

Un plan típico puede incluir tareas como estas:

- Convertir `.csproj` antiguos al formato SDK-style.
- Cambiar el framework objetivo a `net10.0`.
- Sustituir referencias de ensamblado por `PackageReference` cuando corresponda.
- Detectar APIs incompatibles con .NET moderno.
- Actualizar paquetes de acceso a datos o serialización.
- Ejecutar compilación y pruebas para validar.

{{< figure src="/images/como-modernizo-una-aplicacion-legacy-de-net-a-net-10-con-github-copilot-en-visua/body-2.png" alt="Infografía del plan de upgrade a .NET 10" caption="La clave no es solo ejecutar cambios, sino revisar un plan por fases antes de aceptar la modernización." >}}{{< /figure >}}

Aquí encaja especialmente bien lo que Microsoft plantea en sus [escenarios y *skills*](https://learn.microsoft.com/en-us/dotnet/core/porting/github-copilot-upgrade/scenarios-and-skills). El escenario coordina el viaje completo, pero las *skills* atacan problemas concretos cuando aparecen. Si el agente encuentra un proyecto legacy, puede activar la conversión a SDK-style; si encuentra dependencias antiguas, puede proponer su actualización; y si detecta código especialmente problemático, lo marcará como riesgo antes de seguir. A mí me gusta este enfoque porque ordena el caos. Y en modernización, ordenar el caos ya es medio proyecto.

### Paso 3: inspeccionar el cambio clave en el proyecto

Uno de los cambios más visibles después de la modernización es el `.csproj`. Si vienes de un proyecto clásico de .NET Framework, el salto al formato SDK-style se nota enseguida: menos XML, menos ruido, menos puntos de rotura tontos. No es un detalle cosmético; es una mejora real de mantenibilidad.

Un resultado razonable en una aplicación web o librería moderna tras la migración a **.NET 10** podría quedar así:

```xml
<Project Sdk="Microsoft.NET.Sdk.Web">
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <GenerateAssemblyInfo>false</GenerateAssemblyInfo>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Microsoft.Data.SqlClient" Version="6.1.0" />
    <PackageReference Include="System.Configuration.ConfigurationManager" Version="10.0.0" />
  </ItemGroup>

  <ItemGroup>
    <Content Update="appsettings.json">
      <CopyToOutputDirectory>PreserveNewest</CopyToOutputDirectory> <!-- Mantengo el archivo disponible en salida mientras completo la transición de configuración -->
    </Content>
  </ItemGroup>
</Project>
```

¿Qué reviso yo aquí? Varias cosas. Primero, que el proyecto ya usa `Sdk="..."`. Segundo, que el `TargetFramework` sea realmente `net10.0`. Tercero, que hayan desaparecido muchas referencias manuales heredadas que antes vivían en el proyecto por pura inercia histórica. Y cuarto, que las dependencias reflejen un mundo moderno y no una excavación arqueológica.

Fíjate especialmente en `System.Configuration.ConfigurationManager`. En muchas aplicaciones legacy sigue haciendo falta leer configuración clásica durante una fase de transición. No es la solución ideal a largo plazo, desde luego, pero sí una forma pragmática de avanzar sin bloquear todo el upgrade el primer día. Y yo, personalmente, prefiero una transición limpia a una reescritura heroica que nunca llega a producción.

### Paso 4: compilar y detectar incompatibilidades reales

Cuando Copilot termina una tanda de cambios, yo no me fío del “parece que ya está”. Compilo. Siempre. Si estoy en Visual Studio, puedo hacerlo desde el IDE, pero además me gusta validar con CLI porque me da una señal reproducible fuera del entorno interactivo.

```bash
# Valido la solución completa en Release para detectar incompatibilidades que no quiero descubrir más tarde en CI
 dotnet build .\CustomerPortal.sln -c Release
```

Si la modernización principal ha ido bien, deberías ver algo parecido a esto:

```text
Restore completed in 2.1 sec for C:\src\CustomerPortal\CustomerPortal.Web\CustomerPortal.Web.csproj.
CustomerPortal.Core -> C:\src\CustomerPortal\CustomerPortal.Core\bin\Release\net10.0\CustomerPortal.Core.dll
CustomerPortal.Web -> C:\src\CustomerPortal\CustomerPortal.Web\bin\Release\net10.0\CustomerPortal.Web.dll
Build succeeded.
    0 Warning(s)
    0 Error(s)
```

Si aparecen errores, yo no lo interpretaría como un fracaso del agente. Normalmente significa que has llegado a la parte importante: las incompatibilidades específicas de tu código. Y ahí es donde empieza el trabajo de verdad. Suelen salir cosas como estas:

- Uso de APIs de `System.Web`,
- Dependencias no disponibles en .NET moderno,
- Configuración que ahora debería vivir en `appsettings.json`,
- O paquetes antiguos que necesitan sustitución.

En ese punto, Copilot sigue siendo útil, pero ya no con una orden generalista, sino con prompts mucho más acotados. Por ejemplo: “replace System.Data.SqlClient with Microsoft.Data.SqlClient” o “move appSettings usage to IConfiguration”. De hecho, eso encaja directamente con los escenarios descritos en la [visión general del agente](https://learn.microsoft.com/en-us/dotnet/core/porting/github-copilot-upgrade/overview). **La automatización funciona mejor cuando el problema ya está bien delimitado.**

### Paso 5: validar un cambio típico de código tras la modernización

Uno de los ajustes que más veces me encuentro en aplicaciones enterprise es el acceso a configuración. En código legacy, es muy normal ver algo como esto:

```csharp
using System;
using System.Configuration;
using Microsoft.Data.SqlClient;

public sealed class CustomerRepository
{
    public int CountActiveCustomers()
    {
        var settings = ConfigurationManager.ConnectionStrings["CustomerPortalDb"]
            ?? throw new InvalidOperationException("La cadena de conexión 'CustomerPortalDb' no está configurada.");

        using var connection = new SqlConnection(settings.ConnectionString);
        connection.Open();

        using var command = new SqlCommand(
            "SELECT COUNT(1) FROM Sales.Customers WHERE IsActive = 1",
            connection);

        return Convert.ToInt32(command.ExecuteScalar()); // Convierto de forma segura el escalar devuelto por ADO.NET durante la transición
    }
}
```

Este ejemplo sigue siendo perfectamente válido en **.NET 10** si has añadido los paquetes adecuados y mantienes esa cadena de conexión declarada. Lo que yo verificaría aquí es doble: por un lado, que el código compila usando `Microsoft.Data.SqlClient`; por otro, que ya no depende de `System.Data.SqlClient`, que suele ser uno de los pasos típicos de modernización. No es un cambio espectacular visualmente, pero sí elimina una dependencia heredada bastante frecuente.

Si ejecutas la aplicación y el repositorio funciona, la validación práctica es muy simple: la consulta devuelve el número de clientes activos sin lanzar excepciones de proveedor ni de configuración. Dicho así parece obvio (porque lo es), pero en migraciones largas a veces uno se emociona con el XML bonito y se olvida de probar la parte que realmente paga las facturas.

{{< figure src="/images/como-modernizo-una-aplicacion-legacy-de-net-a-net-10-con-github-copilot-en-visua/body-3.png" alt="Comparativa visual entre código legacy y código modernizado" caption="Un cambio típico tras la modernización: pasar de dependencias antiguas a paquetes y APIs compatibles con .NET 10." >}}{{< /figure >}}

### Paso 6: dejar la aplicación preparada para el siguiente salto a Azure

Aunque hoy me he centrado en el upgrade de runtime, hay un matiz importante en la [FAQ de modernización](https://learn.microsoft.com/en-us/dotnet/azure/migration/appmod/faq): el agente no piensa solo en actualizar .NET, también en preparar la aplicación para migración y modernización orientada a Azure. Y eso cambia bastante la conversación.

En mi experiencia, una modernización útil no termina cuando la solución compila en `net10.0`. Termina cuando has reducido la fricción para lo siguiente: externalizar configuración, sustituir dependencias locales por servicios gestionados y hacer que la aplicación sea más desplegable y más observable. Si no llegas a ese punto, has actualizado el runtime, sí, pero probablemente sigues arrastrando la mitad de los acoplamientos que te metieron en el problema original.

Un paso pequeño, pero muy práctico, es mover configuración hacia `appsettings.json` e `IConfiguration`, aunque mantengas compatibilidad temporal durante la transición. Por ejemplo:

```json
{
  "ConnectionStrings": {
    "CustomerPortalDb": "Server=tcp:sql-prod-01.database.windows.net,1433;Initial Catalog=CustomerPortal;Encrypt=True;TrustServerCertificate=False;Authentication=Active Directory Default;"
  },
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning"
    }
  }
}
```

Lo que yo esperaría ver después es que la aplicación empieza a consumir la configuración desde el modelo moderno de .NET y queda bastante mejor posicionada para alojarse en Azure App Service, en contenedores o en cualquier hosting actual. **Ese es el cambio estratégico de verdad**: no solo actualizar, sino ir quitando acoplamientos al pasado antes de que te vuelvan a pasar factura.

### Lo que yo sí revisaría manualmente aunque Copilot haga mucho trabajo

Aquí no voy a vender humo. El agente ayuda mucho, pero hay cosas que yo reviso siempre a mano:

- Autenticación y autorización,
- Serialización JSON y contratos públicos,
- Acceso a datos y proveedores concretos,
- *Jobs* en segundo plano o tareas programadas,
- Y comportamiento de configuración por entorno.

También revisaría los cambios de paquetes uno a uno. Un upgrade exitoso no es “compila”; es “compila y sigue comportándose como esperas”. Si tienes tests automatizados, este es el momento de exprimirlos sin piedad. Y si no los tienes, modernizar una solución crítica sin al menos unas pruebas de humo es jugar con fuego. No suena glamuroso, ya lo sé, pero tampoco lo es restaurar producción a las dos de la mañana.

{{< figure src="/images/como-modernizo-una-aplicacion-legacy-de-net-a-net-10-con-github-copilot-en-visua/body-4.png" alt="Diagrama de preparación de la aplicación para Azure" caption="Tras el upgrade de runtime, la siguiente ganancia es dejar la aplicación lista para una modernización seria hacia Azure." >}}{{< /figure >}}

### Mi conclusión práctica

Si me preguntas si merece la pena usar GitHub Copilot en Visual Studio para llevar una aplicación legacy a .NET 10, mi respuesta es sí, con un matiz importante: úsalo como **acelerador experto**, no como sustituto del criterio técnico. La combinación de evaluación, plan guiado, cambios automatizados y validación dentro del IDE reduce muchísimo el coste de arrancar una modernización que, de otro modo, suele eternizarse.

Lo que más valoro de este enfoque es que empieza justo donde más duele en empresa: soluciones heredadas, proyectos antiguos y dependencias difíciles de desenredar. Y además lo hace con un modelo de trabajo bastante sensato, apoyado en [Visual Studio](https://devblogs.microsoft.com/visualstudio/today-i-will-modernize-a-net-application/), en los [escenarios del agente de upgrade](https://learn.microsoft.com/en-us/dotnet/core/porting/github-copilot-upgrade/overview) y en la [capacidad de modernización orientada a Azure](https://learn.microsoft.com/en-us/dotnet/azure/migration/appmod/faq).

Si yo tuviera que plantear una hoja de ruta pragmática, iría así: primero upgrade guiado a .NET 10, después validación funcional, luego limpieza de dependencias legacy y, solo entonces, preparación seria para Azure. Hacerlo en ese orden evita mezclar demasiados riesgos a la vez, que es exactamente donde estas migraciones suelen torcerse.
