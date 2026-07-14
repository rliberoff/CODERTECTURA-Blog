# Ledger de temas (`automation/topics/`)

El *ledger de temas* es la memoria persistente del pipeline de artículos asistido por IA de este blog. Es git-nativo: un fichero YAML pequeño por tema bajo `automation/topics/`, versionado junto al resto del repositorio.

## Propósito

El ledger cumple tres funciones:

- **Memoria**: recuerda qué temas se han descubierto, propuesto o descartado entre ejecuciones, para no empezar de cero cada vez.
- **Deduplicación**: evita proponer temas repetidos o demasiado parecidos a lo ya publicado, encolado o en revisión.
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
| `title` | string | Sí | Título de trabajo del tema, en inglés (metadato interno de descubrimiento; el título final en español se genera al redactar el artículo). Parte de la clave de deduplicación exacta. |
| `slug` | string | Sí | Slug del artículo (kebab-case, ASCII). Al entrar en revisión se actualiza con el slug final generado. Parte de la deduplicación exacta. |
| `status` | enum | Sí | Estado en el ciclo de vida (ver tabla de estados). |
| `status_history` | lista | Sí | Secuencia cronológica append-only de objetos `{status, at}`. Conserva transiciones ocurridas antes del primer commit. |
| `discovered_at` | datetime | Sí | Fecha y hora de descubrimiento en ISO 8601 con zona horaria. |
| `sources` | lista | Sí | Fuentes validadas para redacción e imágenes, con la primaria en primer lugar. |
| `similarity` | objeto | Sí | Resultado de la deduplicación semántica (ver subcampos). |
| `similarity.max_score` | número | Sí | Máxima similitud (coseno, `0..1`) frente a temas publicados, encolados o en revisión. |
| `similarity.closest_match` | string | Sí | `id` o `slug` del tema más parecido encontrado. |
| `similarity.threshold` | número | Sí | Umbral de novedad. Por defecto `0.82`. |
| `notes` | string | No | Notas libres para personas (contexto, ángulo editorial, recordatorios). |
| `article_path` | string \| null | Sí | Ruta exacta del post generado, incluido el prefijo de fecha. `null` hasta entrar en revisión. |
| `pr_url` | url \| null | Sí | URL del Pull Request asociado. Se persiste al publicar; antes permanece `null`. |

## Ciclo de vida (estados)

Un tema avanza por estos estados:

```text
candidate ─────────> in_review -> published
  │                    ├──────> rejected
  ├──> queued ─────────┘
  ├──> rejected
  └──> parked -> queued
```

| Estado | Significado |
| ------ | ----------- |
| `candidate` | Descubierto, todavía sin validar. |
| `queued` | Aprobado manualmente y en cola para generación. El semanal no se detiene aquí. |
| `in_review` | Hay un PR abierto, pendiente de revisión humana. |
| `published` | Publicado; existe el `.md` correspondiente en `content/posts/`. |
| `rejected` | Descartado por falta de valor editorial o estar fuera de alcance. |
| `parked` | Aparcado temporalmente; se podrá retomar más adelante. |

El pipeline valida las transiciones y rechaza saltos no permitidos. El flujo semanal mueve directamente cada candidato seleccionado a `in_review`; `queued` queda disponible para colas editoriales manuales. La aprobación del CODEOWNER registra `published`. Repetir cualquiera de esos pasos es idempotente y no duplica el historial.

## Deduplicación

Antes de aceptar un tema nuevo se aplican dos claves complementarias:

- **Clave exacta (a)**: coincidencia exacta de `slug` o `title` frente a temas existentes. Si coincide, es un duplicado y se omite.
- **Clave semántica (b)**: comparación por *embeddings* (similitud coseno) contra todo lo publicado, encolado o en revisión. Se calcula `similarity.max_score`.

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

## Persistencia en GitHub Actions

