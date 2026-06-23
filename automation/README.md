# Ledger de temas (`automation/topics/`)

El *ledger de temas* es la memoria persistente del pipeline de artículos asistido por IA de este blog. Es git-nativo: un fichero YAML pequeño por tema bajo `automation/topics/`, versionado junto al resto del repositorio.

## Propósito

El ledger cumple tres funciones:

- **Memoria**: recuerda qué temas se han descubierto, propuesto o descartado entre ejecuciones, para no empezar de cero cada vez.
- **Deduplicación**: evita proponer temas repetidos o demasiado parecidos a lo ya publicado o encolado.
- **Auditoría**: cada cambio queda registrado en el historial de git (quién, cuándo y por qué cambió un estado), sin necesidad de una base de datos externa.

## Estructura de archivos

- Un fichero por tema: `automation/topics/<id>.yaml`.
- El nombre del fichero (`<id>`) coincide con el campo `id` y actúa como clave primaria.
- Los ficheros cuyo nombre empieza por `_` (guion bajo) son plantillas o ejemplos y el escáner los ignora (ver [Convención de plantillas](#convención-de-plantillas)).

## Esquema de un tema

Cada fichero YAML describe un único tema con los campos siguientes.

| Campo | Tipo | Obligatorio | Descripción |
| ------- | ------ | :-----------: | ------------- |
| `id` | string | Sí | Identificador único y estable (kebab-case). Coincide con el nombre del fichero y es la clave primaria. |
| `title` | string | Sí | Título propuesto del artículo, en español. Parte de la clave de deduplicación exacta. |
| `slug` | string | Sí | Slug del artículo (kebab-case, ASCII). Al publicar debe coincidir con `content/posts/<slug>.md`. Parte de la deduplicación exacta. |
| `status` | enum | Sí | Estado en el ciclo de vida (ver tabla de estados). |
| `source` | url | Sí | URL oficial de Microsoft que respalda el tema (fuente autorizada). |
| `discovered_at` | datetime | Sí | Fecha y hora de descubrimiento en ISO 8601 con zona horaria. |
| `language` | string | Sí | Idioma del contenido. En este blog, siempre `es`. |
| `similarity` | objeto | Sí | Resultado de la deduplicación semántica (ver subcampos). |
| `similarity.max_score` | número | Sí | Máxima similitud (coseno, `0..1`) frente a temas publicados o encolados. |
| `similarity.closest_match` | string | Sí | `id` o `slug` del tema más parecido encontrado. |
| `similarity.threshold` | número | Sí | Umbral de novedad. Por defecto `0.82`. |
| `notes` | string | No | Notas libres para personas (contexto, ángulo editorial, recordatorios). |
| `pr_url` | url \| null | Sí | URL del Pull Request asociado. `null` hasta que se abre un PR. |

## Ciclo de vida (estados)

Un tema avanza por estos estados:

```text
candidate -> queued -> in_review -> published
                                 -> rejected
                                 -> parked
```

| Estado | Significado |
| ------ | ----------- |
| `candidate` | Descubierto, todavía sin validar. |
| `queued` | Aprobado y en cola para generación. |
| `in_review` | Hay un PR abierto, pendiente de revisión humana. |
| `published` | Publicado; existe el `.md` correspondiente en `content/posts/`. |
| `rejected` | Descartado por falta de valor editorial o estar fuera de alcance. |
| `parked` | Aparcado temporalmente; se podrá retomar más adelante. |

## Deduplicación

Antes de aceptar un tema nuevo se aplican dos claves complementarias:

- **Clave exacta (a)**: coincidencia exacta de `slug` o `title` frente a temas existentes. Si coincide, es un duplicado y se omite.
- **Clave semántica (b)**: comparación por *embeddings* (similitud coseno) contra todo lo publicado o encolado. Se calcula `similarity.max_score`.

El **umbral de novedad** (`threshold`, por defecto `0.82`) decide la novedad: si `max_score` es **estrictamente mayor** que el umbral, el tema se considera *demasiado parecido* a algo existente y se omite. Si es igual o menor, el tema se considera suficientemente nuevo.

## Índice de publicados (derivado en vivo)

El índice de artículos publicados **no se almacena** en el ledger. Se deriva en cada ejecución escaneando `content/posts/*.md`.

- `content/posts/` es la **única fuente de verdad** de lo que está publicado.
- Si el ledger y la realidad del repositorio discrepan, **gana el escaneo** del directorio de posts.
- Esto hace el sistema **autorreparable**: borrar o renombrar un post se refleja automáticamente, sin mantener un índice paralelo que pueda quedar obsoleto.

## Convención de plantillas

Los ficheros cuyo nombre empieza por `_` (guion bajo) son plantillas o ejemplos y **el escáner de temas los ignora**.

- Ejemplo: `automation/topics/_example.yaml` documenta el esquema completo pero nunca se procesa.
- Para crear un tema real, copia la plantilla a `automation/topics/<id>.yaml` (sin guion bajo) y rellena los campos con valores reales.
