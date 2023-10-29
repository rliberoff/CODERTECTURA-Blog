---
title: "Referencias de Proyectos Dependientes del Modo de Compilación"
excerpt: "***Legacy*** - Veamos una de las formas que tenemos en soluciones de .NET de elegir que referencias a proyectos o librerías NuGet queremos utilizar en base al modo de compilación que estemos usando, tal que se usen ciertas referencias si estamos en modo *Release*, y otras si estamos en modo *Debug*."
date: 2013-07-01 00:00:00 +0200
last_modified_at: 2023-10-29 00:00:00 +0200
layout: post
image:
    path: /images/2008-03-07-realizaciones-o-de-cuando-me-fui-de-venezuela/header.avif
    thumbnail: /images/2008-03-07-realizaciones-o-de-cuando-me-fui-de-venezuela/thumbnail.avif
categories:
    - Legacy
    - Tutorial
    - Visual Studio
---

{% capture notice-text %}
*Este tutorial es sobre una aproximación en C# para poder establecer que referencias (librerías) utilizar si estamos compilando la soludión en modo «Release» o en modo «Debug»*

*Este es uno de mis artículos «legacy» que mantengo en este blog como un recuerdo de mi recorrido profesional y técnico. Es probable que hoy día exista un mecanismo mejor para hacer ésto.*
{% endcapture %}

<div class="notice--warning" style="font-size: small; font-weight: bold;">
  {{ notice-text | markdownify }}
</div>

Una de las cosas que más me gustan de la plataforma .NET y del Visual Studio es la gestión de referencias a otras librerías o entre proyectos dentro de una misma solución. Y ni de que hablar que desde que vio a la luz la plataforma NuGet, el tema de gestión y distribución de estas librerías se ha convertido en todo un paseo por el campo, ya que no es necesario indicar que librerías tiene que tener instalado o descargado los desarrolladores, sino que la solución (apropiadamente configurada) se encargará de recuperar los archivos correspondientes durante la primera compilación de forma automática… toda una maravilla!

Sin embargo, y en particular, al trabajar con librerías de terceras partes o *third party libraries* que no estén disponibles a través de NuGet, existen diversas estrategias que ya se empleaban desde los principios de .NET. La que personal y profesionalmente considero la más apropiada es la de crear una carpeta `Lib` en la raíz del directorio que contiene al archivo de solución (`.sln`) e ir colocando allí los diferentes archivos `dll` que se van a emplear.

<figure class="align-center">
  <a href="{{ '/images/2013-07-01-referencias-proyectos-dependientes-modo-compilacion/file-system.png' | absolute_url }}" target="_blank" rel="noopener">
    <img src="{{ '/images/2013-07-01-referencias-proyectos-dependientes-modo-compilacion/file-system.png' | absolute_url }}" alt="Diagrama de Clases">
  </a>
  <figcaption>Haz click para ver la imagen más grande.</figcaption>
</figure>

