---
title: GitHub Copilot en Visual Studio acelera su madurez con nuevas funciones agentic
date: '2026-06-29T11:02:02+00:00'
draft: true
slug: github-copilot-visual-studio-funciones-agentic
description: Copilot gana peso en Visual Studio con una experiencia más agentic y
  orientada a productividad real. Veamos qué cambia y cómo aprovecharlo.
categories:
- .NET
- Inteligencia Artificial
- Herramientas de Desarrollo
tags:
- GitHub Copilot
- Visual Studio
- IA generativa
- Productividad
- .NET
- Desarrollo asistido
image: /images/github-copilot-visual-studio-funciones-agentic/cover.png
comments: true
ai:
  assisted: true
  model: gpt-5.4-mini
  prompt_version: 2026-06-26.1
  generated_at: '2026-06-29T11:02:02+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://github.blog/changelog/2026-06-04-github-copilot-in-visual-studio-may-update
    title: GitHub Copilot in Visual Studio — May update
    published_date: '2026-06-04'
  - url: https://developer.microsoft.com/blog/build-recap
    title: 'Microsoft Build 2026 recap: vision, launches, and top sessions'
    published_date: '2026-06-02'
  - url: https://blogs.microsoft.com/blog/2026/06/02/microsoft-build-2026-be-yourself-at-work
    title: 'Microsoft Build 2026: Be yourself at work'
    published_date: '2026-06-02'
---

GitHub Copilot en Visual Studio ya no se percibe solo como un asistente que completa líneas de código. La evolución reciente apunta a otra cosa: una experiencia más agentic, más integrada en el flujo de trabajo real y, sobre todo, más útil cuando estamos resolviendo tareas completas y no simples fragmentos. En otras palabras, Microsoft y GitHub están empujando Copilot hacia un rol más cercano al de un compañero de equipo que entiende contexto, ejecuta acciones y reduce fricción.

Ese cambio no es trivial. Durante años hemos pedido a las herramientas de IA que nos ayuden a escribir más rápido, pero en el día a día el cuello de botella rara vez está en teclear. El problema suele estar en navegar un proyecto grande, localizar el punto correcto, entender dependencias, probar una hipótesis y volver atrás si algo no encaja. Ahí es donde una experiencia más agentic empieza a tener sentido: menos “sugiere una línea” y más “ayúdanos a completar una intención”.

