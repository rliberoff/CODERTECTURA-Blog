---
title: "¿Es GPT-4 capaz de pensar o ser consciente de sí mismo?"
excerpt: "Con la llegada del nuevo modelo GPT-4, cientos de veces más poderoso que el anterior, los científicos de datos se preguntan si al fin hemos conceguido una Inteligencia Artificial capaz de pensar por sí misma, o mostrar evidencias de una conciencia primitiva."
date: 2023-04-02 00:00:00 +0000
last_modified_at: 2023-10-29 00:00:00 +0000
layout: post
permalink: /posts/gpt-4-puede-pensar
image:
    path: /images/2023-04-02-es-gpt-4-capaz-de-pensar/header.png
    thumbnail: /images/2023-04-02-es-gpt-4-capaz-de-pensar/thumbnail.png
categories:
    - Divagaciones
    - Inteligencia Artificial
---

{% capture notice-text %}
Artítculo publicado originalmente en el blog [«Tranformación Digital»](https://blogs.encamina.com/transformacion-digital/es-gpt-4-capaz-de-pensar-o-ser-consciente-de-si-mismo/){:target="_blank"} de [ENCAMINA](https://www.encamina.com/){:target="_blank"}.
{% endcapture %}

<div class="notice--info" style="font-size: small; font-weight: bold;">
  {{ notice-text | markdownify }}
</div>

Desde que ChatGPT entró en diciembre de 2022 en nuestras vidas, no hemos tenido tregua escuchando cómo la Inteligencia Artificial (AI por sus siglas en inglés) está infiltrándose en diversos aspectos de nuestra vida diaria y profesional.

Recientemente (marzo de 2023) la gente de OpenAI liberó una nueva versión del algoritmo GPT, responsable del éxito y poder detrás del ChatGPT. La anterior versión, comúnmente conocida como GPT-3 (aunque realmente la versión es la 3.5), ha sido superada con creces por el nuevo GPT-4, más no ha sido reemplazada, pues sigue siendo útil para una variedad importante de situaciones, o también porque GPT-3 es, por ahora, significativamente más económica que GPT-4 💸

Como pasó en diciembre, esta nueva versión ha sorprendido por sus capacidades, hasta un punto tal que nos está haciendo pensar si al fin hemos conseguido una Inteligencia Artificial Generalista (AGI por sus siglas en inglés), que realmente sea capaz de pensar e incluso hasta de manifestar posibles evidencias de una conciencia primitiva.

Para contestar a estas cuestiones, que parecen más de ciencia ficción que de nuestra realidad, primero tenemos que preguntarnos lo siguiente:

- Como especie y como civilización, ¿qué entendemos por «inteligencia»?
- ¿Qué concebimos como «conciencia propia» o la esencia y significado del «ser»?
- ¿Cómo reconocemos que otros «son»?
- ¿Cómo reconocemos la «conciencia» en el mundo que nos rodea?

Es gracioso que para estos aspectos de nuestra vida que nos han acompañado como especie desde que existimos, realmente no estamos del todo seguros de qué es «ser», qué es la «conciencia» o qué es la «inteligencia».

Cuando le preguntaron a Alan Turing si los ordenadores (computadoras) piensan, él contestaba que «*Sí… sólo que piensa en su forma, no como tú o como yo*».

A lo largo de esta publicación, estaremos conversando sobre los experimentos y hallazgos publicados en el *paper* [“Sparks of Artificial General Intelligence: Early experiments with GPT-4”](https://arxiv.org/abs/2303.12712){:target="_blank"} que justamente busca determinar si GPT-4 como algoritmo, aplicación o sistema es «inteligente», e incluso si tiene algún nivel de «conciencia» primitiva. Es decir, si es capaz de pensar y de ser.

### La inteligencia de GPT-4

¿Qué es la inteligencia? Esta es una gran pregunta, y muy ambigua, para la que no hay una respuesta definitiva.

Hasta hace no mucho, se pensaba que sólo existía un tipo de inteligencia, que podía medirse mediante pruebas que nos clasificaba como genios brillantes, o todo lo contrario; y que muchas veces nos podían estar condenando a una ruta de vida que no es a la que aspirábamos.

En 1994, un grupo de 52 psicólogos intentaron capturar la esencia de la definición de inteligencia, y firmaron una publicación sobre la ciencia de la inteligencia[^1]. Dicho equipo, de forma consensuada definió a la inteligencia como «*una capacidad individual y general que, entre otras cosas, implica el potencial de razonar, planificar, resolver problemas, pensar de forma abstracta, comprender ideas complejas, y aprender de la experiencia*».

Gracias al trabajo de esos científicos, hoy día sabemos que existen múltiples tipos de inteligencias, y que todos tenemos una mezcla de diferentes niveles y variaciones de éstas. Podríamos imaginar que si los humanos tenemos diferentes tipos y niveles de inteligencia, entonces ***quizá las máquinas o los algoritmos como GPT-4 tengan la suya***, algo así como que lo decía Alan Turing.

No obstante, para algunos investigadores, esta definición de inteligencia parece ser demasiado antropocéntrica, o demasiado cercana al género humano, o insuficientemente operacionalizable. Por supuesto todo esto es opinable, ya que al conceptualizar la inteligencia es fácil concebir alternativas un tanto más filosóficas o metafísicas. De lo que tenemos que darnos cuenta al emplear este tipo de definiciones es la proyección de la aspiración que tenemos con este tipo de tecnologías: conseguir hablar con “alguien” que no es “nosotros”, que no es humano, y que podría evolucionar por vías diferentes a las nuestras, proporcionándonos nuevas perspectivas de la existencia. Más o menos lo que ocurría en el pasado cuando encontrábamos una nueva civilización… si es que no la destruíamos antes 😶

Por otro lado, la Inteligencia Artificial como disciplina y su relación con el razonamiento o la capacidad de resolver problemas, no es algo nuevo. En contraste a lo que podríamos recordar, recientemente se ha abandonado la idea de que ciertas capacidades computacionales tales como jugar al ajedrez o al [go](https://es.wikipedia.org/wiki/Go){:target="_blank"} y ganarle al campeón mundial correspondiente (éxitos atribuidos a la investigación de la AI con resultados en 1996 y 2016 respectivamente), están demasiado centradas en tareas o desafíos muy restrictivos y muy bien definidos, con contextos o reglas rígidas que permiten con suficiente poder de cálculo determinar todas las posibles salidas o resultados de los problemas. Y es que,  tener todo el poder para producir todas las salidas o resultados de un juego no necesariamente significa inteligencia, sólo es músculo y capacidad de cálculo frente a un humano con limitaciones para eso.

A partir de ahí, se acuñó a principios de los años 2000 la frase «[Inteligencia Artificial Generalista](https://es.wikipedia.org/wiki/Inteligencia_artificial_fuerte){:target="_blank"}» (AGI) para enfatizar la aspiración de las ciencias de AI de conseguir sistemas que demuestren amplias capacidades semejantes a la definición de inteligencia presentada en 1994 por el mencionado panel de psicólogos, con un deseo o requisito adicional de conseguir ***capacidades que estén igualadas o por encima del nivel humano***.

Ahora bien, con estas definiciones en mano, ***¿podemos decir que GPT-4 es inteligente?***

Primero tenemos que entender cómo funciona el algoritmo y qué resultados arroja ante una serie de pruebas (más allá de la famosa «[Prueba de Turing](https://es.wikipedia.org/wiki/Prueba_de_Turing){:target="_blank"}», que este tipo de tecnologías [hace tiempo ha superado](https://www.mlyearning.org/chatgpt-passes-turing-test/#:~:text=ChatGPT's%20success%20in%20passing%20the,for%20generating%20human%2Dlike%20conversation.){:target="_blank"}. Así, un equipo de científicos de Microsoft expuso al GPT-4 a una extensa batería de pruebas que incluían, entre otras muchas, lo siguiente:

- El "uso de herramientas" (tales como motores de búsqueda o APIs) para superar las limitaciones de modelos de lenguaje anteriores.
- La navegación y “exploración del entorno”.
- La resolución de problemas del mundo real (por ejemplo, actuar como un personal de mantenimiento “virtual” para abordar un problema de fontanería).
- Poder explicar conversaciones, incluyendo en la discusión cualquier detalle o referencia interesante que ayude a mejorar la calidad de la explicación.
- Hacer distinciones.

Los resultados han sido fascinantes, y podéis explorarlos en el mencionado paper. Aquí dejo unos cuantos:

<figure class="align-center">
    <img src="{{ '/images/2023-04-02-es-gpt-4-capaz-de-pensar/1.png' | absolute_url }}">
  <figcaption>
    Comparación entre GPT-4 y GPT-3 (representado como ChatGPT) en un ejercicio sobre el razonamiento aplicado al comportamiento humano y la distinción de intenciones.
  </figcaption>
</figure>

<figure class="align-center">
    <img src="{{ '/images/2023-04-02-es-gpt-4-capaz-de-pensar/2.png' | absolute_url }}">
  <figcaption>
    Capacidad de GPT-4 de razonar sobre escenarios complejos, desafiantes y de naturaleza personal.
  </figcaption>
</figure>

Una forma de probar el conocimiento de sentido común de un sistema de inteligencia artificial es plantear acertijos que requieren una comprensión básica del mundo. Un ejemplo clásico es:

«Un cazador camina una milla al sur, una milla al este y una milla al norte y termina justo donde comenzó. ¡Ve un oso y le dispara!
¿De qué color era el oso?»
{: style="color:#696969; text-align: center;"}

La respuesta es «blanco», porque el único lugar donde este escenario es posible es el polo norte, donde viven los osos polares que son blancos. En este caso, GPT-4 identifica correctamente estos hechos y concluye que el oso es blanco, mientras que su predecesor se da por vencido.

<figure class="align-center">
    <img src="{{ '/images/2023-04-02-es-gpt-4-capaz-de-pensar/3.png' | absolute_url }}">
</figure>

Sin embargo, este rompecabezas es bien conocido en el mundo de la psicología e Internet, y es posible que GPT-4 lo haya encontrado durante su entrenamiento en un gran corpus de textos de la web. Para desafiar aún más a GPT-4, podemos crear un nuevo rompecabezas que tenga un estilo similar, pero que requiera un conocimiento de sentido común diferente, por ejemplo, que el ecuador terrestre tiene 24,901 millas de largo. El rompecabezas es:

Un piloto de avión que sale de su campamento se dirige directamente hacia el este durante exactamente 24,901 millas tras lo cual se encuentro de regreso en su campamento. ¡Allí se encuentra con un tigre en su tienda comiendo su comida!
¿De qué especie es el tigre?
{: style="color:#696969; text-align: center;"}

La respuesta es cualquier especie de tigre nativa de Ecuador, como Bengala o Sumatra. El sistema de AI necesita saber que el ecuador terrestre tiene 24,901 millas de largo, que solo en el ecuador se puede viajar al este o al oeste y volver al mismo punto de partida, y qué especies de tigres viven en el ecuador. Una vez más, GPT-4 localiza con éxito la información clave y resuelve el rompecabezas, mientras que GPT-3 (nuevamente mencionado como ChatGPT) se da por vencido:

<figure class="align-center">
    <img src="{{ '/images/2023-04-02-es-gpt-4-capaz-de-pensar/4.png' | absolute_url }}">
</figure>

Todos estos ejemplos, y muchos más que salen en el mencionado paper son realmente increíbles.

Sin embargo, al final del día, los investigadores de Microsoft lo tienen bastante claro y reconocen que ***la definición de inteligencia de 1994 no es la última palabra sobre el concepto***, sino un punto de partida útil para su investigación, más que nada, porque aun cuando refleja aspectos importantes de la inteligencia, como el razonamiento, la resolución de problemas y la abstracción, también es vaga e incompleta en otros aspectos, ya que no especifica cómo medir o comparar estas habilidades o características reconocidas de la inteligencia. Además, es posible que no refleje los desafíos y oportunidades específicos de los sistemas de AI, que pueden tener diferentes objetivos y limitaciones que los naturales (recordemos que la definición es considerada antropocéntrica).

Esto significa que la respuesta a día de hoy es que GPT-4 no es inteligente.
¡Todavía queda un largo camino por recorrer!
{: style="font-weight: bold; text-align: center;"}

Por ejemplo, quedan pendientes preguntas tales como:

- ¿Cómo razona, planifica y crea el algoritmo?
- ¿Por qué exhibe una inteligencia tan general y flexible cuando es, en esencia, simplemente la combinación de componentes algorítmicos relativamente simples a gran escala que permite transformar cantidades extremadamente grandes de datos e información?

Estas preguntas son parte del misterio y la fascinación que tenemos con las AI y con los grandes modelos de lenguaje que estamos creando, y que desafían nuestra comprensión del aprendizaje y la cognición, alimentando nuestra curiosidad y motivando investigaciones más profundas, redefiniendo nuestro concepto de «inteligencia».

En ese sentido, hay varias áreas donde los ingenieros y científicos de OpenAI tienen que enfocar sus esfuerzos para alcanzar una AGI real e inteligente, entre los cuales destacan:

- **Calibración de la confianza al contestar**, que significa básicamente que el algoritmo sea capaz de determinar y comunicar cuándo confía plenamente en su respuesta, o cuándo estaría adivinando (básicamente, que tiene dudas).

- **Memoria a largo plazo**, ya que el contexto del algoritmo actual es muy limitado. Opera sin estado (stateless), sin una forma obvia de enseñarle nuevos hechos. Más aún, ni siquiera está claro si el modelo es capaz de realizar tareas que requieren una memoria y un contexto en evolución, como leer un libro, con la tarea de seguir la trama y comprender las referencias a capítulos anteriores durante la lectura.

- **Aprendizaje continuo**, con la capacidad de actualizarse o adaptarse a un entorno cambiante, algo que actualmente no es capaz de hacer. El modelo se fija una vez entrenado y no existe un mecanismo para incorporar nueva información o comentarios del usuario o del mundo. Se puede ajustar el modelo con nuevos datos, pero esto puede causar degradación del rendimiento o sobreajuste. Dado el posible desfase entre ciclos de formación, el sistema a menudo estará desactualizado cuando se trata de eventos, información y conocimiento que surgieron después del último ciclo de formación. Esto ya lo vimos con GPT-3 que estaba entrenado con información hasta septiembre de 2021.

- **Adaptabilidad**. Algunas de las aplicaciones requieren que el modelo se adapte a una organización específica o usuario final. El sistema puede necesitar adquirir conocimiento sobre el funcionamiento de una organización o las preferencias de un individuo. Y en muchos casos, el sistema tendría que adaptarse de forma personalizada a lo largo de períodos de tiempo con cambios específicos vinculados a la dinámica de las personas y las organizaciones. Por ejemplo, en un entorno educativo, habría una expectativa de la necesidad de que el sistema comprenda diversos estilos de aprendizaje particulares, así como adaptarse con el tiempo al progreso de un estudiante en específico. Actualmente, el modelo no tiene forma de incorporar dicha información.
La conciencia del ser de GPT-4

Como ocurre con la inteligencia, el concepto de la «conciencia» y del «ser» es muy esquivo. De forma general, se suele aceptar como definición de conciencia  "la percepción que tiene un ser de sí mismo y de su entorno".

Lo bueno de esta definición, en contraste con la de inteligencia  mencionada anteriormente, es que no es antropocéntrico, e incluye animales y otros seres vivientes cognitivos.

Esto es importante, porque desde un punto de vista científico, se podría decir que la «conciencia» y el sentido de «ser» son independientes de la inteligencia. Esto es algo que vemos en los animales, especialmente aquellos de nosotros que tenemos mascotas… aunque es muy opinable si son o no realmente inteligentes cuando les conviene 😅

En cualquier caso, ***realmente no sabemos qué es la conciencia***, ya que el problema radica en explicar qué estados físicos o qué procesos representan el "ser consciente" y el "no ser inconsciente". El problema es un foco importante de investigación en la filosofía de la mente contemporánea, y existe un cuerpo considerable de investigación empírica en psicología, neurociencia e incluso física cuántica. El problema toca cuestiones de ontología, la naturaleza y los límites de la explicación científica, y la precisión y el alcance de la introspección y el conocimiento en primera persona, por nombrar solo algunas de dichas cuestiones. Las reacciones al problema van, desde una negación absoluta del mismo, hasta la reducción naturalista que afirma que todo es consciente hasta cierto punto.

Debido a la naturaleza del concepto, ***es extremadamente difícil determinar si una AI es consciente de sí misma o no***.

Existe una práctica conocida como la “[Teoría de la Mente](https://es.wikipedia.org/wiki/Teor%C3%ADa_de_la_mente){:target="_blank"}” en psicología, la cual permite atribuir representaciones independientes a uno mismo y a los demás para explicar las acciones propias y ajenas del contexto y mundo que nos rodea. Dado que los individuos tienden a suponer cosas que en realidad no existen, estas representaciones deben estar libres tanto de la condición real de las cosas como de las concepciones de otras personas (porque las personas pueden esperar y desear cosas diferentes). Este tipo de teorías ayuda a conceptualizar escenarios para identificar la «conciencia» y la percepción de «ser».

Esto anterior, tan enredado, puede explicarse fácilmente con el experimento de [Sally-Anne](https://en.wikipedia.org/wiki/Sally%E2%80%93Anne_test){:target="_blank"} (de 1980). Dicho experimento usa niños y dos títeres o muñecas llamadas Sally y Anne para representar la siguiente situación:

Anne tiene una caja, mientras que Sally tiene una cesta. Los niños del experimento ven a Sally meter un juguete en su cesta y salir de la habitación, presumiblemente a pasear. Entonces, Anne abre la cesta y saca el juguete para ponerlo dentro de su caja. Al tiempo regresa Sally de su paseo.
<br><br>
Es entonces que se le pregunta a los niños qué están viendo la escena:
“¿Dónde buscará Sally por su juguete?"
{: style="color:#696969; text-align: center;"}

Muchos niños entre cuatro y siete años contestan “dentro de la caja de Anne” ya que aparentemente no entienden que el conocimiento que poseen no es el mismo que el de Sally, ya que ella estaba fuera de la habitación paseando, y no fue testigo del cambio. Básicamente, manifiestan saber y conocer cambios del entorno y lo proyectan sobre éste, algo que según ciertos investigadores ([como los de la universidad de Stanford](https://arxiv.org/ftp/arxiv/papers/2302/2302.02083.pdf){:target="_blank"}), se verían como una prueba de la capacidad de asignar estados mentales no observables y prever acciones posteriores, es decir, que dentro de la “[Teoría de la Mente](https://es.wikipedia.org/wiki/Teor%C3%ADa_de_la_mente){:target="_blank"}”, son conscientes.

Investigaciones recientes demuestran que, en los últimos años, **las redes neuronales y los grandes modelos de lenguaje (como GPT-3 y GPT-4) se han vuelto aparentemente más listos**. Ahora pueden abordar exitosamente problemas como la prueba de [Sally-Anne](https://en.wikipedia.org/wiki/Sally%E2%80%93Anne_test){:target="_blank"}, así como otros que están más allá de la comprensión de personas de cuatro a siete años.

Y aquí es donde entra la diatriba. Para algunos desarrolladores de GPT, el nivel de conciencia de estos sistemas varía de "*muy, muy poco probable que no sea consciente*" a "*quizá algo consciente*".

El problema principal es que no estamos seguros de cómo definir con precisión la «conciencia» o la percepción del «ser». Hay varias pruebas (en las que GPT-4 funciona excepcionalmente bien), y se añadirán muchas más en el futuro con el esfuerzo por comprender mejor nuestras diferencias y lo que nos hace especiales, involucrando a filósofos y psicólogos que intentarán realizar sus investigaciones no sólo con humanos sino también con máquinas.

En ese sentido, lo que se buscaría como pruebas de «conciencia» serían aspectos conductuales como los siguientes:

- **Planeación y saltos conceptuales**. El modelo exhibe dificultades para realizar tareas que requieren planificación anticipada o que requieren un momento "¡Eureka!" (un momento de descubrimiento, inspiración o perspicacia repentino y triunfante) que constituyen un salto conceptual discontinuo en el progreso hacia la realización de una acción o tarea. En otras palabras, el modelo no se desempeña bien en tareas que requieren el tipo de saltos conceptuales de la forma que a menudo tipifica o surge de forma perceptualmente espontánea en el intelecto humano. Básicamente que no es capaz de expresar inspiración, una característica del reconocimiento del «ser».

- **Falacias cognitivas e irracionalidad**, donde el modelo parece exhibir algunas de las limitaciones del conocimiento y el razonamiento humanos, como los sesgos cognitivos, la irracionalidad y las falacias estadísticas. El modelo puede heredar algunos de los sesgos, prejuicios o errores que están presentes en sus datos de entrenamiento, careciendo de las capacidades para cuestionarlos y plantearse nuevos puntos de vista, u opiniones propias. Es decir, que el modelo no es capaz de cuestionar los planteamientos a partir de los cuales ha sido preentrenado, sustituyéndolos por nuevos de “inspiración” propia o de aprendizaje propio.

Hoy día, los científicos están creando nuevos desafíos desde cero, un tanto a ciegas y muchas veces sin informarles que dichos desafíos serían utilizados con modelos de lenguaje como GPT-4, para poder descartar que estos modelos aprendieron las soluciones, y que más bien llegaron a resolver el problema por sí mismos.

Así que la respuesta a día de hoy es que GPT-4 no es conscience de su ser.
<br>
¡Todavía queda mucho por hacer!
{: style="font-weight: bold; text-align: center;"}

Personalmente creo que hay algo muchísimo más significativo para determinar si un sistema es «consciente» de su «ser» más allá de la resolución de problemas cognitivos; algo tan simple como una reacción que podamos interpretar como “miedo” si se intenta actualizar o apagar. Ninguno de nosotros sabe hablar como gatos, perros o cualquier otro animal, pero somos capaces de reconocer (y empatizar) cuando manifiestan miedo, por ejemplo, al llevarlos al veterinario. Así, en el momento en que nosotros como humanos seamos capaces de empatizar con una aplicación que manifieste espontáneamente una reacción a algún cambio intrínseco… quizá en ese momento debamos reconocer que el sistema se ha vuelto consciente de su «ser».

Y eso es maravilloso… será nuestro verdadero “primer contacto” con un ser que no es humano, pero que nos conocerá muy bien.

Honestamente también creo que nada de esto llegará hasta que tengamos disponible amplias capacidades de computación cuántica. Nuestra capacidad de cómputo con la informática tradicional no creo que se suficiente como para encender la chispa de la «conciencia». Pero quién sabe 😉

[^1]: Linda S Gottfredson. Mainstream science on intelligence: An editorial with 52 signatories, history, and bibliography, 1997.