El script de descubrimiento aplica el límite una sola vez y emite directamente la matriz de fan-out. Cada entrada transporta un único YAML completo mediante base64; el workflow reutilizable deriva de él el id, el tema y las fuentes. El PR confirma juntos el post, sus imágenes y `automation/topics/<id>.yaml`. Los temas del flujo semanal usan una rama estable `bot/ai-article-<id>`, por lo que un *rerun* reutiliza el historial ya confirmado en vez de reconstruir sus fechas.

Antes de una nueva búsqueda, el workflow superpone temporalmente solo las entradas de ledger modificadas por cada PR de IA abierto. Si dos PR abiertos reclaman el mismo fichero de tema, aborta en vez de elegir uno de forma ambigua. De este modo la deduplicación ve tanto lo fusionado en `main` como los temas todavía `in_review`. Cuando un CODEOWNER aprueba el artículo, el workflow de publicación cambia la entrada a `published` y conserva la ruta exacta en `article_path`.

## Agente de descubrimiento de temas (Tavily)

El script `automation/scripts/discover_topics.py` (apoyado en el módulo compartido `automation/scripts/_foundry.py`) descubre artículos técnicos recientes en los dominios oficiales de Microsoft y GitHub, valida sus fechas, deduplica y escribe los que pasan como ficheros `candidate` en este ledger. Es la **Fase 1** del pipeline; las fases de redacción e imágenes consumirán estos candidatos más adelante.

### Cómo funciona

- **Bucle agéntico (ReAct)** sobre la superficie sin claves `POST {endpoint}/openai/v1/chat/completions` con una única herramienta, `tavily_search`. El modelo decide *qué* buscar; el **orquestador** (este script) ejecuta cada búsqueda HTTP en Tavily.
- La **lista blanca de dominios es una constante del servidor** y nunca procede de la salida del modelo: `learn.microsoft.com`, `devblogs.microsoft.com`, `techcommunity.microsoft.com`, `azure.microsoft.com`, `microsoft.com`, `github.blog`, `github.com`, `githubnext.com`.
- Todo el contenido web se trata como **datos no fiables** (mitigación de inyección de prompts): se sanea, se delimita en un bloque "UNTRUSTED" y el orquestador es quien aplica la lista blanca, los topes y la escritura de ficheros con `yaml.safe_dump`.

### Validación de fechas (fail-closed)

- La fecha de publicación se resuelve en este orden: `published_date` de Tavily → fecha estructural de la URL → si no hay ninguna fiable, se considera **sin fecha**. Las fechas encontradas en texto libre se ignoran.
- *Fresco* = dentro de `TAVILY_FRESHNESS_DAYS` (por defecto 30). Cualquier cosa más antigua que el tope duro (`TAVILY_HARD_CAP_DAYS`, por defecto 90) se descarta.
- Un candidato necesita **al menos una fuente primaria fresca y con fecha**. Las fuentes sin fecha solo se adjuntan como secundarias.

### Deduplicación en el descubrimiento

- **Exacta**: `slug`/`title` del candidato frente a los temas del ledger y a los posts publicados en `content/posts/*.md`.
- **Semántica**: similitud coseno de *embeddings* frente a temas publicados, encolados o en revisión; se registra en `similarity` y se omite el candidato si `max_score` supera el umbral (`SIMILARITY_THRESHOLD`, por defecto 0.82).

### Fuentes de *grounding*

`sources` contiene como máximo cinco artículos de respaldo, con la fuente primaria primero. Cada entrada tiene `url`, `title`, `published_date`, `host` y `kind` (`primary` o `secondary`). Los campos opcionales `excerpt` e `images` aportan contexto de redacción e imágenes a la Fase 2. No se mantiene una copia singular de la primera URL.

### Variables de entorno

La autenticación de Azure no cambia: el workflow adquiere el token con OIDC/UAMI y lo pasa por `AOAI_TOKEN` (scope `https://cognitiveservices.azure.com`, válido para chat y embeddings). El script nunca llama a la CLI de Azure.