Las notas recientes sobre GitHub Copilot en Visual Studio refuerzan precisamente esa dirección. El [changelog de GitHub](https://github.blog/changelog/2026-06-04-github-copilot-in-visual-studio-may-update) sitúa las novedades en torno a una experiencia más capaz dentro del IDE. Y, al mismo tiempo, el contexto de Microsoft Build 2026 deja claro que la compañía sigue apostando por flujos de trabajo basados en agentes y en productividad práctica, no en demostraciones aisladas ([recap de Build](https://developer.microsoft.com/blog/build-recap) y [blog oficial de Microsoft](https://blogs.microsoft.com/blog/2026/06/02/microsoft-build-2026-be-yourself-at-work)).

### Qué significa realmente una experiencia más agentic

Cuando hablamos de IA agentic en desarrollo no nos referimos a “que el modelo sea más listo”, sino a que pueda participar en una secuencia de trabajo más completa. Es decir:

- Entender mejor la intención del cambio.
- Proponer modificaciones repartidas por varios archivos.
- Reducir el cambio manual de contexto.
- Ayudarnos a validar el resultado con más rapidez.

En Visual Studio esto importa especialmente porque el IDE sigue siendo el entorno principal para muchísimos equipos .NET. Si Copilot vive solo en el editor, aporta; si además conversa con el proyecto, el árbol de archivos y el flujo de depuración, deja de ser un accesorio y se convierte en una capa de productividad transversal.

### La clave no es escribir más, sino decidir mejor

Aquí está el matiz importante: la IA no sustituye el criterio técnico. Lo que sí puede hacer es acelerar la parte mecánica de evaluar alternativas, preparar cambios repetitivos y ofrecer un primer borrador razonable. Nosotros seguimos decidiendo arquitectura, consistencia, seguridad y mantenibilidad.

En proyectos .NET esto se nota mucho. Pongamos un ejemplo simple: una API ASP.NET Core con validación, logging y manejo de errores. Un asistente de código puede generar la estructura inicial, pero el valor real aparece cuando puede ayudarnos a extender el patrón en varios puntos del proyecto sin que tengamos que repetir el mismo trabajo una y otra vez.

### Un ejemplo práctico en ASP.NET Core

Imaginemos una API minimalista que expone clientes. Visual Studio con Copilot puede ayudarnos a crear un endpoint, validar entrada y aplicar una política de errores coherente. El resultado no tiene por qué ser magia; basta con que nos ahorre pasos repetitivos.

```csharp
using Microsoft.AspNetCore.Mvc;

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

app.MapGet("/customers/{id:int}", ([FromRoute] int id) =>
{
    if (id <= 0)
    {
        return Results.BadRequest(new { error = "El identificador debe ser mayor que cero." });
    }

    var customer = new CustomerDto(id, $"Cliente {id}", $"cliente{id}@example.com");
    return Results.Ok(customer);
});

app.Run();

public record CustomerDto(int Id, string Name, string Email);
```

Ese tipo de código lo podemos escribir nosotros en pocos minutos. Entonces, ¿qué aporta Copilot? Sobre todo, velocidad para iterar. Si más tarde necesitamos:

- añadir un `POST` con validación,
- introducir un repositorio,
- mover la lógica a una capa de aplicación,
- o adaptar el modelo a pruebas unitarias,

un flujo más agentic reduce el coste de hacer esos cambios de forma coherente en varios archivos.

### Donde de verdad se nota: refactorización y navegación

El gran salto de valor no suele estar en el snippet inicial, sino en el refactor. Visual Studio es fuerte cuando el proyecto crece, y ahí Copilot puede ayudar de varias maneras:

- resumiendo intención a partir del código existente,
- sugiriendo cambios en clases relacionadas,
- generando tests de apoyo,
- y manteniendo el hilo de una tarea mientras pasamos de archivo en archivo.

Eso es especialmente interesante en soluciones con varios proyectos: API, aplicación, dominio, infraestructura y pruebas. En una arquitectura limpia, cada cambio implica tocar más de un sitio. Si la herramienta entiende mejor la relación entre piezas, dejamos de gastar tiempo en mecánica y lo dedicamos a revisar si el diseño sigue siendo correcto.

### Un ejemplo de dominio con test

Veamos un caso más realista. Supongamos una regla de negocio sencilla para calcular descuentos. Copilot puede ayudar a crear la implementación y el test correspondiente, pero nosotros seguimos marcando el contrato.

```csharp
using Xunit;

public class DiscountCalculator
{
    public decimal ApplyDiscount(decimal amount, decimal discountPercentage)
    {
        if (amount < 0)
            throw new ArgumentOutOfRangeException(nameof(amount));

        if (discountPercentage < 0 || discountPercentage > 100)
            throw new ArgumentOutOfRangeException(nameof(discountPercentage));

        return amount - (amount * discountPercentage / 100m);
    }
}

public class DiscountCalculatorTests
{
    [Fact]
    public void ApplyDiscount_WhenDiscountIsTenPercent_ReturnsExpectedAmount()
    {
        var calculator = new DiscountCalculator();

        var result = calculator.ApplyDiscount(100m, 10m);

        Assert.Equal(90m, result);
    }
}
```

En una sesión de trabajo real, la utilidad de Copilot está en acelerar variaciones como esta: crear más pruebas, cubrir casos límite o extraer reglas adicionales sin perder el hilo de la intención original.

### Lo importante para equipos .NET

Si trabajáis con Visual Studio a diario, hay varias conclusiones prácticas que ya podemos extraer de este movimiento:

- **Copilot tiene más sentido cuanto mayor es el contexto del proyecto.** En soluciones pequeñas ayuda; en soluciones grandes puede marcar diferencias reales.
- **La supervisión humana sigue siendo obligatoria.** El asistente acelera, pero no valida arquitectura ni dominio.
- **Las tareas repetitivas son su terreno natural.** Crear esqueletos, expandir pruebas, adaptar nombres y generar variantes es donde más retorno vemos.
- **La calidad depende del contexto que le damos.** Cuanto mejor estructurado está el código, mejores suelen ser las propuestas.

### Microsoft está empujando hacia flujos de trabajo más conectados

La lectura de fondo es clara: GitHub Copilot en Visual Studio forma parte de una estrategia más amplia. La narrativa de Microsoft alrededor de Build 2026 insiste en que la IA debe integrarse en el trabajo real y en herramientas que ya usamos, no en entornos separados. Eso encaja con una idea muy concreta: no queremos un copiloto que viva al margen del IDE, sino uno que participe en la productividad cotidiana ([Microsoft Build 2026 recap](https://developer.microsoft.com/blog/build-recap), [blog oficial](https://blogs.microsoft.com/blog/2026/06/02/microsoft-build-2026-be-yourself-at-work)).

Y aquí Visual Studio es un escenario natural. Es donde muchos proyectos .NET nacen, crecen y se mantienen. Si la experiencia de Copilot mejora dentro del IDE, el beneficio no es abstracto: se traduce en menos interrupciones, menos cambio de contexto y más foco en lo que importa.

### Cómo aprovecharlo sin caer en dependencia

Nos interesa adoptar estas herramientas con una idea muy sana: usar IA para reforzar el criterio, no para sustituirlo. Algunas buenas prácticas serían:

- Pedir al asistente cambios concretos y delimitados.
- Revisar siempre el código generado con la misma exigencia que el propio.
- Mantener tests que protejan el comportamiento esperado.
- Evitar aceptar refactors grandes sin entender el impacto.

Si lo hacemos así, Copilot se convierte en un multiplicador de productividad. Si no, corre el riesgo de convertirse en una fábrica de deuda técnica más rápida.

### Una evolución que merece seguimiento

La sensación general es que GitHub Copilot en Visual Studio está ganando tracción porque su propuesta ya no se limita a “escribir más deprisa”. La conversación ha cambiado hacia una IA que participa más en el flujo, entiende mejor el contexto y ayuda a cerrar tareas completas con menos fricción. Ese es el tipo de avance que realmente merece la pena seguir de cerca.

Para quienes trabajamos con .NET, Azure y el ecosistema Microsoft, esto no es solo una novedad más. Es una pista bastante clara de hacia dónde se están moviendo las herramientas de desarrollo: más asistencia contextual, más automatización útil y menos tareas mecánicas entre nosotros y el código.

Y, sinceramente, esa es una evolución que sí se nota en el día a día 🙂
