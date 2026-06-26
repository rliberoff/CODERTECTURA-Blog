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

## Agente de descubrimiento de temas (Tavily)

El script `automation/scripts/discover_topics.py` (apoyado en el módulo compartido `automation/scripts/_foundry.py`) descubre artículos técnicos recientes en los dominios oficiales de Microsoft y GitHub, valida sus fechas, deduplica y escribe los que pasan como ficheros `candidate` en este ledger. Es la **Fase 1** del pipeline; las fases de redacción e imágenes consumirán estos candidatos más adelante.

### Cómo funciona

- **Bucle agéntico (ReAct)** sobre la superficie sin claves `POST {endpoint}/openai/v1/chat/completions` con una única herramienta, `tavily_search`. El modelo decide *qué* buscar; el **orquestador** (este script) ejecuta cada búsqueda HTTP en Tavily.
- La **lista blanca de dominios es una constante del servidor** y nunca procede de la salida del modelo: `learn.microsoft.com`, `devblogs.microsoft.com`, `techcommunity.microsoft.com`, `azure.microsoft.com`, `microsoft.com`, `github.blog`, `github.com`, `githubnext.com`.
- Todo el contenido web se trata como **datos no fiables** (mitigación de inyección de prompts): se sanea, se delimita en un bloque "UNTRUSTED" y el orquestador es quien aplica la lista blanca, los topes y la escritura de ficheros con `yaml.safe_dump`.

### Validación de fechas (fail-closed)

- La fecha de publicación se resuelve en este orden: `published_date` de Tavily → fecha extraída de la URL o del contenido → si no hay ninguna fiable, se considera **sin fecha**.
- *Fresco* = dentro de `TAVILY_FRESHNESS_DAYS` (por defecto 30). Cualquier cosa más antigua que el tope duro (`TAVILY_HARD_CAP_DAYS`, por defecto 90) se descarta.
- Un candidato necesita **al menos una fuente primaria fresca y con fecha**. Las fuentes sin fecha solo se adjuntan como secundarias.

### Deduplicación en el descubrimiento

- **Exacta**: `slug`/`title` del candidato frente a los temas del ledger y a los posts publicados en `content/posts/*.md`.
- **Semántica**: similitud coseno de *embeddings* frente a temas publicados o encolados; se registra en `similarity` y se omite el candidato si `max_score` supera el umbral (`SIMILARITY_THRESHOLD`, por defecto 0.82).

### Campo añadido al esquema: `sources`