| Variable | Tipo | Por defecto | Descripción |
| ---------- | ------ | ------------- | ------------- |
| `TAVILY_API_KEY` | Secret | — | Clave de Tavily. Solo en GitHub Secrets; nunca se imprime ni se registra. |
| `AOAI_TOKEN` | Token efímero | — | Bearer pre-adquirido (env únicamente). |
| `AOAI_ENDPOINT` | Variable | — | Endpoint de Foundry (ya existe en el pipeline). |
| `AOAI_TEXT_DEPLOYMENT` | Variable | `gpt-5.4-mini` | Despliegue de chat usado como planificador. |
| `AZURE_OPENAI_DEPLOYMENT_EMBEDDINGS` | Variable | `text-embedding-3-large` | Despliegue de embeddings para la dedup semántica. |
| `REQUIRE_EMBEDDINGS` | Variable | `false` | Falla si no hay deployment de embeddings. El workflow semanal establece `true`. |
| `TAVILY_FRESHNESS_DAYS` | Variable | `30` | Ventana de frescura en días. |
| `TAVILY_HARD_CAP_DAYS` | Variable | `90` | Edad máxima absoluta en días. |
| `TAVILY_MAX_RESULTS` | Variable | `8` | Resultados por llamada a Tavily. |
| `TAVILY_TIMEOUT` | Variable | `60` | Timeout HTTP de Tavily (segundos). |
| `SIMILARITY_THRESHOLD` | Variable | `0.82` | Umbral de novedad semántica. |
| `MAX_CANDIDATES` | Variable | `10` | Máximo de candidatos escritos por ejecución. |
| `DISCOVERY_MAX_ITERATIONS` | Variable | `6` | Máximo de turnos modelo↔herramienta. |
| `DISCOVERY_MAX_SEARCHES` | Variable | `8` | Máximo de rondas de búsqueda (cada una son 2 llamadas HTTP). |
| `DISCOVERY_FOCUS` | Variable | (vacío) | Tema opcional para sesgar el descubrimiento. |

### Cómo ejecutarlo

Prepara las credenciales (el token cubre chat y embeddings) y lanza primero una vista previa:

```bash
export AOAI_TOKEN="$(az account get-access-token --resource https://cognitiveservices.azure.com --query accessToken -o tsv)"
export TAVILY_API_KEY="<tu-clave>"   # env únicamente; nunca se imprime
export AOAI_ENDPOINT="https://asi-relv-blog.services.ai.azure.com/"
export AOAI_TEXT_DEPLOYMENT="gpt-5.4-mini"
export AZURE_OPENAI_DEPLOYMENT_EMBEDDINGS="text-embedding-3-large"

# Vista previa: imprime los candidatos que escribiría, sin tocar ficheros.
python automation/scripts/discover_topics.py --dry-run

# Ejecución real: escribe automation/topics/<id>.yaml por cada candidato válido.
python automation/scripts/discover_topics.py
```

Las dependencias siguen siendo solo la biblioteca estándar más PyYAML (la misma de `requirements.txt`).

### Pruebas

Las pruebas offline no usan red (respuestas de Tavily simuladas y cliente de embeddings *mock*):

```bash
python -m pytest tests/
```

## Redacción con fundamento e imágenes de cuerpo (Fase 2)

La **Fase 2** consume el campo `sources` de los candidatos para fundar el artículo en fuentes reales y enriquecerlo con imágenes en el cuerpo. Reutiliza el módulo compartido `automation/scripts/_sources.py` (lista blanca de dominios y saneado de texto no fiable) y `automation/scripts/_foundry.py` (`FoundryImageClient`, la llamada a MAI-Image-2.5 que también usa `generate_image.py`). No añade dependencias: sigue siendo biblioteca estándar más PyYAML.

