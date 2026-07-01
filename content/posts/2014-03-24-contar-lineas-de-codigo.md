---
slug: contar-lineas-de-codigo
title: "Contar Líneas de Código"
excerpt: "Contar líneas de código no necesariamente puede considerarse como una métrica fiable de la calidad del código. No por tener más o por tener menos líneas de código un sistema es mejor o peor. Sin embargo, no deja de ser una métrica importante parea ciertos escenarios, y quizás sea una de las más antiguas."
date: 2014-03-24 00:00:00 +0200
lastmod: 2023-10-29 00:00:00 +0200
url: "/posts/contar-lineas-de-codigo/"
image:
    path: /images/2014-03-24-contar-lineas-de-codigo/header.png
    thumbnail: /images/2014-03-24-contar-lineas-de-codigo/thumbnail.png
categories:
    - Visual Studio
---

Contar líneas de código no necesariamente puede considerarse como una métrica fiable de la calidad del código. No por tener más o por tener menos líneas de código un sistema es mejor o peor. Sin embargo, no deja de ser una métrica importante parea ciertos escenarios, y quizás sea una de las más antiguas, tanto que existen registros de esta práctica desde de 1970 más o menos.

Por ejemplo, de acuerdo con el Centro Tecnológico de Calidad de Software (Software Assurance Technology Center – SATC) de la NASA:

<p style="color:#696969; text-align: center;">«*El tamaño es una de las formas más antiguas y comunes de medición de software. El tamaño de los módulos es en sí misma un indicador de calidad. El tamaño puede ser medido a través del total de líneas de código, contando todas las líneas; que no correspondan a comentarios y que no esté en blanco, disminuyendo las líneas totales, por el número de espacios en blanco y comentarios, y todas aquellas sentencias ejecutables que se definen por un delimitador dependiente del lenguaje de programación.*»</p>

{{< figure src="/images/2014-03-24-contar-lineas-de-codigo/nasa.jpg" alt="image-center" class="align-center" imageClass="image-border" imageStyle="width: 400;" >}}{{< /figure >}}

Sin embargo, con el paso del tiempo y medida que nuestra disciplina evolucionaba y maduraba, se determinó que por sí sólo el número de líneas de código en un proyecto de software no es un indicador de la calidad del mismo, o la productividad del trabajo realizado por los desarrolladores, si se podría afirmar que es una métrica confiable del tamaño real del proyecto. Habitualmente es una métrica que combinamos con índices como la Complejidad Ciclomática o el número de clases.

En el mundo de Visual Studio contamos con una funcionalidad denominada Code Metrics la cual nos muestra una serie de estadísticas muy útiles sobre nuestra solución y sus proyectos. Entre estas métricas está la cuenta de líneas de código.

{{< figure src="/images/2014-03-24-contar-lineas-de-codigo/metrics.png" class="align-center" caption="Haz click para ver la imagen más grande." >}}{{< /figure >}}

Ahora, esta cuenta no es exactamente todas las líneas de código de nuestra solución (o proyecto), sino una cuenta aproximada basada en el código IL generado por la compilación (vamos, más o menos lo que hace la NASA). Éste índice como tal es bastante útil en determinar si un método está haciendo más de lo que debe, pues aún cuando un método tenga cientos de líneas de código físico, la compilación puede hacer que el número de líneas sea radicalmente menos, y si el mismo no baja, puede indicar una pobre o inapropiada mantenibilidad del método.

Cuando necesito conocer las líneas reales de código fuente, su tipo (código, comentario o línea en blanco) y su distribución (SQL, XML, ASP.NET o C#) empleo y recomiendo un pequeño programa llamado <a href="https://github.com/AlDanial/cloc" target="_blank" rel="noopener noreferrer">CLOC</a>, el cual no requiere instalacieon, es súper fácil de usar y soporta <a href="https://github.com/AlDanial/cloc#recognized-languages-" target="_blank" rel="noopener noreferrer">cientos de tecnologías y lenguajes de programación</a>, incluyendo C#, ASP.NET, VB.NET y muchos más.

{{< figure src="/images/2014-03-24-contar-lineas-de-codigo/count.png" alt="image-center" class="align-center" >}}{{< /figure >}}

Entre sus características básicas, me es muy útil que es capaz de reconocer el número de líneas blancas dentro de código, y aquellas que se corresponden a texto de documentación y comentarios, con lo cual se puede obtener métricas, ahora si de la calidad del código, sobre cuanto documentado este puede estar. Por ejemplo, imaginen un código fuente sin ninguna documentación. A través de una aplicación como CLOC podríamos determinar esto y así levantar la correspondiente incidencia.

Otras característica interesante es que se puede obtener un reporte de líneas de código por archivo o por lenguaje.

El reporte puede exportarse a un archivo separado por comas, a XML e incluso en sentencias de SQL que pueden ser útiles para inyectar en una base de datos de reportes de estado y salud del proyecto.

Profesionalmente, al realizar auditorias técnicas complemento el resultado del Code Metrics del Visual Studio con los resultados de CLOC. De esa forma puedo ofrecer una fotografía completa de la mantenibilidad del código versus cuanto está escrito, cuanto es espacio vacío y que tanta documentación podríamos encontrar.
