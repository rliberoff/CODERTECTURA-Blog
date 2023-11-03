---
title: "Evitar la ventana de \"Adjuntar Advertencia de Seguridad\""
excerpt: "A veces cuando trabajamos con referencias a servicios web, el Visual Studio nos puede mostrar una ventana muy molesta con una advertencia de seguridad. Veamos como podemos gestionar esta fastidiosa advertencia."
date: 2012-07-24 00:00:00 +0200
last_modified_at: 2023-11-01 00:00:00 +0200
layout: post
permalink: /posts/evitar-ventana-adjuntar-advertencia-de-seguridad
image:
    path: /images/2012-07-24-evitar-ventana-adjuntar-advertencia-seguridad/header.jpg
    thumbnail: /images/2012-07-24-evitar-ventana-adjuntar-advertencia-seguridad/thumbnail.jpg
categories:
    - Legacy    
    - Visual Studio
---
Hoy día ya es casi asumible que todo sistema tendrá en su arquitectura uno o más componentes de servicios, habitualmente servicios web. En la plataforma .NET, los servicios web vienen en muchas formas siendo las dos más habituales los ASMX y los SVC (WCF Web Services).

Resulta que con el Windows 7 y el Visual Studio 2008/2010 cuando trabajamos con referencias a servicios web de WCF nos suele saltar la siguiente ventana al depurar la aplicación:

![center-aligned-image](/images/2012-07-24-evitar-ventana-adjuntar-advertencia-seguridad/1.png){: .align-center}

Particularmente esta ventana no supone nada malo. Es una simple advertencia del sistema operativo en la que nos informa de que un usuario *X* trata de depurar un proceso *Y*.

El problema es que un proceso normal de desarrollo involucra incontables sesiones de depuración, lo que eventualmente conlleva a odiar esta advertencia…

La solución formal y correcta resulta ser bastante sencilla (más allá de estar tocando el registro de Windows). Hay que seguir los siguientes pasos:

1. Abrir la cónsola de gestión del IIS (simplemente ejecutar el comando inetmgr).
2. Posicionarse sobre el grupo de aplicaciones (*Application Pool*).
3. Seleccionar el grupo de aplicaciones sobre el cual se ejecuta el componente de servicios web de nuestro sistema.
4. Con el botón derecho del mouse elige la opción de «Opciones Avanzadas».
5. En la ventana que aparece, buscamos el apartado de «Identidad» y hacemos click en el botón con los puntos suspensivos (‘…’).
6. En la nueva ventana emergente, seleccionamos del desplegable de cuentas integradas la opción de «NetworkService».

![center-aligned-image](/images/2012-07-24-evitar-ventana-adjuntar-advertencia-seguridad/2.webp){: .align-center}

{:start="7"}
7. Salimos de estas ventanas, y desde una línea de comando con derechos de administrador ejecutamos un reset del IIS (simplemente ejecutar el comando `iisreset`).

Y santo remedio. Ahora cuando depuremos una aplicación que emplea referencias a servicios web de WCF o cualquier otra integración con otro sistema al cual deba anexarse el depurador no nos saldrá la advertencia de seguridad.
