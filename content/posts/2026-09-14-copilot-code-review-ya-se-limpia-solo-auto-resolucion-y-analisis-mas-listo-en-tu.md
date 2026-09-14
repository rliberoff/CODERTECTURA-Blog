---
title: 'Copilot Code Review ya se limpia solo: auto-resolución y análisis más listo
  en tus PR'
date: '2026-09-14T12:05:55+00:00'
draft: true
slug: copilot-code-review-ya-se-limpia-solo-auto-resolucion-y-analisis-mas-listo-en-tu
description: GitHub mejora Copilot Code Review con auto-resolución de comentarios
  y análisis más fino. Te enseño cómo probarlo en un repo real y qué cambia de verdad
  en tu flujo de PR.
categories:
- Inteligencia Artificial
- Arquitectura de Software
- .NET
tags:
- GitHub Copilot
- Code Review
- Pull Requests
- Automatización
- GitHub
image: /images/copilot-code-review-ya-se-limpia-solo-auto-resolucion-y-analisis-mas-listo-en-tu/cover.png
comments: true
ai:
  assisted: true
  article_type: technical
  model: gpt-5.4
  prompt_version: 2026-08-21.1
  generated_at: '2026-09-14T12:05:55+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://github.blog/changelog/2026-09-11-auto-resolution-and-analysis-updates-in-copilot-code-review
    title: Auto-resolution and analysis updates in Copilot code review
    published_date: '2026-09-11'
  - url: https://github.blog/changelog/2025-09-18-copilot-code-review-now-in-jetbrains-ides-and-visual-studio
    title: 'Copilot code review: Now in JetBrains IDEs and Visual Studio - GitHub
      Changelog'
    published_date: null
  - url: https://github.blog/changelog/2026-08-28-upcoming-changes-to-github-copilot-policies-and-billing
    title: Upcoming changes to GitHub Copilot policies and billing
    published_date: null
---

