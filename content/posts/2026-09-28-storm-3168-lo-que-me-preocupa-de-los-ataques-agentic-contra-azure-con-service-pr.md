---
title: 'Storm-3168: lo que de verdad me preocupa de los ataques agentic en Azure con
  service principals comprometidos'
date: '2026-09-28T13:00:11+00:00'
draft: true
slug: storm-3168-lo-que-me-preocupa-de-los-ataques-agentic-contra-azure-con-service-pr
description: Analizo Storm-3168 desde la óptica de arquitectura e identidad. Te enseño
  a auditar service principals, revisar actividad sospechosa y recortar exposición
  en Azure.
categories:
- Azure
- Arquitectura de Software
- Inteligencia Artificial
tags:
- Seguridad en Azure
- Microsoft Entra ID
- Service Principals
- Identidades de carga de trabajo
- Threat Intelligence
image: /images/storm-3168-lo-que-me-preocupa-de-los-ataques-agentic-contra-azure-con-service-pr/cover.png
comments: true
ai:
  assisted: true
  article_type: technical
  model: gpt-5.4
  prompt_version: 2026-08-21.1
  generated_at: '2026-09-28T13:00:11+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://www.microsoft.com/en-us/security/blog/2026/09/25/storm-3168-agentic-driven-cloud-attacks-using-compromised-service-principals
    title: 'Storm-3168: Agentic-driven cloud attacks using compromised service principals
      | Microsoft Security Blog'
    published_date: '2026-09-25'
  - url: https://www.microsoft.com/en-us/security/blog/2026/09/22/unmasking-eviltokens-getting-to-the-root-of-device-code-phishing
    title: 'Unmasking EvilTokens: Getting to the root of device code phishing | Microsoft
      Security Blog'
    published_date: '2026-09-22'
  - url: https://www.microsoft.com/en-us/security/blog/2026/09/17/from-guidance-to-action-security-fundamentals-that-materially-reduce-risk
    title: 'From guidance to action: Security fundamentals that materially reduce
      risk | Microsoft Security Blog'
    published_date: '2026-09-17'
---

Lo de Storm-3168 no me llama la atención solo por el titular de «ataque *agentic*». Lo que realmente me inquieta es algo bastante más prosaico: **el punto de apoyo sigue siendo una identidad no humana con demasiado poder y demasiada vida útil**. Si tú diseñas arquitectura en Azure, o si te toca pelearte con identidad y acceso, esta historia no va de ciencia ficción. Va de *service principals* olvidados, secretos expuestos y automatizaciones que nadie revisa hasta el día en que ya es tarde.