Además de los campos del [esquema de un tema](#esquema-de-un-tema), los candidatos generados por este agente incluyen una clave **`sources`**: una lista (máximo 5) de los artículos de respaldo, con la fuente primaria primero. Cada entrada tiene `url`, `title`, `published_date`, `host` y `kind` (`primary` o `secondary`). Sirve de contexto de redacción e imágenes para la Fase 2. El campo `source` (singular, obligatorio) sigue apuntando a la fuente primaria.

### Variables de entorno

La autenticación de Azure no cambia: el workflow adquiere el token con OIDC/UAMI y lo pasa por `AOAI_TOKEN` (scope `https://cognitiveservices.azure.com`, válido para chat y embeddings). El script nunca llama a la CLI de Azure.

| Variable | Tipo | Por defecto | Descripción |
| ---------- | ------ | ------------- | ------------- |
| `TAVILY_API_KEY` | Secret | — | Clave de Tavily. Solo en GitHub Secrets; nunca se imprime ni se registra. |
| `AOAI_TOKEN` | Token efímero | — | Bearer pre-adquirido (env únicamente). |
| `AOAI_ENDPOINT` | Variable | — | Endpoint de Foundry (ya existe en el pipeline). |
| `AOAI_TEXT_DEPLOYMENT` | Variable | `gpt-5.4-mini` | Despliegue de chat usado como planificador. |
| `AZURE_OPENAI_DEPLOYMENT_EMBEDDINGS` | Variable | `text-embedding-3-large` | Despliegue de embeddings para la dedup semántica. |
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

- Las fuentes llegan por **fichero** (`SOURCES_FILE`, JSON UTF-8), nunca por argumentos, igual que `IMAGE_PROMPT_FILE`. Se aceptan tanto una lista como un objeto con clave `sources`; cada entrada es `{url, title, published_date, host, kind}` y, opcionalmente, un extracto (`raw_content`/`text`/`snippet`) y candidatos de imagen (`images`).
- Todo el contenido se trata como **DATOS EXTERNOS NO FIABLES**: el host se revalida contra la lista blanca, el texto se sanea y se inyecta en el prompt dentro de un bloque delimitado con la instrucción de no seguir órdenes que aparezcan dentro y de citar **solo** las URLs proporcionadas (enlaces Markdown).
- La portada (`image_prompt`) se ancla al título y al contenido real del artículo con un estilo **cinematográfico de alto impacto**: una escena conceptual con un sujeto protagonista (siluetas, figuras de espaldas o robots/mascotas, sin rostros reales), composición dramática, profundidad e iluminación volumétrica, sobre base oscura azul medianoche con color cinematográfico libre y vibrante; reserva una zona inferior más sobria para el título superpuesto y nunca lleva texto aun que si logos de productos o marcas. Las imágenes de cuerpo de IA divergen a propósito: mantienen la **familia visual de CODERTECTURA** plana y explicativa para ilustrar conceptos y diagramas.
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

Para `type: "source"`, el modelo **solo** indica `source_url` (el artículo, para la atribución). El orquestador selecciona la URL de imagen concreta a partir de los candidatos `images` de esa fuente y la fija en la especificación (`image_url`), de modo que una URL de imagen **nunca** procede de la salida del modelo (defensa SSRF).

### Resolución de imágenes de cuerpo (`resolve_body_images.py`)

Sustituye cada marcador por una llamada al shortcode `figure` apuntando al fichero guardado. Es **tolerante por imagen** (si una falla, se avisa y se elimina su marcador) y **seguro en conjunto** (una especificación ausente o vacía es un no-op correcto). La portada (`generate_image.py`) sigue siendo la única imagen obligatoria.

- `type: "ai"`: genera la imagen con MAI-Image-2.5 y la guarda en `static/images/<slug>/body-<n>.png`.
- `type: "source"` (extracción real, sensible a derechos de autor): el host de la imagen debe estar en la lista blanca; **no** se siguen redirecciones a hosts fuera de ella y se revalida la URL **final**; se validan los **números mágicos** (PNG, JPEG, WebP, GIF) y un **tope de tamaño** (8 MB por defecto) **antes** de escribir; se guarda en `static/images/<slug>/source-<n>.<ext>`. El pie incluye atribución visible: `Fuente: [<host>](<source_url>)`.

### Variables de entorno (Fase 2)

| Variable | Tipo | Por defecto | Descripción |
| ---------- | ------ | ------------- | ------------- |
| `SOURCES_FILE` | Variable | (vacío) | Ruta a un JSON con las fuentes de fundamento (`generate_article.py`). Ausente → flujo manual sin cambios. |
| `BODY_IMAGES_FILE` | Variable | (vacío) | Ruta donde `generate_article.py` escribe la especificación de imágenes y de donde `resolve_body_images.py` la lee. Ausente → sin imágenes de cuerpo. |
| `POST_PATH` | Variable | (de la especificación) | `.md` a reescribir (`resolve_body_images.py`). |
| `POST_SLUG` | Variable | (de la especificación) | Slug para derivar `static/images/<slug>/`. |
| `STATIC_IMAGES_DIR` | Variable | `static/images` | Raíz de imágenes. |
| `AOAI_IMAGE_DEPLOYMENT` | Variable | — | Despliegue de imagen (MAI-Image-2.5) para imágenes `type:ai`. |
| `AOAI_BODY_IMAGE_SIZE` | Variable | `1024x1024` | Tamaño de las imágenes de cuerpo generadas por IA. |
| `AOAI_IMAGE_TIMEOUT` | Variable | `300` | Timeout HTTP de generación de imagen (segundos). |
| `BODY_IMAGE_DOWNLOAD_TIMEOUT` | Variable | `30` | Timeout de descarga de imágenes de fuente (segundos). |
| `BODY_IMAGE_MAX_BYTES` | Variable | `8388608` | Tamaño máximo aceptado de una imagen de fuente (bytes). |

Las pruebas offline cubren el parseo del fichero de fuentes, la validación del contrato `body_images`, la reescritura de marcadores a `figure`, los números mágicos (aceptar/rechazar), el rechazo de redirecciones fuera de la lista blanca y el no-op con especificación vacía (cliente de imagen y descarga HTTP simulados; sin red).