Si trabajas a diario con *pull requests*, esta mejora de GitHub Copilot toca una fricción muy concreta y muy real: esos comentarios automáticos que al principio ayudan, pero que después se quedan flotando en la conversación aunque ya hayas corregido el problema. Según el anuncio de [auto-resolution and analysis updates in Copilot code review](https://github.blog/changelog/2026-09-11-auto-resolution-and-analysis-updates-in-copilot-code-review), Copilot ahora puede resolver sus propios comentarios cuando detecta que ya los has abordado y además genera mensajes de *commit* más inteligentes cuando aplicas sus sugerencias. Y a mí esto no me parece un retoque cosmético. Me parece un ajuste pequeño con bastante impacto en el día a día.

Porque el problema nunca ha sido sólo que un bot comente. El problema aparece cuando comenta, tú actúas y el PR sigue pareciendo un tablón de notas viejas. Ahí es donde una automatización deja de ayudar y empieza a estorbar. **Si la IA quiere quedarse en el flujo de revisión, tiene que saber cerrar el bucle**, no sólo abrirlo.

Además, esto encaja bastante bien con el recorrido que GitHub ya había iniciado cuando [llevó Copilot code review a Visual Studio y JetBrains](https://github.blog/changelog/2025-09-18-copilot-code-review-now-in-jetbrains-ides-and-visual-studio). Es decir: no hablamos sólo del comentario en GitHub, sino de una experiencia que intenta aparecer antes, durante y después del PR. Yo aquí me voy a quedar en GitHub y con un ejemplo muy pequeño en .NET, porque es la forma más limpia de ver el antes y el después sin montar una demo de escaparate.

### Qué cambia de verdad en el flujo de revisión

Hasta ahora, una de las debilidades habituales de muchas automatizaciones de *code review* era bastante simple: detectaban mejor de lo que remataban. Te señalaban un riesgo, tú lo corregías y aun así quedaba trabajo manual. Había que revisar si el comentario seguía aplicando, resolver la conversación a mano o dejar una respuesta explicando que ya estaba arreglado. No era dramático, pero sí era otra pequeña tarea mecánica más.

El cambio anunciado por GitHub va justo contra esa molestia. Si Copilot abre una conversación en tu PR y más tarde detecta que el nuevo *commit* ya aborda esa observación, la conversación puede resolverse automáticamente. Y si aplicas una sugerencia suya, el mensaje de *commit* deja de quedarse en algo genérico del estilo «Apply suggestion» para ser más descriptivo.

{{< figure src="/images/copilot-code-review-ya-se-limpia-solo-auto-resolucion-y-analisis-mas-listo-en-tu/body-1.png" alt="Diagrama del flujo de revisión con auto-resolución de Copilot" caption="Así encaja la auto-resolución en el ciclo normal de una pull request: comentario, corrección, nuevo push y cierre automático de la conversación." >}}{{< /figure >}}

Yo aquí haría una precisión importante: esto **no sustituye el criterio de nadie**. No convierte a Copilot en aprobador del PR, ni en arquitecto, ni en revisor de negocio. Lo que hace es otra cosa, bastante más humilde y bastante más útil: quitar residuos del proceso. Y sinceramente, en revisiones con mucha actividad, esa limpieza vale más de lo que parece.

### Antes de empezar

Para reproducirlo de punta a punta, yo usaría un entorno mínimo como este:

- Una cuenta de GitHub con acceso a GitHub Copilot y a Copilot Code Review.
- Permisos para crear ramas y abrir *pull requests* en un repositorio propio o de pruebas.
- Git instalado.
- [.NET 8 SDK](https://dotnet.microsoft.com/) para crear y validar el proyecto de ejemplo.
- GitHub CLI `gh` para abrir la PR desde terminal de forma reproducible.
- Un editor como Visual Studio o VS Code si quieres comparar el flujo local con el de GitHub, especialmente ahora que [Copilot code review también está disponible en Visual Studio y JetBrains](https://github.blog/changelog/2025-09-18-copilot-code-review-now-in-jetbrains-ides-and-visual-studio).

Mi recomendación: usa un repositorio de laboratorio. Vas a provocar a propósito un cambio mejorable para que Copilot tenga algo razonable que comentar, así que mejor hacerlo donde no molestes a nadie (incluido tu yo del futuro).

### Preparar un repositorio mínimo en .NET 8 para provocar una observación útil

La idea no es engañar a Copilot con un caso absurdo, sino darle un cambio bastante normal: código que compila, parece correcto a primera vista, pero tiene una validación demasiado débil. Voy a crear una librería pequeña con un método que divide sin validar el divisor. Es un caso muy simple, sí, pero precisamente por eso sirve bien para comprobar si la revisión automatizada detecta algo útil.

```bash
mkdir copilot-review-lab
cd copilot-review-lab
dotnet new sln --name CopilotReviewLab
dotnet new classlib --framework net8.0 --name Pricing.Core
dotnet sln add Pricing.Core/Pricing.Core.csproj
git init
git checkout -b main
```

Ahora crea `Pricing.Core/PriceCalculator.cs` con este contenido:

```csharp
namespace Pricing.Core;

public static class PriceCalculator
{
    public static decimal CalculateUnitPrice(decimal totalPrice, int quantity)
    {
        return totalPrice / quantity; // Dejo el caso frágil a propósito para que la review tenga algo concreto que señalar
    }
}
```

Y elimina el archivo que crea la plantilla para que el proyecto quede limpio:

```bash
rm Pricing.Core/Class1.cs
dotnet build
```

Si todo va bien, deberías obtener un `Build succeeded` sin advertencias ni errores. Después haz el primer *commit* y publícalo en tu repositorio remoto:

```bash
git add .
git commit -m "Create initial pricing library"
git remote add origin git@github.com:arquitectura-practica/copilot-review-lab.git
git push -u origin main
```

No hace falta complicarlo más. Lo importante aquí es tener una base mínima, compilable y lo bastante creíble como para que el comentario posterior de Copilot no parezca forzado.

### Abrir una PR con un cambio mejorable para que Copilot revise

Ahora creo una rama de trabajo con una mejora aparentemente razonable: añadir redondeo al cálculo del precio unitario. El detalle interesante es que sigo sin validar `quantity`, así que el método mejora por un lado pero continúa siendo frágil por otro. Ese tipo de cambio da bastante contexto al análisis del diff.

```bash
git checkout -b feature/unit-price-rounding
cat > Pricing.Core/PriceCalculator.cs <<'EOF'
namespace Pricing.Core;

public static class PriceCalculator
{
    public static decimal CalculateUnitPrice(decimal totalPrice, int quantity)
    {
        return decimal.Round(totalPrice / quantity, 2, MidpointRounding.AwayFromZero);
    }
}
EOF

dotnet build
git add Pricing.Core/PriceCalculator.cs
git commit -m "Add rounded unit price calculation"
git push -u origin feature/unit-price-rounding
```

Con eso ya puedes abrir la PR desde terminal:

```bash
gh pr create \
  --base main \
  --head feature/unit-price-rounding \
  --title "Add rounded unit price calculation" \
  --body "Esta PR añade redondeo al cálculo de precio unitario para probar Copilot Code Review en un caso real y pequeño."
```

A partir de aquí, toca esperar a que Copilot analice la PR. Según [la actualización oficial de GitHub](https://github.blog/changelog/2026-09-11-auto-resolution-and-analysis-updates-in-copilot-code-review), también hay mejoras internas en el análisis, así que yo no me fijaría sólo en si aparece un comentario, sino en si ese comentario es accionable y suficientemente específico sobre el diff.

{{< figure src="/images/copilot-code-review-ya-se-limpia-solo-auto-resolucion-y-analisis-mas-listo-en-tu/source-2.jpg" alt="Captura de la interfaz de Copilot Code Review con estado de conversación" caption="La interfaz de Copilot Code Review ya muestra estados y acciones de resolución dentro de la conversación del PR. Fuente: [github.blog](https://github.blog/changelog/2025-09-18-copilot-code-review-now-in-jetbrains-ides-and-visual-studio)" >}}{{< /figure >}}

Lo esperable es que Copilot señale que `quantity` no se valida y que eso puede provocar una división por cero o aceptar valores no válidos. El texto exacto puede variar, claro, pero el sentido debería ser ese. Y aquí está una de las claves: no necesito que redacte un ensayo brillante; necesito que encuentre algo útil, concreto y corregible.

### Corregir el problema y comprobar la auto-resolución

Aquí está la parte interesante de verdad. Voy a aplicar una corrección pequeña, explícita y fácil de verificar. Cuanto más clara sea la intención del cambio, más sencillo será comprobar si la conversación se resuelve sola después del *push*.

```csharp
using System;

namespace Pricing.Core;

public static class PriceCalculator
{
    public static decimal CalculateUnitPrice(decimal totalPrice, int quantity)
    {
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(quantity); // Expresa exactamente la precondición y evita una validación manual más verbosa

        return decimal.Round(totalPrice / quantity, 2, MidpointRounding.AwayFromZero);
    }
}
```

Valida y publica el cambio:

```bash
dotnet build
git add Pricing.Core/PriceCalculator.cs
git commit -m "Validate quantity before division"
git push
```

En la PR deberías ver una de estas dos cosas: o bien la conversación de Copilot pasa automáticamente a resuelta, o bien queda marcada como abordada por el propio sistema. Ese es justamente el comportamiento que describe [la mejora de auto-resolución en Copilot code review](https://github.blog/changelog/2026-09-11-auto-resolution-and-analysis-updates-in-copilot-code-review).

{{< figure src="/images/copilot-code-review-ya-se-limpia-solo-auto-resolucion-y-analisis-mas-listo-en-tu/source-3.jpg" alt="Captura de una conversación marcada como Addressed en Copilot Code Review" caption="Cuando la corrección ya está en la rama, Copilot puede marcar la conversación como abordada y resolverla automáticamente. Fuente: [github.blog](https://github.blog/changelog/2026-08-28-upcoming-changes-to-github-copilot-policies-and-billing)" >}}{{< /figure >}}

Para mí, aquí está el valor real. En un repositorio con bastante movimiento, esta pequeña automatización evita que el PR termine convertido en una excavación arqueológica de comentarios que ya no aplican. **La limpieza del contexto también es productividad**. No suena épico, pero funciona.

### Aplicar una sugerencia de Copilot y observar el mensaje de commit

La otra mejora que menciona GitHub es que Copilot escribe mensajes de *commit* más inteligentes cuando aplicas sus sugerencias de código. Y esto, otra vez, parece menor hasta que llevas unos cuantos meses revisando historiales llenos de mensajes genéricos que no cuentan nada.

No siempre vas a obtener exactamente el mismo resultado, porque depende del cliente, del diff y de cómo se aplique la sugerencia. Pero la idea que describe [el anuncio oficial](https://github.blog/changelog/2026-09-11-auto-resolution-and-analysis-updates-in-copilot-code-review) es clara: si aceptas una sugerencia de Copilot, el mensaje generado debería reflejar mejor qué cambio acabas de incorporar.

Un historial razonable podría terminar viéndose así:

```text
git log --oneline -3
9f31e3a Validate quantity before division
53bb2c1 Round unit price to two decimals
f84a1d7 Create initial pricing library
```

Lo importante no es la cadena exacta, sino la intención. Si el historial explica mejor qué ha pasado en cada paso, revisar y entender la PR después también cuesta menos. Y sí, esto parece una tontería... hasta que te toca revisar un cambio antiguo con prisas.

### Comparar el antes y el después del análisis en un repo de trabajo

Aquí conviene separar un poco el entusiasmo del marketing. GitHub habla de análisis actualizado *behind the scenes*, pero eso no implica que Copilot vaya a descubrir de repente una nueva categoría de errores en todos tus repositorios. Yo sería bastante más prudente con esa expectativa.

Lo que sí esperaría, y lo que me parece más valioso en la práctica, es una combinación de tres cosas: comentarios más centrados en el diff real, menos conversaciones obsoletas una vez corriges el problema y una trazabilidad mejor cuando aceptas sugerencias y se generan *commits*.

{{< figure src="/images/copilot-code-review-ya-se-limpia-solo-auto-resolucion-y-analisis-mas-listo-en-tu/body-4.png" alt="Comparativa visual entre PR con comentarios pendientes y PR limpia tras auto-resolución" caption="La diferencia práctica no es sólo técnica: un PR con menos conversaciones obsoletas se revisa mejor y más rápido." >}}{{< /figure >}}

Si quieres medirlo con un poco de disciplina, yo haría una prueba muy simple en un repositorio real:

1. Abre una PR pequeña pero no trivial;
2. Anota cuántos comentarios de Copilot aparecen;
3. Corrige dos o tres observaciones legítimas;
4. Comprueba cuántas quedan auto-resueltas tras el siguiente *push*;
5. Revisa si el historial de *commits* cuenta mejor lo que ha cambiado.

No es una métrica científica (ni pretende serlo), pero sí una comprobación útil de trabajo cotidiano. Yo no evaluaría esta mejora por cuánta «magia» de IA promete, sino por **cuántos clics irrelevantes y cuánta limpieza manual te ahorra en una semana normal**.

### Dónde encaja esto en un flujo sano de PR

Mi recomendación aquí es muy pragmática: usa Copilot Code Review como primera capa de fricción barata. Que te señale cosas obvias, que te ayude a autocorregirte y que mantenga el PR algo más limpio. Después deja a las personas lo que de verdad importa: intención de diseño, contratos, impacto arquitectónico, nomenclatura, deuda técnica tolerable y riesgos de negocio.

Si además trabajas desde IDE, tiene bastante sentido aprovechar que [Copilot code review ya está integrado en Visual Studio y JetBrains](https://github.blog/changelog/2025-09-18-copilot-code-review-now-in-jetbrains-ides-and-visual-studio). Cuanto antes aparezca un comentario útil, menos retrabajo arrastras hasta la PR. Y eso, en mi experiencia, reduce tanto tiempo como fricción mental.

También me parece sensato no perder de vista el contexto operativo. GitHub sigue tocando [políticas y facturación de Copilot](https://github.blog/changelog/2026-08-28-upcoming-changes-to-github-copilot-policies-and-billing), así que si estás valorando una adopción más amplia en equipo o empresa, yo no separaría la mejora técnica del modelo de uso, permisos y coste. Una experiencia mejor sigue formando parte de una plataforma que hay que gobernar.

### Mi conclusión

Esta novedad me gusta porque ataca una molestia pequeña, frecuente y bastante poco glamurosa. No intenta venderte que la IA revisa por ti. Intenta algo más sensato: que la revisión automática se comporte de una forma más madura dentro del flujo real de desarrollo.

Si Copilot comenta y luego sabe reconocer que ya lo has arreglado, el PR se parece más a una conversación útil y menos a un buzón de avisos acumulados. En resumen: **menos ruido, mejor cierre del feedback y *commits* más comprensibles cuando aceptas sugerencias**.

Si ya usas GitHub Copilot en revisión, yo probaría esta mejora hoy mismo en un repositorio de laboratorio como el de este artículo. Y si todavía no lo usas, este tipo de detalle es precisamente lo que a mí me hace tomármelo en serio para flujos reales, no sólo para demos bonitas.