La parte final sería agregar el contenido de la carpeta `Lib` a la solución (a través de las funcionalidades de *Add solution's folder* y de *Add existing item...*) para poder gestionar estas referencias a través del repositorio de versiones que empleemos: TFS, GitHub, SVN, o cualquier otro.

Pero… ¿Qué pasa si la version de librería de terceros que necesitamos emplear debe ser diferente en tiempo de desarrollo que en tiempo de despliegue/producción? ¿Cómo se gestiona una referencia a dos archivos `dll` diferentes dentro de un mismo proyecto y solución?

En principio no se puede. La referencia es exclusive a un archivo `dll` y a una versión de éste en específico, lo cual plantea un inconveniente que la mayoría de las personas termina resolviendo a través de dudosas prácticas y aún peores estrategias. Otros directamente culpan al Visual Studio y alegan que en otros IDEs es fácil hacer algo como ésto.

El problema es que esta necesidad es tan poco común que pocas personas en una empresa saben como resolverlo, pero la verdad es que es muy fácil a través del Visual Studio y de `MSBUILD`.

### Solución

Supongamos que necesitamos referenciar una lirabría llamada `My.Special.Library` en una version especifica cunado compilamos en `DEBUG` y en una versión diferente cuando compilamos en `RELEASE`. Los pasos serían los siguientes:

1. Desde el sistema de archivos navegamos hasta el directorio de la solución, y buscamos el directorio especial `Lib`.
2. Dentro de `Lib` creamos dos nuevos directorios: `Debug` y `Release`.
3. Colocamos en cada nuevo directorio la versión de la libraría de terceros (en nuestro ejemplo `My.Special.Library`) donde corresponda, tal que la versión que queremos para el modo `DEBUG` esté en el directorio `Debug`, y de igual manera para el caso del modo `RELEASE`.
4. Es importante desde el Visual Studio crear dos «Solution Folders» adicionales dentro del «Solution Folder» de `Lib` para mapear los directorios `Debug` y `Release` así como su contenido para poder gestionarlos a través de nuestro correspondiente sistema de gestión de versiones.

<figure class="align-center">
  <a href="{{ '/images/2013-07-01-referencias-proyectos-dependientes-modo-compilacion/lib.png' | absolute_url }}" target="_blank" rel="noopener">
    <img src="{{ '/images/2013-07-01-referencias-proyectos-dependientes-modo-compilacion/lib.png' | absolute_url }}" alt="Diagrama de Clases">
  </a>
  <figcaption>Haz click para ver la imagen más grande.</figcaption>
</figure>

{:start="5"}
5. Luego, desde el Visual Studio, seleccionamos el proyecto que queremos trabajar desde el «Solutio Explorer».
6. Hacemos *right-click* sobre el proyecto y elegimos la opción de «Unload project».
7. Una vez que el proyecto a sido *descargado*, hacemos nuevamente *right-click* y elegimos la opción de editar el archivo `.csproj`.
8.  Se nos mostrará el XML que conforma el `MSBUILD` del proyecto. Allí debemos buscar donde comienzan las inclusions de las referencias en el proyecto, lo cual es fácil de identificar porque son una sucesión de *tags* `Reference`.
9.  Debemos colocar la siguientes instrucciones (XML) justo antes del `ItemGroup` que contiene las referencias:

```xml
<Choose>
    <When Condition="'$(Configuration)'=='Debug'">
      <ItemGroup>
        <Reference Include="My.Special.Library, Version=1.222.2033.0, Culture=neutral, PublicKeyToken=26e441566366f4ab">
           <SpecificVersion>False</SpecificVersion>
          <HintPath>..\Lib\Debug\My.Special.Library.dll</HintPath>
        </Reference>
      </ItemGroup>
    </When>
     <Otherwise>
      <ItemGroup>
        <Reference Include="My.Special.Library, Version=1.342.2035.0, Culture=neutral, PublicKeyToken=26e441566366f4ab">
          <SpecificVersion>False</SpecificVersion>
           <HintPath>..\Lib\Release\My.Special.Library.dll</HintPath>
        </Reference>
      </ItemGroup>
    </Otherwise>
</Choose>
```

{:start="10"}
10. Salvamos el archivo `.csproj`.
11. Hacemos de nuevo *right-click* sobre el proyecto desde el «Solution Explorer» y ahora elegimos la opción de «Reload Project». Si el Visual Studio nos pregunta para cerrar el archivo `.csproj`, le contestamos que «Si».

Y listo, ya tenemos configurado el proyecto para que considerere una versión u otra de la librería de terceros dependiendo del modo de compilación, sin tener que hacer nada más, todo de forma automática y transparente.

Lo más interesante de esta solución es que la referencia se actualiza automáticamente y sin interrupciones en el proyecto que la contenga cuando cambiamos de modos de compilación desde el Visual Studio. Así, si estamos en el modo `DEBUG`, se estará referenciando a la version `1.222.2033.0`, pero si cambiamos a otro modo (digamos `RELEASE`) automáticamente y sin enterarnos se actualizará la referencia del proyecto para utilizer la version `1.342.2035.0`.

Por otro lado, no es estrictamente necesario tener que realizar la selección de una versián u otra si estamos en modo `DEBUG` o no, ya que como Visual Studio y el compilador de C# soportan variables de compilación, podemos definir nuestras porpias variables y emplear éstas para determiner que libraría y versión referenciar en nuestros proyectos.

Espero que este truco les sea de utilidad.