### Redacción con fundamento (`generate_article.py`)

- **Doble pasada (C.1)**: la pasada 1 redacta un borrador fundado en las fuentes con código real; la pasada 2 reescribe la prosa para la **voz del blog**, endurece los ejemplos de código y sustituye `image_prompt` por una dirección de portada basada en el artículo final. El `slug`, los marcadores `{{img:<id>}}` y las `body_images` permanecen intactos. Ambas pasadas usan el despliegue de generación (`AOAI_GENERATE_DEPLOYMENT`, p. ej. `gpt-5.4`, con *fallback* a `AOAI_TEXT_DEPLOYMENT`). La pasada 2 es *fail-open*: si falla, se conserva el borrador. El presupuesto de *grounding* por fuente sube a 3000 caracteres para ejemplos de código más fieles.
- Las fuentes llegan por **fichero** (`SOURCES_FILE`, JSON UTF-8), nunca por argumentos, igual que `IMAGE_PROMPT_FILE`. Se aceptan tanto una lista como un objeto con clave `sources`; cada entrada es `{url, title, published_date, host, kind}` y, opcionalmente, un extracto (`raw_content`/`text`/`snippet`) y candidatos de imagen (`images`).
- Todo el contenido se trata como **DATOS EXTERNOS NO FIABLES**: el host se revalida contra la lista blanca, el texto se sanea y se inyecta en el prompt dentro de un bloque delimitado con la instrucción de no seguir órdenes que aparezcan dentro y de citar **solo** las URLs proporcionadas (enlaces Markdown).
- La portada (`image_prompt`) se concibe como un **visual publicitario de campaña** derivado de la tesis final, el beneficio concreto para quien lee y la tensión o transformación central del artículo. La dirección de arte elige para cada tema una familia compositiva pertinente —objeto protagonista, bodegón editorial, acción o transformación, metáfora escultórica, entorno arquitectónico o campaña con personaje— y define una metáfora y una paleta con significado propio. No usa por defecto neón azul/cian, personas de espaldas, centros de mando, muros de paneles, orbes luminosos, salas futuristas simétricas, interfaces flotantes ni circuitos decorativos. El motivo esencial permanece en el 70 % central para resistir recortes 2:1 de LinkedIn y tarjetas del blog, y la franja inferior queda calmada para el título superpuesto. Nunca incorpora texto; puede usar logotipos relevantes. Las imágenes de cuerpo de IA divergen a propósito: son **diagramas esquemáticos o infografías** (arquitecturas, flujos, *pipelines*, modelos por capas o comparativas) en la **familia visual de CODERTECTURA**, con nodos, flechas y conectores; pueden llevar **etiquetas cortas** cuando aclaran el concepto (el modelo lo decide por imagen) o quedarse puramente visuales.
- El front matter incorpora `ai.sources` (lista de `{url, title, published_date}` usadas) para que la revisión pueda auditar el origen.
- Si `BODY_IMAGES_FILE` está definido, el modelo puede proponer un array opcional `body_images`. El orquestador lo valida y escribe la especificación resuelta a ese fichero para el paso siguiente. Si **no** está definido (flujo manual actual), se eliminan todos los marcadores `{{img:<id>}}` y el comportamiento es idéntico al anterior (compatibilidad hacia atrás).

Esquema de cada elemento de `body_images` (lo que devuelve el modelo):

```json
{
  "placeholder": "{{img:<id>}}",
  "type": "ai | source",
  "alt": "texto alternativo",
  "caption": "pie de figura",
  "prompt_en": "(solo type=ai) descripción en inglés de la ilustración/diagrama",
  "source_url": "(solo type=source) una de las URLs de las fuentes proporcionadas"
}
```