Según el análisis de [Microsoft sobre Storm-3168](https://www.microsoft.com/en-us/security/blog/2026/09/25/storm-3168-agentic-driven-cloud-attacks-using-compromised-service-principals), el actor abusó de *service principals* comprometidos para reconocimiento, recopilación de credenciales y operaciones destructivas a gran escala en Azure. Entre los recursos afectados aparecen Storage Accounts, SQL databases, Key Vaults, Function Apps, máquinas virtuales, App Services e incluso mecanismos de recuperación. Para mí, lo importante no es solo la destrucción en sí, sino la velocidad y el radio de acción que te concede una identidad de *workload* cuando ya tiene permisos otorgados y nadie está mirando.

### Por qué este caso cambia la conversación

Llevamos años repitiendo lo de mínimo privilegio. Y sí, sigue siendo correcto. Lo que cambia aquí es la cadencia. Como explica [Microsoft al hablar de fundamentos de seguridad que reducen materialmente el riesgo](https://www.microsoft.com/en-us/security/blog/2026/09/17/from-guidance-to-action-security-fundamentals-that-materially-reduce-risk), la IA acelera la exploración de rutas de ataque y la combinación de debilidades conocidas: permisos excesivos, secretos expuestos, flujos de autenticación mal protegidos y una visibilidad fragmentada. Dicho de forma más directa: el problema no es nuevo, pero **la velocidad con la que el atacante puede explotarlo sí lo es**.

Esa idea encaja además con [el caso EvilTokens](https://www.microsoft.com/en-us/security/blog/2026/09/22/unmasking-eviltokens-getting-to-the-root-of-device-code-phishing), donde Microsoft describe cómo la automatización asistida por IA industrializa campañas y acelera reconocimiento, abuso de tokens y persistencia. Storm-3168 lleva esa misma lógica al plano *cloud*. Menos «te comprometo una VM» y más «uso una identidad válida para operar tu plataforma como si fuera mía». Y eso, admitámoslo, da bastante menos margen de reacción.

{{< figure src="/images/storm-3168-lo-que-me-preocupa-de-los-ataques-agentic-contra-azure-con-service-pr/body-1.png" alt="Diagrama del flujo de ataque de Storm-3168 usando service principals comprometidos" caption="Una vista simplificada del patrón que más me preocupa: credencial expuesta, abuso del service principal, reconocimiento, acceso a secretos y destrucción de recursos." >}}{{< /figure >}}

### Mi lectura como arquitecto: el activo crítico ya no es solo la cuenta admin humana

Muchas organizaciones siguen tratando el *service principal* como una pieza técnica secundaria. Lo crea Terraform, lo necesita un *pipeline*, lo usa una integración, y a partir de ahí se queda viviendo en un rincón oscuro del tenant. En mi experiencia, ese enfoque ya no aguanta. Un *service principal* con permisos amplios, secretos de larga duración y sin un dueño claro se parece peligrosamente a una cuenta privilegiada sin fricción operativa.

Y lo peor es que suele vivir en una zona gris. No recibe el mismo nivel de escrutinio que una cuenta administrativa humana, no siempre entra en campañas de rotación y muchas veces tampoco participa en procesos de recertificación. Cuando un actor consigue esa identidad, no necesita «romper» Azure. **Solo necesita usar Azure exactamente como fue diseñado**, pero con objetivos hostiles.

Ese matiz me parece clave, porque cambia la forma de pensar la defensa. Ya no basta con endurecer la autenticación humana y asumir que lo demás es «infraestructura». Las identidades no humanas son parte de tu perímetro real. De hecho, en entornos muy automatizados, probablemente sean una parte más crítica que muchos usuarios interactivos.

### Antes de empezar

Para reproducir la parte práctica de este artículo, yo partiría de un entorno bastante sencillo:

- `Azure CLI` 2.75 o superior, con sesión iniciada mediante `az login`.
- Permisos para leer Microsoft Entra ID y Azure RBAC; como mínimo, capacidad para consultar aplicaciones, *service principals* y asignaciones de rol en la suscripción objetivo.
- Acceso a una suscripción de Azure donde existan *service principals* usados por automatización.
- `Jq` instalado para procesar JSON desde terminal.
- Como recomendación muy seria, no como adorno, tener habilitado Defender for Cloud, porque [Microsoft recomienda activar las protecciones relevantes para este tipo de exposición](https://www.microsoft.com/en-us/security/blog/2026/09/25/storm-3168-agentic-driven-cloud-attacks-using-compromised-service-principals).

Yo comprobaría primero la versión de la CLI, simplemente para evitar perder tiempo con comportamientos raros:

```bash
az version --output json
```

La salida debería incluir una versión de `azure-cli` igual o superior a `2.75.0`.

### Paso 1: inventariar service principals con credenciales y permisos altos

La primera medida defensiva no tiene nada de exótica: saber qué identidades no humanas tienes y qué pueden hacer. Yo empezaría sacando un inventario de *service principals* y cruzándolo con asignaciones RBAC de la suscripción. Porque sí, a veces buscamos señales sofisticadas cuando todavía no hemos hecho lo básico.

Este ejemplo está pensado para Bash con `Azure CLI 2.75+`. Enumera *service principals*, consulta sus credenciales asociadas y marca aquellos que, además, tienen roles especialmente potentes en la suscripción actual.

```bash
#!/usr/bin/env bash
set -euo pipefail

subscription_id="$(az account show --query id -o tsv)"
scope="/subscriptions/${subscription_id}"

tmpfile="$(mktemp)"
trap 'rm -f "$tmpfile"' EXIT

az ad sp list --all \
  --query "[].{displayName:displayName, appId:appId, id:id}" \
  -o json > "$tmpfile"

jq -c '.[]' "$tmpfile" | while IFS= read -r item; do
  sp_id="$(jq -r '.id' <<< "$item")"
  app_id="$(jq -r '.appId' <<< "$item")"
  name="$(jq -r '.displayName // "<sin-nombre>"' <<< "$item")"

  creds="$(az ad app credential list --id "$app_id" -o json 2>/dev/null || printf '[]')"
  cred_count="$(jq 'length' <<< "$creds")"

  roles="$(az role assignment list --assignee-object-id "$sp_id" --scope "$scope" -o json 2>/dev/null || printf '[]')"
  high_roles="$(jq '[.[] | select(.roleDefinitionName == "Owner" or .roleDefinitionName == "Contributor" or .roleDefinitionName == "User Access Administrator")]' <<< "$roles")"
  high_count="$(jq 'length' <<< "$high_roles")"

  if [[ "$cred_count" -gt 0 || "$high_count" -gt 0 ]]; then
    printf 'SP=%s\n' "$name"
    printf '  appId=%s\n' "$app_id"
    printf '  credentials=%s\n' "$cred_count"
    printf '  highPrivilegeAssignments=%s\n' "$high_count"
    jq -r '.[] | "  - role=" + .roleDefinitionName + " scope=" + .scope' <<< "$high_roles"
  fi
done
```

La salida esperada es una lista de *service principals* con su `appId`, el número de credenciales registradas y, cuando aplique, roles como `Owner`, `Contributor` o `User Access Administrator` a nivel de suscripción.

Si aquí encuentras una identidad de automatización con `Contributor` sobre toda la suscripción, yo no me tranquilizaría pensando que «seguro que se necesita para algo». Puede que sí. O puede que sea un permiso heredado por pura comodidad. En cualquier caso, ya tienes una pista seria de **superficie de impacto desproporcionada** si esa credencial termina expuesta.

{{< figure src="/images/storm-3168-lo-que-me-preocupa-de-los-ataques-agentic-contra-azure-con-service-pr/body-2.png" alt="Diagrama de auditoría de service principals y permisos altos" caption="Mi punto de partida práctico: inventariar identidades no humanas, credenciales activas y asignaciones RBAC amplias." >}}{{< /figure >}}

### Qué buscar en ese inventario

Yo priorizaría cuatro señales bastante terrenales:

- *Service principals* sin propietario funcional claro.
- Secretos antiguos o con una duración excesiva.
- Asignaciones amplias a nivel de suscripción o en grupos de recursos compartidos.
- Identidades creadas para tareas pequeñas pero con permisos globales «por si acaso».

Storm-3168 me parece relevante precisamente porque muestra que, una vez comprometida una identidad válida, el atacante puede encadenar reconocimiento, acceso a secretos y destrucción de recursos dentro del plano de control de Azure. Y en ese contexto, el exceso de permisos deja de ser una mala práctica abstracta y se convierte en un multiplicador operativo.

### Paso 2: revisar actividad sospechosa y patrones de borrado en Activity Log

La segunda parte práctica consiste en mirar el plano de control. Si el actor borra recursos, quita *locks* o manipula protección de recuperación, eso deja rastro en Azure Activity Log. No te va a contar toda la historia, claro, pero sí te da una manera rápida de detectar ráfagas destructivas y *callers* que no deberían estar haciendo tantas cosas tan deprisa.

Este comando, también con `Azure CLI 2.75+`, busca en las últimas 24 horas operaciones de borrado o actividad sobre proveedores especialmente sensibles en el contexto descrito por Microsoft.

```bash
#!/usr/bin/env bash
set -euo pipefail

start_time="$(date -u -d '24 hours ago' '+%Y-%m-%dT%H:%M:%SZ')"

az monitor activity-log list \
  --start-time "$start_time" \
  --status Succeeded \
  -o json \
| jq '[.[]
    | select(
        (.operationName.value | test("/delete$"; "i")) or
        (.resourceProviderName.value | test("Microsoft.KeyVault|Microsoft.Storage|Microsoft.Sql|Microsoft.Web|Microsoft.Compute"; "i"))
      )
    | {
        eventTime,
        caller,
        operation: .operationName.value,
        resourceGroup,
        resourceId,
        status: .status.value
      }
  ]
  | sort_by(.eventTime)' # Ordeno por tiempo para ver ráfagas destructivas y cambios encadenados
```

La salida esperada es un array JSON con eventos recientes que incluyan `eventTime`, `caller`, `operation`, `resourceGroup` y `resourceId`. Si ves muchos `/delete` concentrados en poco tiempo, o un `caller` asociado a un *service principal* operando sobre recursos heterogéneos, yo lo investigaría de inmediato.

Y no, no me quedaría solo con el borrado. También revisaría operaciones sobre *locks*, cambios en Key Vault, Function Apps y App Services, porque [Microsoft describe que Storm-3168 impactó precisamente ese tipo de recursos](https://www.microsoft.com/en-us/security/blog/2026/09/25/storm-3168-agentic-driven-cloud-attacks-using-compromised-service-principals). A veces la señal más útil no es «ha borrado X», sino «ha preparado el terreno para poder borrarlo todo mejor».

### Paso 3: correlacionar un caller con su rol y su blast radius

Una vez identificas un `caller` sospechoso, la pregunta útil no es solo «qué hizo», sino «qué más podía hacer». Ahí conviene mapear su *blast radius* real en RBAC. Este tercer ejemplo toma un `appId` observado en logs y lista sus asignaciones de rol para que puedas ver el alcance real de esa identidad.

```bash
#!/usr/bin/env bash
set -euo pipefail

app_id="11111111-2222-3333-4444-555555555555"
sp_object_id="$(az ad sp show --id "$app_id" --query id -o tsv)"

az role assignment list --assignee-object-id "$sp_object_id" -o json \
| jq '[.[] | {
    principalName,
    role: .roleDefinitionName,
    scope,
    subscriptionId,
    resourceGroup
  }]
  | sort_by(.scope, .role)' # El alcance efectivo importa más que el evento aislado
```

La salida esperada es un JSON con todas las asignaciones RBAC del *service principal*. Si aparecen *scopes* amplios, como la suscripción completa, yo asumiría un potencial de impacto muy superior al evento aislado que hayas visto en los registros.

Sí, aquí he dejado un `appId` concreto de ejemplo para que el comando sea ejecutable. En un caso real, lo sustituirás por el `caller` observado en tus logs cuando corresponda a una aplicación o a un *service principal*.

{{< figure src="/images/storm-3168-lo-que-me-preocupa-de-los-ataques-agentic-contra-azure-con-service-pr/body-3.png" alt="Diagrama del blast radius de un service principal con permisos amplios" caption="Cuando correlaciono un caller con su RBAC, lo que busco no es solo el evento observado, sino todo lo que esa identidad podía hacer." >}}{{< /figure >}}

### Qué haría hoy mismo para reducir exposición

Si me preguntas por una hoja de ruta sensata, yo empezaría por aquí:

1. **Reducir secretos persistentes**. Siempre que puedas, migra automatizaciones a identidades administradas o a mecanismos con menos material secreto expuesto.
2. Recertificar permisos de *workload identities* igual que haces —o deberías hacer— con cuentas privilegiadas humanas.
3. Acotar *scopes* RBAC al recurso o grupo de recursos estrictamente necesario.
4. Separar identidades por función. Un *pipeline* que despliega web apps no necesita tocar Key Vault, SQL, Storage y *locks* de media suscripción.
5. Proteger recursos de recuperación y su gobierno. En el caso descrito por Microsoft, los mecanismos de recuperación también fueron objetivo.
6. Habilitar visibilidad y alertas sobre borrados masivos, cambios en *locks* y uso anómalo de *service principals*.

No me parece una lista glamourosa. De hecho, es bastante poco sexy (la seguridad útil tiene ese problema). Pero justamente por eso funciona: porque ataca el terreno donde una identidad válida se convierte en arma operativa.

{{< figure src="/images/storm-3168-lo-que-me-preocupa-de-los-ataques-agentic-contra-azure-con-service-pr/body-4.png" alt="Checklist visual de defensa para identidades de carga de trabajo en Azure" caption="La defensa no empieza con IA defensiva; empieza con higiene de identidades, scopes pequeños, rotación y observabilidad." >}}{{< /figure >}}

### Lo que este incidente me confirma sobre gobernanza de identidades no humanas

Durante mucho tiempo, la conversación de identidad giró alrededor de MFA, phishing resistente y cuentas humanas. Todo eso sigue importando, por supuesto. Pero ya no basta. Casos como Storm-3168 me refuerzan una idea muy concreta: **la seguridad *cloud* moderna depende tanto de la gobernanza de las *workload identities* como de la de los administradores humanos**.

Y aquí hay un matiz incómodo. Cuando el atacante usa una identidad válida con permisos legítimos, la frontera entre operación normal y operación maliciosa se vuelve mucho más fina. Por eso no alcanza con prevenir; también necesitas detectar desviaciones de comportamiento y entender qué identidades tienen capacidad real de destruir, extraer o desactivar controles. En otras palabras: ya no basta con saber quién puede entrar. Tienes que saber quién puede arrasarte la suscripción una vez dentro.

### Mi conclusión

Storm-3168 no me parece interesante solo por el componente «*agentic*». Me parece valioso porque obliga a aterrizar el debate en algo accionable: *service principals*, secretos, RBAC y telemetría. Ahí es donde un equipo de arquitectura o de identidad puede mover la aguja hoy, sin esperar a una gran iniciativa estratégica ni a una herramienta milagrosa (que, como casi siempre, no existe).

Si tuviera que resumirlo en una sola frase, sería esta: **un *service principal* comprometido con permisos amplios es una plataforma de ataque, no una simple credencial**. Y cuanto más automatizada esté tu nube, más disciplina necesitas para gobernar esas identidades antes de que alguien las use mejor que tú.

Mi recomendación final es muy simple: lee el detalle técnico de [Storm-3168](https://www.microsoft.com/en-us/security/blog/2026/09/25/storm-3168-agentic-driven-cloud-attacks-using-compromised-service-principals), compáralo con la tendencia más amplia que [Microsoft describe sobre ataques acelerados por IA](https://www.microsoft.com/en-us/security/blog/2026/09/17/from-guidance-to-action-security-fundamentals-that-materially-reduce-risk), y dedica una tarde a revisar tus identidades no humanas con los pasos de arriba. Esa tarde, sinceramente, puede salirte muchísimo más barata que una semana entera de respuesta a incidente.