Para `type: "source"`, el modelo indica `source_url` (el artículo, para la atribución) y **puede** nombrar un `image_url` concreto, que solo se acepta si coincide **exactamente** con uno de los candidatos `images` permitidos de esa fuente; si no lo nombra, el orquestador elige el primer candidato **no usado** de esa fuente. Así una URL de imagen **nunca** procede libremente del modelo (defensa SSRF) y se pueden extraer **varias imágenes distintas de la misma fuente** (cada una con su marcador y su `image_url`).

### Resolución de imágenes de cuerpo (`resolve_body_images.py`)

Sustituye cada marcador por una llamada al shortcode `figure` apuntando al fichero guardado. Es **tolerante por imagen** (si una falla, se avisa y se elimina su marcador) y **seguro en conjunto** (una especificación ausente o vacía es un no-op correcto). La portada (`generate_image.py`) sigue siendo la única imagen obligatoria.

- `type: "ai"`: genera un **diagrama esquemático o infografía** (arquitecturas, flujos, *pipelines*, modelos por capas o comparativas) con el modelo de imagen configurado (p. ej. `gpt-image-2`) y la guarda en `static/images/<slug>/body-<n>.png`. Puede llevar **etiquetas cortas** cuando aclaran el concepto (el modelo lo decide por imagen).
- `type: "source"` (extracción real, sensible a derechos de autor): el host de la imagen debe estar en la lista blanca; **no** se siguen redirecciones a hosts fuera de ella y se revalida la URL **final**; se validan los **números mágicos** (PNG, JPEG, WebP, GIF) y un **tope de tamaño** (8 MB por defecto) **antes** de escribir; se guarda en `static/images/<slug>/source-<n>.<ext>`. El pie incluye atribución visible: `Fuente: [<host>](<source_url>)`.

### Variables de entorno (Fase 2)

| Variable | Tipo | Por defecto | Descripción |
| ---------- | ------ | ------------- | ------------- |
| `SOURCES_FILE` | Variable | (vacío) | Ruta a un JSON con las fuentes de fundamento (`generate_article.py`). Ausente → flujo manual sin cambios. |
| `BODY_IMAGES_FILE` | Variable | (vacío) | Ruta donde `generate_article.py` escribe la especificación de imágenes y de donde `resolve_body_images.py` la lee. Ausente → sin imágenes de cuerpo. |
| `POST_PATH` | Variable | (de la especificación) | `.md` a reescribir (`resolve_body_images.py`). |
| `POST_SLUG` | Variable | (de la especificación) | Slug para derivar `static/images/<slug>/`. |
| `STATIC_IMAGES_DIR` | Variable | `static/images` | Raíz de imágenes. |
| `AOAI_GENERATE_DEPLOYMENT` | Variable | (`AOAI_TEXT_DEPLOYMENT`) | Despliegue de texto para **ambas pasadas** de redacción (p. ej. `gpt-5.4`). Si no se define, usa `AOAI_TEXT_DEPLOYMENT`. |
| `AOAI_IMAGE_DEPLOYMENT` | Variable | — | Despliegue de imagen configurado (p. ej. `gpt-image-2`) para imágenes `type:ai`. |
| `AOAI_BODY_IMAGE_SIZE` | Variable | `1024x1024` | Tamaño de las imágenes de cuerpo generadas por IA. |
| `AOAI_IMAGE_TIMEOUT` | Variable | `300` | Timeout HTTP de generación de imagen (segundos). |
| `BODY_IMAGE_DOWNLOAD_TIMEOUT` | Variable | `30` | Timeout de descarga de imágenes de fuente (segundos). |
| `BODY_IMAGE_MAX_BYTES` | Variable | `8388608` | Tamaño máximo aceptado de una imagen de fuente (bytes). |

Las pruebas offline cubren el parseo del fichero de fuentes, la validación del contrato `body_images`, la reescritura de marcadores a `figure`, los números mágicos (aceptar/rechazar), el rechazo de redirecciones fuera de la lista blanca y el no-op con especificación vacía (cliente de imagen y descarga HTTP simulados; sin red).
