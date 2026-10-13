# LinkedIn Article editor scripts

Run these snippets with the Chrome extension's `javascript_tool`. Run source scripts on the canonical CODERTECTURA post and editor scripts on the LinkedIn Article editor.

## Extract the CODERTECTURA article

This function extracts only `article.post .post__content`. It replaces images with stable markers, converts Hugo-specific elements, normalizes URLs, and builds the manifest used by every later audit.

```js
function extractCodertecturaArticle() {
  const article = document.querySelector('article.post');
  const titleElement = article?.querySelector('.post__header h1');
  const sourceBody = article?.querySelector('.post__content');
  if (!article || !titleElement || !sourceBody) {
    throw new Error('CODERTECTURA article, title, or .post__content was not found.');
  }

  const canonicalElement = document.querySelector('link[rel="canonical"]');
  const canonicalUrl = new URL(canonicalElement?.href || location.href).href;
  const canonicalSource = canonicalElement ? 'link[rel="canonical"]' : 'location.href';
  const language = (document.documentElement.lang || 'es').toLowerCase();
  const hadRepublishedNotice = !!sourceBody.querySelector('.notice--republished');
  const sourceSnapshot = {
    selector: 'article.post .post__content',
    className: sourceBody.className,
    directChildren: sourceBody.children.length,
    paragraphs: sourceBody.querySelectorAll('p').length,
    headings: sourceBody.querySelectorAll('h1, h2, h3, h4, h5, h6').length,
    h2: sourceBody.querySelectorAll('h2').length,
    h3: sourceBody.querySelectorAll('h3').length,
    orderedLists: sourceBody.querySelectorAll('ol').length,
    unorderedLists: sourceBody.querySelectorAll('ul').length,
    listItems: sourceBody.querySelectorAll('li').length,
    links: sourceBody.querySelectorAll('a[href]').length,
    figures: sourceBody.querySelectorAll('figure').length,
    images: sourceBody.querySelectorAll('img[src]').length,
    codeBlocks: sourceBody.querySelectorAll('pre').length,
    blockquotes: sourceBody.querySelectorAll('blockquote').length,
    tables: sourceBody.querySelectorAll('table').length,
    notices: sourceBody.querySelectorAll('aside.notice').length,
    galleries: sourceBody.querySelectorAll('figure.content-gallery').length,
    embeds: sourceBody.querySelectorAll('.responsive-embed, video, iframe').length
  };
  const body = sourceBody.cloneNode(true);
  const media = [];
  let mediaIndex = 0;

  const normalizeText = value => (value || '').replace(/\s+/g, ' ').trim();
  const absoluteUrl = value => value ? new URL(value, canonicalUrl).href : '';
  const nextMediaIdentity = url => {
    mediaIndex += 1;
    const id = `LI_MEDIA_${String(mediaIndex).padStart(3, '0')}`;
    const marker = `[[${id}]]`;
    const pathName = decodeURIComponent(new URL(url).pathname.split('/').pop() || 'image');
    const safeName = pathName.replace(/[^a-zA-Z0-9._-]+/g, '-');
    return { id, marker, fileName: `${id.toLowerCase()}-${safeName}` };
  };
  const getCaptionDetails = caption => {
    if (!caption) return { captionText: '', fullCaptionText: '', links: [] };
    const fullCaptionText = normalizeText(caption.textContent);
    const links = [...caption.querySelectorAll('a[href]')].map(link => ({
      text: normalizeText(link.textContent),
      url: absoluteUrl(link.getAttribute('href'))
    }));
    return { captionText: fullCaptionText, fullCaptionText, links };
  };
  const markerParagraph = marker => {
    const paragraph = document.createElement('p');
    paragraph.textContent = marker;
    return paragraph;
  };
  const richCaptionParagraph = caption => {
    const paragraph = document.createElement('p');
    const emphasis = document.createElement('em');
    emphasis.append(...[...caption.cloneNode(true).childNodes]);
    paragraph.append(emphasis);
    return paragraph;
  };
  const addImage = (image, caption, groupId) => {
    const url = absoluteUrl(image.getAttribute('src'));
    if (!url) return null;

    const identity = nextMediaIdentity(url);
    const captionDetails = getCaptionDetails(caption);
    const captionText = !captionDetails.links.length && captionDetails.captionText.length <= 250
      ? captionDetails.captionText
      : '';
    const entry = {
      ...identity,
      kind: 'image',
      url,
      alt: normalizeText(image.getAttribute('alt')),
      captionText,
      fullCaptionText: captionDetails.fullCaptionText,
      captionHtml: caption?.innerHTML || '',
      captionLinks: captionDetails.links,
      groupId: groupId || null
    };
    const nodes = [markerParagraph(identity.marker)];
    if (caption && !captionText) nodes.push(richCaptionParagraph(caption));
    media.push(entry);
    return nodes;
  };
  const linkedMediaParagraph = element => {
    const source = element.querySelector('iframe[src], video source[src], video[src]');
    const url = absoluteUrl(source?.getAttribute('src'));
    if (!url) return document.createTextNode('');

    const title = normalizeText(
      element.querySelector('iframe[title]')?.getAttribute('title') ||
      element.closest('figure')?.querySelector('figcaption')?.textContent ||
      (language.startsWith('es') ? 'Contenido multimedia' : 'Embedded media')
    );
    const paragraph = document.createElement('p');
    const label = document.createElement('strong');
    const link = document.createElement('a');
    label.textContent = `${title}: `;
    link.href = url;
    link.textContent = url;
    paragraph.append(label, link);
    return paragraph;
  };

  const candidates = [...body.querySelectorAll('figure, .responsive-embed, img')];
  for (const candidate of candidates) {
    if (!body.contains(candidate)) continue;

    if (candidate.matches('figure')) {
      if (candidate.matches('.content-video')) {
        const video = candidate.querySelector('video');
        const poster = video?.getAttribute('poster');
        const replacements = [];
        if (poster) {
          const posterImage = document.createElement('img');
          posterImage.src = absoluteUrl(poster);
          posterImage.alt = normalizeText(candidate.querySelector('figcaption')?.textContent);
          const posterNodes = addImage(posterImage, candidate.querySelector('figcaption'), null);
          if (posterNodes) replacements.push(...posterNodes);
        }
        replacements.push(linkedMediaParagraph(candidate));
        candidate.replaceWith(...replacements);
        continue;
      }

      const images = [...candidate.querySelectorAll('img[src]')];
      if (images.length) {
        const caption = candidate.querySelector(':scope > figcaption');
        const groupId = candidate.matches('.content-gallery')
          ? candidate.id || `gallery-${mediaIndex + 1}`
          : null;
        const replacements = [];
        images.forEach((image, index) => {
          const nodes = addImage(image, index === 0 ? caption : null, groupId);
          if (nodes) replacements.push(...nodes);
        });
        candidate.replaceWith(...replacements);
        continue;
      }

      const embedded = candidate.querySelector('.responsive-embed, iframe[src], video');
      if (embedded) candidate.replaceWith(linkedMediaParagraph(candidate));
      else candidate.replaceWith(...candidate.childNodes);
      continue;
    }

    if (candidate.matches('.responsive-embed')) {
      candidate.replaceWith(linkedMediaParagraph(candidate));
      continue;
    }

    const nodes = addImage(candidate, null, null);
    if (nodes) candidate.replaceWith(...nodes);
  }

  body.querySelectorAll('aside.notice').forEach(notice => {
    const quote = document.createElement('blockquote');
    quote.append(...notice.childNodes);
    notice.replaceWith(quote);
  });
  // LinkedIn has no inline-code mark: wrap inline code in straight single quotes.
  // Runs BEFORE the table conversion so table cells get quoted identifiers too.
  body.querySelectorAll('code').forEach(code => {
    if (code.closest('pre')) return;
    code.replaceWith(document.createTextNode(`'${code.textContent}'`));
  });

  // LinkedIn has no tables. Replace each one with a marker and record its cells;
  // Step 2b rewrites it as a natural-prose bulleted list (applyTableRewrites).
  const tables = [];
  body.querySelectorAll('table').forEach((table, index) => {
    const id = `LI_TABLE_${String(index + 1).padStart(3, '0')}`;
    const marker = `[[${id}]]`;
    const rows = [...table.querySelectorAll('tr')]
      .map(row => [...row.querySelectorAll('th, td')].map(cell => normalizeText(cell.textContent)))
      .filter(cells => cells.length);
    const hasHeader = !!table.querySelector('thead th') || !!rows.length && !!table.querySelector('tr')?.querySelector('th');
    let top = table;
    while (top.parentElement && top.parentElement !== body) top = top.parentElement;
    const tableLinks = [...table.querySelectorAll('a[href]')].map(link => absoluteUrl(link.getAttribute('href')));
    tables.push({
      id,
      marker,
      headers: hasHeader ? rows[0] : [],
      rows: hasHeader ? rows.slice(1) : rows,
      leadIn: normalizeText(top.previousElementSibling?.textContent),
      links: tableLinks
    });
    top.replaceWith(markerParagraph(marker));
  });
  body.querySelectorAll('h1').forEach(heading => {
    const replacement = document.createElement('h2');
    replacement.append(...heading.childNodes);
    heading.replaceWith(replacement);
  });
  body.querySelectorAll('h4, h5, h6').forEach(heading => {
    const replacement = document.createElement('h3');
    replacement.append(...heading.childNodes);
    heading.replaceWith(replacement);
  });
  body.querySelectorAll('span[style]').forEach(span => {
    const style = span.getAttribute('style') || '';
    const isBold = /font-weight\s*:\s*(bold|[6-9]00)/i.test(style);
    const isItalic = /font-style\s*:\s*italic/i.test(style);
    const replacement = document.createElement(isBold ? 'strong' : isItalic ? 'em' : 'span');
    replacement.append(...span.childNodes);
    span.replaceWith(replacement);
  });
  body.querySelectorAll('a[href]').forEach(link => {
    link.href = absoluteUrl(link.getAttribute('href'));
  });
  body.querySelectorAll('script, style, svg, noscript, form, button').forEach(element => element.remove());

  const allowedTags = new Set([
    'P', 'H2', 'H3', 'STRONG', 'EM', 'A', 'UL', 'OL', 'LI',
    'BLOCKQUOTE', 'PRE', 'CODE', 'BR'
  ]);
  [...body.querySelectorAll('*')].reverse().forEach(element => {
    if (!allowedTags.has(element.tagName)) {
      element.replaceWith(...element.childNodes);
      return;
    }
    [...element.attributes].forEach(attribute => {
      if (!(element.tagName === 'A' && attribute.name === 'href')) {
        element.removeAttribute(attribute.name);
      }
    });
  });
  body.querySelectorAll('p').forEach(paragraph => {
    if (!normalizeText(paragraph.textContent) && !paragraph.querySelector('br')) paragraph.remove();
  });

  const attribution = document.createElement('p');
  const emphasis = document.createElement('em');
  const attributionLink = document.createElement('a');
  const attributionPrefix = language.startsWith('es')
    ? hadRepublishedNotice
      ? 'Esta versión se publicó en '
      : 'Publicado originalmente en '
    : hadRepublishedNotice
      ? 'This version was published on '
      : 'Originally published on ';
  attributionLink.href = canonicalUrl;
  attributionLink.textContent = 'CODERTECTURA';
  emphasis.append(
    document.createTextNode(attributionPrefix),
    attributionLink,
    document.createTextNode('.')
  );
  attribution.append(emphasis);
  body.append(attribution);

  const headerBackground = document.querySelector('.post__header-bg');
  const backgroundImage = headerBackground ? getComputedStyle(headerBackground).backgroundImage : '';
  const backgroundMatch = backgroundImage.match(/^url\(["']?(.*?)["']?\)$/);
  const openGraphImage = document.querySelector('meta[property="og:image"]')?.content || '';
  const twitterImage = document.querySelector('meta[name="twitter:image"]')?.content || '';
  let coverSource = backgroundMatch?.[1]
    ? 'computed-background'
    : openGraphImage
      ? 'meta[property="og:image"]'
      : twitterImage
        ? 'meta[name="twitter:image"]'
        : '';
  let coverUrl = absoluteUrl(backgroundMatch?.[1] || openGraphImage || twitterImage || '');
  if (!coverUrl && media.length) {
    coverUrl = media[0].url;
    coverSource = 'first-body-image';
  }
  const coverPathName = coverUrl
    ? decodeURIComponent(new URL(coverUrl).pathname.split('/').pop() || 'cover.png')
    : '';
  const coverFileName = coverPathName
    ? `li-cover-${coverPathName.replace(/[^a-zA-Z0-9._-]+/g, '-')}`
    : '';
  const bodyHtml = `<p></p>${body.innerHTML}`;
  const markerMatches = bodyHtml.match(/\[\[LI_MEDIA_\d{3}\]\]/g) || [];

  return {
    canonicalUrl,
    canonicalSource,
    language,
    title: normalizeText(titleElement.textContent),
    bodyHtml,
    coverUrl,
    coverFileName,
    coverSource,
    hadRepublishedNotice,
    attributionHtml: attribution.outerHTML,
    sourceSnapshot,
    media,
    tables,
    // Every href that SHOULD be a link, in order. Anything else in the editor is a LinkedIn auto-link.
    // Table links are appended so a rewrite that keeps them as <a> passes the audit.
    expectedLinks: [
      ...[...body.querySelectorAll('a[href]')].map(link => link.href),
      ...tables.flatMap(table => table.links)
    ],
    expected: {
      headings: body.querySelectorAll('h2, h3').length,
      // Each table becomes one <ul> in Step 2b.
      lists: body.querySelectorAll('ul, ol').length + tables.length,
      blockquotes: body.querySelectorAll('blockquote').length,
      codeBlocks: body.querySelectorAll('pre').length,
      links: body.querySelectorAll('a[href]').length,
      media: media.length,
      markers: markerMatches.length,
      tables: tables.length
    }
  };
}

window.__linkedinArticleManifest = extractCodertecturaArticle();
localStorage.setItem('__liManifest', JSON.stringify(window.__linkedinArticleManifest));
// Return a SUMMARY only — never bodyHtml (output filter + context size).
(m => ({
  title: m.title,
  canonicalUrl: m.canonicalUrl,
  canonicalSource: m.canonicalSource,
  language: m.language,
  coverSource: m.coverSource,
  coverFileName: m.coverFileName,
  sourceSnapshot: m.sourceSnapshot,
  expected: m.expected,
  bodyLength: m.bodyHtml.length,
  tables: m.tables,
  media: m.media.map(({ id, marker, fileName, captionText, alt }) => ({ id, marker, fileName, captionText, alt }))
}))(window.__linkedinArticleManifest);
```

Do not navigate away until the table rewrite (if any) and source preflight pass. The returned `tables[].rows` may contain dotted identifiers that the output filter blocks. If a cell shows `[BLOCKED: …]`, read that cell again with `.replace(/\./g, '·')`.

## Rewrite tables (Step 2b)

Run this on the canonical CODERTECTURA page after writing the replacement HTML yourself (see SKILL.md Step 2b for the style rules). Pass one entry per table:

- `html`: a single `<ul>` with one `<li>` per row. Plain text and `<a>`, `<strong>`, or `<em>` only. Identifiers go in straight single quotes.
- `leadInFrom` / `leadInTo` (optional): the exact text of the preceding paragraph and its replacement, used when that sentence mentions "tabla".

```js
function applyTableRewrites(rewrites) {
  const manifest = JSON.parse(localStorage.getItem('__liManifest'));
  const escapeText = text => { const div = document.createElement('div'); div.textContent = text; return div.innerHTML; };
  let html = manifest.bodyHtml;
  const report = [];
  for (const table of manifest.tables) {
    const rewrite = rewrites[table.id];
    if (!rewrite) throw new Error(`No rewrite for ${table.id}.`);
    if (!/^<ul>[\s\S]*<\/ul>$/.test(rewrite.html.trim())) throw new Error(`${table.id}: html must be one <ul>.`);
    const items = (rewrite.html.match(/<li>/g) || []).length;
    if (items !== table.rows.length) throw new Error(`${table.id}: ${items} items for ${table.rows.length} rows.`);
    if (/\s\|\s/.test(rewrite.html)) throw new Error(`${table.id}: pipe residue in rewrite.`);
    const markerParagraph = `<p>${table.marker}</p>`;
    if (html.split(markerParagraph).length !== 2) throw new Error(`${table.id}: marker paragraph not found exactly once.`);
    html = html.replace(markerParagraph, rewrite.html.replace(/\n\s*/g, ''));
    if (rewrite.leadInFrom) {
      const from = `<p>${escapeText(rewrite.leadInFrom)}</p>`;
      if (html.split(from).length !== 2) throw new Error(`${table.id}: lead-in paragraph not found exactly once.`);
      html = html.replace(from, `<p>${escapeText(rewrite.leadInTo)}</p>`);
    }
    report.push({ id: table.id, items });
  }
  manifest.bodyHtml = html;
  manifest.tablesRewritten = true;
  localStorage.setItem('__liManifest', JSON.stringify(manifest));
  window.__linkedinArticleManifest = manifest;
  return { report, markersLeft: (html.match(/\[\[LI_TABLE_\d{3}\]\]/g) || []).length, bodyLength: html.length };
}

applyTableRewrites({
  LI_TABLE_001: {
    html: `<ul><li>…</li><li>…</li></ul>`,
    leadInFrom: 'Si tuviera que resumir la diferencia en una tabla, sería esta:',
    leadInTo: 'Si tuviera que resumir la diferencia, me quedaría con esto:'
  }
});
```

Reference rewrite from a real run (a "Portal frente a OpenTelemetry" table with 8 rows: where the data lives, granularity, identity, content, latency, surfaces, access/retention, question answered):

```html
<ul>
<li>Los datos del portal viven en GitHub (dashboards, API, NDJSON) y es GitHub quien gobierna su ciclo de vida, con un máximo de 28 días. Con la telemetría OTel y 'capture.identity', acaban en tu colector OTLP y en tu backend de observabilidad, y el ciclo de vida lo gobiernas tú.</li>
<li>El portal trabaja con agregados diarios y de 28 días por empresa, organización, repositorio y usuario. OTel baja al detalle: trazas, métricas y eventos por sesión, paso a paso, durante el tiempo que tu organización decida conservarlos.</li>
<li>Para identificar a la persona, el portal se queda en el login de GitHub y 'last_activity_at'. OTel te da 'user.name', 'process.user.name' y 'host.name', además del pseudónimo (el login de GitHub).</li>
<li>El contenido no lo captura nunca el portal. En OTel viene apagado por defecto, con cinco clases que puedes activar por separado.</li>
<li>En latencia, el portal puede tardar hasta dos o tres días (UTC). Con OTel, lo que tarde tu pipeline.</li>
<li>El portal cubre los IDE soportados, Copilot CLI y los agentes, pero deja fuera Copilot Chat en GitHub.com y GitHub Mobile. OTel llega a Copilot CLI, la app de GitHub Copilot y VS Code, con cobertura parcial según el harness.</li>
<li>El acceso y la retención los decide GitHub en el portal, más los roles que tú asignes. En OTel los decides tú (y, por tanto, también son tu responsabilidad).</li>
<li>Y, sobre todo, responden a preguntas distintas. El portal: ¿se está adoptando?, ¿compensa?, ¿quién no usa su licencia? OTel: ¿qué pasó exactamente, quién lo hizo y desde dónde?</li>
</ul>
```

Note how the quoted identifiers in that list (`'user.name'`, `'host.name'`, `'process.user.name'`) and `GitHub.com` are exactly what LinkedIn auto-links on paste. Plan on Step 4b for them.

## Run source preflight

This check fails before LinkedIn is modified. It verifies the extraction invariants and downloads each unique image once to validate its response and MIME type.

```js
async function preflightCodertecturaArticle(manifest) {
  const failures = [];
  const canonicalOrigin = new URL(manifest.canonicalUrl).origin;
  const markers = manifest.bodyHtml.match(/\[\[LI_MEDIA_\d{3}\]\]/g) || [];
  const uniqueIdentity = new Set(manifest.media.flatMap(item => [item.id, item.marker, item.fileName]));

  if (!manifest.title) failures.push('title is empty');
  if (!manifest.bodyHtml.trim()) failures.push('bodyHtml is empty');
  if (!/^https?:/.test(manifest.canonicalUrl)) failures.push('canonical URL is not HTTP(S)');
  if (!['link[rel="canonical"]', 'location.href'].includes(manifest.canonicalSource)) {
    failures.push('canonical source is unknown');
  }
  if (!!manifest.coverUrl !== !!manifest.coverSource) {
    failures.push('cover URL and source are inconsistent');
  }
  if (manifest.sourceSnapshot?.selector !== 'article.post .post__content') {
    failures.push('source snapshot has the wrong body selector');
  }
  if (!manifest.sourceSnapshot?.directChildren) failures.push('source body has no direct children');
  if (markers.length !== manifest.media.length) failures.push('marker count does not equal media count');
  if (uniqueIdentity.size !== manifest.media.length * 3) failures.push('media identities are not unique');
  if (/<h[23]>\s*Comentarios\s*<\/h[23]>|Este sitio utiliza cookies propias|aria-label="Compartir artículo"/i.test(manifest.bodyHtml)) {
    failures.push('site chrome leaked into bodyHtml');
  }
  if (/\[\[LI_TABLE_\d{3}\]\]/.test(manifest.bodyHtml)) failures.push('table markers remain: run applyTableRewrites first');
  const parsed = document.createElement('div');
  parsed.innerHTML = manifest.bodyHtml;
  if ([...parsed.querySelectorAll('code')].some(code => !code.closest('pre'))) failures.push('inline <code> remains outside <pre>');
  if (/[‘’]/.test(parsed.textContent)) failures.push('typographic single quotes present');
  // Domain-looking tokens outside links: LinkedIn auto-links them on paste (Step 4b).
  const autolinkRisk = [];
  const walker = document.createTreeWalker(parsed, NodeFilter.SHOW_TEXT);
  let textNode;
  while ((textNode = walker.nextNode())) {
    if (textNode.parentElement.closest('a, pre')) continue;
    const found = textNode.nodeValue.match(/\b[\w-]+(?:\.[\w-]+)*\.(?:com|net|org|io|dev|app|ai|name|info|co|me|tech|cloud|es|us|uk|ly|sh)\b/gi) || [];
    autolinkRisk.push(...found);
  }

  const resources = [
    ...(manifest.coverUrl ? [{ kind: 'cover', url: manifest.coverUrl }] : []),
    ...manifest.media.map(item => ({ kind: item.id, url: item.url }))
  ];
  const uniqueResources = [...new Map(resources.map(item => [item.url, item])).values()];
  const results = await Promise.all(uniqueResources.map(async resource => {
    try {
      const url = new URL(resource.url);
      if (url.origin !== canonicalOrigin) {
        return { ...resource, ok: false, reason: 'cross-origin image' };
      }
      const response = await fetch(url.href, { credentials: 'same-origin' });
      const type = response.headers.get('content-type') || '';
      return { ...resource, ok: response.ok && type.startsWith('image/'), status: response.status, type };
    } catch (error) {
      return { ...resource, ok: false, reason: error.message };
    }
  }));
  results.filter(result => !result.ok).forEach(result => {
    failures.push(`${result.kind}: ${result.url} failed image preflight`);
  });

  return {
    ok: failures.length === 0,
    failures,
    // Dots replaced so the tool output filter does not block dotted identifiers.
    autolinkRisk: [...new Set(autolinkRisk)].map(token => token.replace(/\./g, '·')),
    summary: {
      title: manifest.title,
      canonicalSource: manifest.canonicalSource,
      coverSource: manifest.coverSource,
      source: manifest.sourceSnapshot,
      cover: !!manifest.coverUrl,
      ...manifest.expected
    },
    resources: results
  };
}

await preflightCodertecturaArticle(window.__linkedinArticleManifest);
```

## One-trip bundle: body + images + cover (Step 4)

Run `prepareBundle()` on the canonical CODERTECTURA page. It reads the manifest from `localStorage` and adds body images in manifest order, then the cover, while the encoded payload stays under 1.2 MB. It returns names only, never data.

```js
async function encodeImageForTransfer(url) {
  const toDataUrl = blob => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(blob);
  });
  const canvasDataUrl = async (blob, maxDimension, quality) => {
    const bitmap = await createImageBitmap(blob);
    const scale = Math.min(1, maxDimension / Math.max(bitmap.width, bitmap.height));
    const canvas = document.createElement('canvas');
    canvas.width = Math.max(1, Math.round(bitmap.width * scale));
    canvas.height = Math.max(1, Math.round(bitmap.height * scale));
    const context = canvas.getContext('2d');
    context.fillStyle = '#ffffff';
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    bitmap.close();
    return canvas.toDataURL('image/jpeg', quality);
  };
  const response = await fetch(url, { credentials: 'same-origin' });
  if (!response.ok) throw new Error(`${url} returned HTTP ${response.status}.`);
  const blob = await response.blob();
  if (!blob.type.startsWith('image/')) throw new Error(`${url} is not an image.`);
  if (blob.size <= 300000) return { durl: await toDataUrl(blob), originalBytes: blob.size };
  let durl = '';
  for (const [maxDimension, quality] of [[2400, 0.9], [2000, 0.84], [1600, 0.78]]) {
    durl = await canvasDataUrl(blob, maxDimension, quality);
    if (durl.length <= 500000) break;
  }
  return { durl, originalBytes: blob.size };
}

// 1,180,000 leaves room for the lite manifest added after the loop (well under 1.2 MB total).
async function prepareBundle(maxHashLength = 1180000) {
  const manifest = JSON.parse(localStorage.getItem('__liManifest'));
  if (/\[\[LI_TABLE_\d{3}\]\]/.test(manifest.bodyHtml)) throw new Error('Run applyTableRewrites first.');
  const items = [
    ...manifest.media.map(item => ({ fileName: item.fileName, url: item.url })),
    ...(manifest.coverUrl ? [{ fileName: manifest.coverFileName, url: manifest.coverUrl, cover: true }] : [])
  ];
  const images = [];
  const skipped = [];
  for (const item of items) {
    const encoded = await encodeImageForTransfer(item.url);
    const candidate = { bodyHtml: manifest.bodyHtml, images: [...images, { fileName: item.fileName, durl: encoded.durl }] };
    if (encodeURIComponent(JSON.stringify(candidate)).length > maxHashLength) {
      skipped.push(item.fileName);
      // Keep body images in order: once one body image does not fit, the rest go in later trips.
      if (!item.cover) break;
      continue;
    }
    images.push({ fileName: item.fileName, durl: encoded.durl });
  }
  // A lite manifest travels with the bundle so the LinkedIn page can audit and find auto-links.
  const lite = {
    title: manifest.title,
    canonicalUrl: manifest.canonicalUrl,
    coverUrl: manifest.coverUrl,
    coverFileName: manifest.coverFileName,
    expected: manifest.expected,
    expectedLinks: manifest.expectedLinks,
    media: manifest.media.map(({ id, marker, fileName, captionText }) => ({ id, marker, fileName, captionText }))
  };
  window.__bundle = { bodyHtml: manifest.bodyHtml, images, manifest: lite };
  const included = images.map(image => image.fileName);
  return {
    included,
    remaining: items.map(item => item.fileName).filter(name => !included.includes(name)),
    encodedLength: encodeURIComponent(JSON.stringify(window.__bundle)).length
  };
}

await prepareBundle();
```

Navigate with the bundle (same tab). Then wait OUTSIDE the browser tool for about 8 s.

```js
function navigateBundle(editorUrl) {
  if (!window.__bundle) throw new Error('Run prepareBundle first.');
  const target = new URL(editorUrl);
  target.hash = 'CLAUDEBUNDLE=' + encodeURIComponent(JSON.stringify(window.__bundle));
  const hashLength = target.hash.length;
  setTimeout(() => location.assign(target.href), 300);
  return { hashLength };
}

navigateBundle('https://www.linkedin.com/article/edit/<id>/');
```

The FIRST JavaScript call on LinkedIn after that navigation must be this one. It hydrates the files, strips the hash, and pastes the body.

```js
(function hydrateBundleAndPaste() {
  const navigationUrl = performance.getEntriesByType('navigation')[0]?.name || location.href;
  const source = location.hash.includes('CLAUDEBUNDLE=') ? location.href : navigationUrl;
  const url = new URL(source);
  const match = url.hash.match(/CLAUDEBUNDLE=(.+)$/);
  if (!match) {
    history.replaceState(null, '', location.pathname + location.search);
    return { error: 'bundle not found' };
  }
  const bundle = JSON.parse(decodeURIComponent(match[1]));
  history.replaceState(null, '', url.pathname + url.search);
  // Lite manifest for auditLinkedInDraft / findUnexpectedLinks on this page.
  window.__liManifest = bundle.manifest;
  try { sessionStorage.setItem('__liManifest', JSON.stringify(bundle.manifest)); } catch {}

  window.__files = {};
  for (const item of bundle.images) {
    const [header, base64] = item.durl.split(',');
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index);
    const type = header.match(/data:([^;]+)/)?.[1] || 'application/octet-stream';
    window.__files[item.fileName] = new File([bytes], item.fileName, { type });
  }

  const editor = document.querySelector('div.ProseMirror[contenteditable="true"]');
  if (!editor) return { error: 'editor not found', files: Object.keys(window.__files), hashRemoved: !location.hash };
  if (editor.textContent.trim()) return { error: 'editor not empty — not pasting', files: Object.keys(window.__files), hashRemoved: !location.hash };
  if (!bundle.bodyHtml.startsWith('<p></p>')) return { error: 'bodyHtml must start with <p></p>' };

  editor.focus();
  const selection = window.getSelection();
  const range = document.createRange();
  range.selectNodeContents(editor);
  range.collapse(false);
  selection.removeAllRanges();
  selection.addRange(range);
  const transfer = new DataTransfer();
  transfer.setData('text/html', bundle.bodyHtml);
  editor.dispatchEvent(new ClipboardEvent('paste', { clipboardData: transfer, bubbles: true, cancelable: true }));
  return {
    files: Object.keys(window.__files),
    hashRemoved: !location.hash,
    characters: editor.textContent.length,
    blocks: editor.children.length
  };
})();
```

`window.__files` lives only in this page instance. A reload or navigation of the editor drops it, so re-hydrate before placing any image that is not yet in the article.

## Paste HTML (body text, formatting preserved)

```js
function pasteArticleHtml(html) {
  const editor = document.querySelector('div.ProseMirror[contenteditable="true"]');
  if (!editor) throw new Error('LinkedIn ProseMirror editor was not found.');
  if (editor.textContent.trim()) throw new Error('Refusing to paste into a non-empty draft.');
  if (!html.startsWith('<p></p>')) throw new Error('Article HTML must start with <p></p>.');

  editor.focus();
  const selection = window.getSelection();
  const range = document.createRange();
  range.selectNodeContents(editor);
  range.collapse(false);
  selection.removeAllRanges();
  selection.addRange(range);

  const transfer = new DataTransfer();
  transfer.setData('text/html', html);
  editor.dispatchEvent(new ClipboardEvent('paste', {
    clipboardData: transfer,
    bubbles: true,
    cancelable: true
  }));
  return { characters: editor.textContent.length, htmlCharacters: editor.innerHTML.length };
}

pasteArticleHtml(manifest.bodyHtml);
```

Supported HTML is `<p>`, `<h2>`, `<h3>`, `<strong>`, `<em>`, `<a>`, `<ul>`, `<ol>`, `<li>`, `<blockquote>`, `<pre>`, `<code>`, and `<br>`. Remote `img` elements are intentionally absent.

## Setting the selection programmatically (before a targeted paste)

ProseMirror ignores DOM selection changes made synchronously before a dispatched event. Always:

```js
sel.removeAllRanges();sel.addRange(range);
document.dispatchEvent(new Event('selectionchange'));
await new Promise(r=>setTimeout(r,500));   // let PM sync
// ...now dispatch the paste
```

## Fix a demoted heading

Use this only when the text audit shows one heading merged into the preceding paragraph. The heading text must be unique.

```js
async function repairDemotedHeading(headingText) {
  const editor = document.querySelector('div.ProseMirror[contenteditable="true"]');
  const walker = document.createTreeWalker(editor, NodeFilter.SHOW_TEXT);
  const matches = [];
  let node;
  while ((node = walker.nextNode())) {
    const index = node.nodeValue.indexOf(headingText);
    if (index >= 0) matches.push({ node, index });
  }
  if (matches.length !== 1) {
    throw new Error(`Expected one heading text match, found ${matches.length}.`);
  }

  const match = matches[0];
  const range = document.createRange();
  range.setStart(match.node, match.index);
  range.setEnd(match.node, match.index + headingText.length);
  const selection = window.getSelection();
  selection.removeAllRanges();
  selection.addRange(range);
  document.dispatchEvent(new Event('selectionchange'));
  await new Promise(resolve => setTimeout(resolve, 500));

  const escapedHeading = document.createElement('div');
  escapedHeading.textContent = headingText;
  const transfer = new DataTransfer();
  transfer.setData('text/html', `<p></p><h3>${escapedHeading.innerHTML}</h3><p></p>`);
  editor.dispatchEvent(new ClipboardEvent('paste', {
    clipboardData: transfer,
    bubbles: true,
    cancelable: true
  }));
  return editor.querySelectorAll('h2, h3').length;
}
```

If the repair leaves a final empty paragraph, select it with the computer tool and press Backspace once.

## Structural audit

```js
function getLinkedInArticleTitle(editor) {
  const candidates = [...document.querySelectorAll('textarea, input, [contenteditable="true"]')]
    .filter(element => element !== editor)
    .map(element => {
      const hint = [
        element.getAttribute('placeholder'),
        element.getAttribute('aria-label'),
        element.getAttribute('data-placeholder')
      ].filter(Boolean).join(' ');
      const value = 'value' in element ? element.value : element.textContent;
      return { hint, value: (value || '').trim() };
    });
  return candidates.find(item => /title|título/i.test(item.hint))?.value || '';
}

function auditLinkedInDraft(manifest, options = {}) {
  const { requireMedia = false, requireSaved = false } = options;
  const editor = document.querySelector('div.ProseMirror[contenteditable="true"]');
  if (!editor) throw new Error('LinkedIn ProseMirror editor was not found.');

  const observedCaptions = [...editor.querySelectorAll('figure figcaption textarea')]
    .map(textarea => textarea.value.replace(/\s+/g, ' ').trim());
  const expectedCaptions = manifest.media.map(item => item.captionText || '');
  // Top-level blocks only: list items wrap a <p>, and LinkedIn keeps one empty
  // paragraph after each figure on purpose (see SKILL.md Step 6).
  const isFigureBlock = block => block?.tagName === 'FIGURE' || !!block?.querySelector?.('figure');
  const emptyParagraphs = [...editor.children]
    .filter(block => block.tagName === 'P' && !block.textContent.trim());
  const unexpectedEmptyParagraphs = emptyParagraphs
    .filter(paragraph => paragraph !== editor.lastElementChild && !isFigureBlock(paragraph.previousElementSibling));
  const markers = editor.textContent.match(/\[\[LI_(MEDIA|TABLE)_\d{3}\]\]/g) || [];
  const anchors = [...editor.querySelectorAll('a[href]')];
  // Count link RUNS: after a reload LinkedIn splits one link into adjacent <a> elements
  // around <em>/<strong>. Same href + nothing but whitespace between them = one link.
  const links = anchors.filter((anchor, index) => {
    const previous = anchors[index - 1];
    if (!previous || previous.href !== anchor.href) return true;
    const between = document.createRange();
    between.setStartAfter(previous);
    between.setEndBefore(anchor);
    return between.toString().trim() !== '';
  });
  const expectedHrefs = new Set((manifest.expectedLinks || []).map(href => new URL(href).href));
  const unexpectedLinks = manifest.expectedLinks
    ? anchors.filter(anchor => !expectedHrefs.has(anchor.href)).map(anchor => anchor.textContent.replace(/\./g, '·'))
    : [];
  const textOutsideCode = [...editor.children].filter(block => block.tagName !== 'PRE').map(block => block.textContent).join('\n');
  const attributionPresent = links.some(link => {
    try {
      return link.textContent.trim() === 'CODERTECTURA' &&
        new URL(link.href).href === new URL(manifest.canonicalUrl).href;
    } catch {
      return false;
    }
  });
  const saveText = document.body.innerText.match(
    /Draft\s*[-–·]\s*saved|Borrador\s*[-–·]\s*guardado/i
  )?.[0] || '';
  const observed = {
    title: getLinkedInArticleTitle(editor),
    headings: editor.querySelectorAll('h2, h3').length,
    lists: editor.querySelectorAll('ul, ol').length,
    blockquotes: editor.querySelectorAll('blockquote').length,
    codeBlocks: editor.querySelectorAll('pre').length,
    links: links.length,
    figures: editor.querySelectorAll('figure').length,
    captions: observedCaptions,
    markers,
    attributionPresent,
    cover: !!document.querySelector('[class*="cover-media"] img, [class*="coverMedia"] img'),
    unexpectedEmptyParagraphs: unexpectedEmptyParagraphs.length,
    unexpectedLinks,
    tableResidue: (textOutsideCode.match(/\s\|\s/g) || []).length,
    typographicQuotes: /[‘’]/.test(textOutsideCode),
    saveText
  };
  const failures = [];
  if (observed.unexpectedLinks.length) failures.push('unexpectedLinks');
  if (observed.tableResidue) failures.push('tableResidue');
  if (observed.typographicQuotes) failures.push('typographicQuotes');

  if (observed.title !== manifest.title) failures.push('title');
  if (observed.headings !== manifest.expected.headings) failures.push('headings');
  if (observed.lists !== manifest.expected.lists) failures.push('lists');
  if (observed.blockquotes !== manifest.expected.blockquotes) failures.push('blockquotes');
  if (observed.codeBlocks !== manifest.expected.codeBlocks) failures.push('codeBlocks');
  if (observed.links !== manifest.expected.links) failures.push('links');
  if (!observed.attributionPresent) failures.push('attribution');
  if (observed.unexpectedEmptyParagraphs) failures.push('emptyParagraphs');

  if (requireMedia) {
    if (observed.figures !== manifest.expected.media) failures.push('figures');
    if (JSON.stringify(observed.captions) !== JSON.stringify(expectedCaptions)) failures.push('captions');
    if (observed.markers.length) failures.push('markers');
    if (observed.cover !== !!manifest.coverUrl) failures.push('cover');
  }
  if (requireSaved && !observed.saveText) failures.push('savedState');
  return { ok: failures.length === 0, failures, observed, expected: manifest.expected };
}

auditLinkedInDraft(manifest);
```

Run `auditLinkedInDraft(manifest)` after the text paste. Run `auditLinkedInDraft(manifest, { requireMedia: true, requireSaved: true })` before opening the publish dialog.

## Prepare the next image payload

Run this on the canonical CODERTECTURA page. Pass only the body media that remain to be uploaded, in manifest order. The function automatically fills one hash payload without crossing 1.2 MB.

```js
async function prepareNextImagePayload(imageItems, maxHashLength = 1200000) {
  const toDataUrl = blob => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(blob);
  });
  const canvasDataUrl = async (blob, maxDimension, quality) => {
    const bitmap = await createImageBitmap(blob);
    const scale = Math.min(1, maxDimension / Math.max(bitmap.width, bitmap.height));
    const canvas = document.createElement('canvas');
    canvas.width = Math.max(1, Math.round(bitmap.width * scale));
    canvas.height = Math.max(1, Math.round(bitmap.height * scale));
    const context = canvas.getContext('2d');
    context.fillStyle = '#ffffff';
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    bitmap.close();
    return canvas.toDataURL('image/jpeg', quality);
  };
  const encodeImage = async item => {
    const response = await fetch(item.url, { credentials: 'same-origin' });
    if (!response.ok) throw new Error(`${item.fileName} returned HTTP ${response.status}.`);
    const blob = await response.blob();
    if (!blob.type.startsWith('image/')) throw new Error(`${item.fileName} is not an image.`);
    if (blob.size <= 300000) {
      return { ...item, durl: await toDataUrl(blob), originalBytes: blob.size };
    }

    let durl = '';
    for (const [maxDimension, quality] of [[2400, 0.9], [2000, 0.84], [1600, 0.78]]) {
      durl = await canvasDataUrl(blob, maxDimension, quality);
      if (durl.length <= 500000) break;
    }
    return { ...item, durl, originalBytes: blob.size };
  };

  const payload = [];
  for (const item of imageItems) {
    const encoded = await encodeImage(item);
    const candidate = [...payload, encoded];
    if (encodeURIComponent(JSON.stringify(candidate)).length > maxHashLength) {
      if (!payload.length) throw new Error(`${item.fileName} cannot fit in one transfer payload.`);
      break;
    }
    payload.push(encoded);
  }
  window.__preparedImagePayload = payload;
  return {
    includedNames: payload.map(item => item.fileName),
    remainingNames: imageItems.slice(payload.length).map(item => item.fileName),
    encodedLength: encodeURIComponent(JSON.stringify(payload)).length
  };
}

await prepareNextImagePayload(remainingMedia);
```

For the final cover trip, pass the concrete manifest values. If `coverUrl` is empty, skip this trip.

```js
if (manifest.coverUrl) {
  await prepareNextImagePayload([{
    id: 'LI_COVER',
    kind: 'cover',
    url: manifest.coverUrl,
    fileName: manifest.coverFileName
  }]);
}
```

## Navigate and hydrate the payload

Use the exact saved editor URL. Wait outside the browser tool after navigation so no output echoes the large hash.

```js
function navigatePreparedImagePayload(editorUrl) {
  if (!window.__preparedImagePayload?.length) throw new Error('No prepared payload is available.');
  const target = new URL(editorUrl);
  target.hash = `CLAUDEIMGS=${encodeURIComponent(JSON.stringify(window.__preparedImagePayload))}`;
  const summary = {
    files: window.__preparedImagePayload.map(item => item.fileName),
    encodedLength: target.hash.length
  };
  setTimeout(() => location.assign(target.href), 300);
  return summary;
}

navigatePreparedImagePayload(editorUrl);
```

Hydrate the files immediately after LinkedIn loads and strip the hash in the same call. This MUST be the first JavaScript call after the hash navigation. Do not inspect the tab, read the editor DOM, or run any other browser action first because its response can echo the complete base64 URL and overflow the tab context.

```js
function hydrateTransferredImageFiles() {
  const navigationUrl = performance.getEntriesByType('navigation')[0]?.name || location.href;
  const hashSource = location.hash.includes('CLAUDEIMGS=') ? location.href : navigationUrl;
  const transferUrl = new URL(hashSource);
  const match = transferUrl.hash.match(/CLAUDEIMGS=(.+)$/);
  if (!match) throw new Error('Image-transfer payload was not found.');

  const payload = JSON.parse(decodeURIComponent(match[1]));
  window.__files = {};
  for (const item of payload) {
    const [header, base64] = item.durl.split(',');
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let index = 0; index < binary.length; index += 1) {
      bytes[index] = binary.charCodeAt(index);
    }
    const type = header.match(/data:([^;]+)/)?.[1] || 'application/octet-stream';
    window.__files[item.fileName] = new File([bytes], item.fileName, { type });
  }

  transferUrl.hash = '';
  history.replaceState(null, '', `${transferUrl.pathname}${transferUrl.search}`);
  return { files: Object.keys(window.__files), hashRemoved: !location.hash };
}

hydrateTransferredImageFiles();
```

After inserting the included files, return to the canonical post and rerun extraction plus `prepareNextImagePayload()` for `remainingNames`. This avoids carrying base64 data through tool output.

## Insert a content image at its marker

```js
async function insertImageAtMarker(marker, fileName, captionText = '') {
  const editor = document.querySelector('div.ProseMirror[contenteditable="true"]');
  const file = window.__files?.[fileName];
  if (!editor) throw new Error('LinkedIn ProseMirror editor was not found.');
  if (!file) throw new Error(`${fileName} is not hydrated.`);

  const walker = document.createTreeWalker(editor, NodeFilter.SHOW_TEXT);
  const matches = [];
  let node;
  while ((node = walker.nextNode())) {
    const index = node.nodeValue.indexOf(marker);
    if (index >= 0) matches.push({ node, index });
  }
  if (matches.length !== 1) throw new Error(`Expected one ${marker} match, found ${matches.length}.`);

  const beforeFigures = [...editor.querySelectorAll('figure')];
  const match = matches[0];
  let markerBlock = match.node.parentElement;
  while (markerBlock?.parentElement && markerBlock.parentElement !== editor) {
    markerBlock = markerBlock.parentElement;
  }
  if (!markerBlock || markerBlock.parentElement !== editor) {
    throw new Error(`${marker} is not inside a top-level editor block.`);
  }

  window.__linkedinImageInsertions ??= {};
  const insertionState = {
    marker,
    fileName,
    captionText,
    beforeFigures,
    beforeFigureCount: beforeFigures.length,
    markerBlock,
    previousBlock: markerBlock.previousElementSibling,
    nextBlock: markerBlock.nextElementSibling,
    targetIndex: [...editor.children].indexOf(markerBlock),
    status: 'targeted'
  };
  window.__linkedinImageInsertions[marker] = insertionState;

  const range = document.createRange();
  range.setStart(match.node, match.index);
  range.setEnd(match.node, match.index + marker.length);
  const selection = window.getSelection();
  selection.removeAllRanges();
  selection.addRange(range);
  document.dispatchEvent(new Event('selectionchange'));
  await new Promise(resolve => setTimeout(resolve, 600));

  const transfer = new DataTransfer();
  transfer.items.add(file);
  editor.dispatchEvent(new ClipboardEvent('paste', {
    clipboardData: transfer,
    bubbles: true,
    cancelable: true
  }));
  insertionState.status = 'paste-dispatched';

  const deadline = Date.now() + 12000;
  let insertedFigure = null;
  while (Date.now() < deadline) {
    insertedFigure = [...editor.querySelectorAll('figure')]
      .find(figure => !beforeFigures.includes(figure));
    if (insertedFigure && !editor.textContent.includes(marker)) break;
    await new Promise(resolve => setTimeout(resolve, 300));
  }
  if (!insertedFigure) {
    insertionState.status = 'figure-not-observed';
    throw new Error(`${fileName} did not create a figure.`);
  }
  insertionState.insertedFigure = insertedFigure;
  insertionState.status = 'figure-created';
  if (editor.textContent.includes(marker)) {
    insertionState.status = 'marker-remained';
    throw new Error(`${marker} was not removed.`);
  }

  const caption = insertedFigure.querySelector('figcaption textarea');
  if (caption && captionText) {
    const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
    caption.focus();
    setter.call(caption, captionText);
    caption.dispatchEvent(new Event('input', { bubbles: true }));
    caption.blur();
  }
  insertionState.status = 'complete';
  return {
    figures: editor.querySelectorAll('figure').length,
    markerRemoved: !editor.textContent.includes(marker),
    caption: caption?.value || ''
  };
}

await insertImageAtMarker(mediaItem.marker, mediaItem.fileName, mediaItem.captionText);
```

Verify the figure count, marker removal, and caption before inserting the next image. Retry once after re-querying the editor DOM.

If the browser tool or CDP call times out, do not call `insertImageAtMarker()` again immediately. The paste can finish in the page after the tool stops waiting. Wait outside the browser tool for the upload to settle, then run this recovery in a new JavaScript call:

```js
function recoverTimedOutImageInsertion(marker) {
  const editor = document.querySelector('div.ProseMirror[contenteditable="true"]');
  const state = window.__linkedinImageInsertions?.[marker];
  if (!editor) throw new Error('LinkedIn ProseMirror editor was not found.');
  if (!state) throw new Error(`No insertion state was recorded for ${marker}.`);

  const currentFigures = [...editor.querySelectorAll('figure')];
  const createdFigures = currentFigures.filter(figure => !state.beforeFigures.includes(figure));
  const insertedFigure = state.insertedFigure?.isConnected
    ? state.insertedFigure
    : createdFigures.length === 1
      ? createdFigures[0]
      : null;

  const walker = document.createTreeWalker(editor, NodeFilter.SHOW_TEXT);
  const markerMatches = [];
  let node;
  while ((node = walker.nextNode())) {
    if (node.nodeValue.includes(marker)) markerMatches.push(node);
  }

  if (!insertedFigure) {
    return {
      outcome: 'not-created',
      figuresBefore: state.beforeFigureCount,
      figuresNow: currentFigures.length,
      markerMatches: markerMatches.length,
      safeToRetry: currentFigures.length === state.beforeFigureCount && markerMatches.length === 1
    };
  }
  if (createdFigures.length > 1 && !state.insertedFigure?.isConnected) {
    throw new Error(`Cannot identify one new figure for ${marker}.`);
  }

  let figureBlock = insertedFigure;
  while (figureBlock.parentElement && figureBlock.parentElement !== editor) {
    figureBlock = figureBlock.parentElement;
  }
  if (figureBlock.parentElement !== editor) {
    throw new Error(`The new figure for ${marker} is not inside a top-level editor block.`);
  }

  let liveMarkerBlock = markerMatches[0]?.parentElement || null;
  while (liveMarkerBlock?.parentElement && liveMarkerBlock.parentElement !== editor) {
    liveMarkerBlock = liveMarkerBlock.parentElement;
  }

  const anchor = liveMarkerBlock?.isConnected
    ? liveMarkerBlock
    : state.markerBlock?.isConnected
      ? state.markerBlock
      : state.nextBlock?.isConnected
        ? state.nextBlock
        : null;
  let moved = false;
  if (anchor && figureBlock.nextElementSibling !== anchor) {
    editor.insertBefore(figureBlock, anchor);
    moved = true;
  } else if (!anchor && state.previousBlock?.isConnected
    && state.previousBlock.nextElementSibling !== figureBlock) {
    state.previousBlock.after(figureBlock);
    moved = true;
  } else if (!anchor && !state.previousBlock?.isConnected) {
    const indexedAnchor = [...editor.children]
      .filter(child => child !== figureBlock)[state.targetIndex] || null;
    if (indexedAnchor !== figureBlock) {
      editor.insertBefore(figureBlock, indexedAnchor);
      moved = true;
    }
  }

  for (const markerNode of markerMatches) {
    markerNode.nodeValue = markerNode.nodeValue.replace(marker, '');
  }
  const staleMarkerBlock = liveMarkerBlock?.isConnected
    ? liveMarkerBlock
    : state.markerBlock?.isConnected
      ? state.markerBlock
      : null;
  if (staleMarkerBlock && staleMarkerBlock !== figureBlock
    && !staleMarkerBlock.textContent.trim()) {
    staleMarkerBlock.remove();
  }

  const caption = insertedFigure.querySelector('figcaption textarea');
  if (caption && state.captionText && caption.value !== state.captionText) {
    const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
    caption.focus();
    setter.call(caption, state.captionText);
    caption.dispatchEvent(new Event('input', { bubbles: true }));
    caption.blur();
  }
  editor.dispatchEvent(new Event('input', { bubbles: true }));
  state.insertedFigure = insertedFigure;
  state.status = moved ? 'placement-recovered' : 'complete';

  return {
    outcome: moved ? 'recovered' : 'already-inserted',
    figuresBefore: state.beforeFigureCount,
    figuresNow: currentFigures.length,
    markerRemoved: !editor.textContent.includes(marker),
    caption: caption?.value || '',
    safeToRetry: false
  };
}

recoverTimedOutImageInsertion(mediaItem.marker);
```

Continue without another upload when the outcome is `recovered` or `already-inserted`. Retry once only when the outcome is `not-created` and `safeToRetry` is `true`. Stop for manual inspection when the state is ambiguous.

## Retry one caption

Use the manifest index of the image. LinkedIn captions are `<textarea maxlength="250">` elements.

```js
function setImageCaption(figureIndex, text) {
  const editor = document.querySelector('div.ProseMirror[contenteditable="true"]');
  const textarea = editor.querySelectorAll('figure figcaption textarea')[figureIndex];
  if (!textarea) throw new Error(`Caption ${figureIndex} was not found.`);
  const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
  textarea.focus();
  setter.call(textarea, text);
  textarea.dispatchEvent(new Event('input', { bubbles: true }));
  textarea.blur();
  return textarea.value;
}
```

## Cover image

Upload the cover last in two observable phases. Opening the crop dialog and applying the final cover are separate actions, so a timeout on the final selector cannot hide a successful file selection.

```js
window.findArticleCoverCropDialog = function findArticleCoverCropDialog() {
  return [...document.querySelectorAll('[role="dialog"]')].find(dialog => {
    const hasPreview = !!dialog.querySelector('img, canvas');
    const hasNext = [...dialog.querySelectorAll('button')]
      .some(button => /^(next|siguiente)$/i.test(button.textContent.trim()));
    return dialog.isConnected && hasPreview && hasNext;
  }) || null;
};

window.getArticleCoverUploadState = function getArticleCoverUploadState() {
  const coverImage = document.querySelector('[class*="cover-media"] img, [class*="coverMedia"] img');
  const cropDialog = findArticleCoverCropDialog();
  const nextButton = cropDialog
    ? [...cropDialog.querySelectorAll('button')]
      .find(button => /^(next|siguiente)$/i.test(button.textContent.trim()))
    : null;
  return {
    stage: coverImage ? 'applied' : cropDialog ? 'crop-ready' : 'idle',
    cover: !!coverImage,
    cropDialog: !!cropDialog,
    cropPreview: !!cropDialog?.querySelector('img, canvas'),
    nextAvailable: !!nextButton,
    nextEnabled: !!nextButton && !nextButton.disabled
      && nextButton.getAttribute('aria-disabled') !== 'true'
  };
};

window.waitForArticleCoverState = async function waitForArticleCoverState(predicate, timeout = 10000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    const state = getArticleCoverUploadState();
    if (predicate(state)) return state;
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  throw new Error('Timed out waiting for LinkedIn cover UI.');
};

window.openArticleCoverCrop = async function openArticleCoverCrop(fileName) {
  const file = window.__files?.[fileName];
  if (!file) throw new Error(`${fileName} is not hydrated.`);
  const originalInputClick = HTMLInputElement.prototype.click;
  const originalPicker = window.showOpenFilePicker;

  try {
    HTMLInputElement.prototype.click = function patchedInputClick() {
      if (this.type !== 'file') return originalInputClick.call(this);
      const transfer = new DataTransfer();
      transfer.items.add(file);
      this.files = transfer.files;
      this.dispatchEvent(new Event('change', { bubbles: true }));
    };
    if (originalPicker) {
      window.showOpenFilePicker = async () => [{
        kind: 'file',
        name: file.name,
        getFile: async () => file
      }];
    }

    const uploadButton = [...document.querySelectorAll('button')]
      .find(button => /upload from computer|subir desde el ordenador/i.test(button.textContent));
    if (!uploadButton) throw new Error('Cover upload button was not found.');
    uploadButton.click();
    return await waitForArticleCoverState(state => state.stage === 'crop-ready');
  } finally {
    HTMLInputElement.prototype.click = originalInputClick;
    if (originalPicker) window.showOpenFilePicker = originalPicker;
  }
};

await openArticleCoverCrop(manifest.coverFileName);
```

Require `stage: "crop-ready"` before continuing. In a separate JavaScript call, confirm the crop:

```js
async function confirmArticleCoverCrop() {
  const initialState = getArticleCoverUploadState();
  if (initialState.stage === 'applied') return initialState;
  if (initialState.stage !== 'crop-ready') {
    throw new Error(`Expected crop-ready cover state, found ${initialState.stage}.`);
  }

  const nextButton = await (async () => {
    const deadline = Date.now() + 10000;
    while (Date.now() < deadline) {
      const dialog = findArticleCoverCropDialog();
      const button = dialog
        ? [...dialog.querySelectorAll('button')]
          .find(candidate => /^(next|siguiente)$/i.test(candidate.textContent.trim()))
        : null;
      if (button && !button.disabled && button.getAttribute('aria-disabled') !== 'true') {
        return button;
      }
      await new Promise(resolve => setTimeout(resolve, 250));
    }
    throw new Error('Timed out waiting for the enabled cover Next button.');
  })();
  nextButton.click();

  try {
    return await waitForArticleCoverState(state => state.stage === 'applied', 12000);
  } catch (error) {
    return {
      ...getArticleCoverUploadState(),
      confirmationTimedOut: true,
      message: error.message
    };
  }
}

const coverResult = manifest.coverUrl
  ? await confirmArticleCoverCrop()
  : { stage: 'skipped', cover: false };
coverResult;
```

If confirmation returns `confirmationTimedOut`, call `getArticleCoverUploadState()` before taking another action. Continue when the stage is `applied`. When it remains `crop-ready`, the file selection succeeded but Next was not accepted; click the enabled Next button once more through `confirmArticleCoverCrop()`. Do not reopen the file picker. Stop for inspection when the stage is `idle`.

When replacing an existing cover, use the edit or remove button inside the element whose class contains `cover-media`, then run the same two-phase cover flow.

## Readiness and focus guards

Run `editorReadiness()` before the first real input and after any pause. Run `assertFocus(kind)` right before pressing keys or typing.

```js
function editorReadiness() {
  const editor = document.querySelector('div.ProseMirror[contenteditable="true"]');
  return {
    visible: document.visibilityState === 'visible', // 'hidden' => typing is silently lost, screenshots time out
    hasFocus: document.hasFocus(),
    editor: !!editor,
    k: 1568 / window.innerWidth, // replace 1568 with the reported screenshot frame width
    scrollY: Math.round(scrollY)
  };
}

function assertFocus(kind, index = 0) {
  const active = document.activeElement;
  const editor = document.querySelector('div.ProseMirror[contenteditable="true"]');
  const ok = {
    editor: active === editor,
    title: active?.matches?.('textarea[placeholder="Title"]'),
    caption: active === editor?.querySelectorAll('figure figcaption textarea')[index]
  }[kind];
  if (!ok) throw new Error(`Focus is not on ${kind}: ${active?.tagName} ${active?.getAttribute?.('aria-label') || active?.getAttribute?.('placeholder') || ''}`);
  return `focus ok: ${kind}`;
}
```

## Locate a marker without scrolling (image placement)

Scroll with the computer tool's `scroll_to` (on a `find` ref) and wait about 2 s first. Then read coordinates with this function, which does NOT scroll, so the rect is not stale.

```js
function locateMarkerBlockNoScroll(marker, frameWidth = 1568) {
  const k = frameWidth / window.innerWidth;
  const editor = document.querySelector('div.ProseMirror[contenteditable="true"]');
  const blocks = [...editor.children].filter(child => child.textContent.trim() === marker);
  if (blocks.length !== 1) throw new Error(`${marker}: ${blocks.length} blocks`);
  const rect = blocks[0].getBoundingClientRect();
  if (rect.bottom < 80 || rect.top > window.innerHeight - 20) throw new Error(`${marker} is off screen (top ${Math.round(rect.top)}); scroll_to and wait again.`);
  return {
    x: Math.round((rect.left + 20) * k),
    y: Math.round((rect.top + rect.height / 2) * k),
    figures: editor.querySelectorAll('figure').length
  };
}
```

Then `triple_click` at `{x, y}` and, in one JavaScript call, assert the selection and paste:

```js
(() => {
  const marker = '[[LI_MEDIA_001]]';
  const fileName = 'li_media_001-body-1.png';
  const selected = window.getSelection().toString().trim();
  if (selected !== marker) throw new Error('selection mismatch: ' + JSON.stringify(selected.slice(0, 60)));
  const editor = document.querySelector('div.ProseMirror[contenteditable="true"]');
  const transfer = new DataTransfer();
  transfer.items.add(window.__files[fileName]);
  editor.dispatchEvent(new ClipboardEvent('paste', { clipboardData: transfer, bubbles: true, cancelable: true }));
  return 'pasted';
})();
```

Check the placement after about 12 s:

```js
function figureState() {
  const editor = document.querySelector('div.ProseMirror[contenteditable="true"]');
  const children = [...editor.children];
  return {
    blocks: children.length,
    figures: editor.querySelectorAll('figure').length,
    markers: editor.textContent.match(/\[\[LI_MEDIA_\d{3}\]\]/g) || [],
    placed: children
      .map((block, index) => ({ block, index }))
      .filter(({ block }) => block.tagName === 'FIGURE' || block.querySelector?.('figure'))
      .map(({ block, index }) => ({
        index,
        previous: block.previousElementSibling?.textContent.slice(0, 35),
        nextNonEmpty: (block.nextElementSibling?.textContent.trim() ? block.nextElementSibling : block.nextElementSibling?.nextElementSibling)?.textContent.slice(0, 35),
        naturalWidth: block.querySelector('img')?.naturalWidth,
        caption: block.querySelector('figcaption textarea')?.value
      }))
  };
}
```

## Edit text in place (Step 8 and inline-code fixes)

`selectTextInEditor` selects exactly one occurrence, identified by its context, and syncs ProseMirror through `selectionchange`. Then use the computer `type` action to type the replacement, and verify with `checkTextInEditor`. Pass `before = ''` to anchor at the start of a block. Process several edits in one block from last to first.

```js
async function selectTextInEditor(before, term, after) {
  const editor = document.querySelector('div.ProseMirror[contenteditable="true"]');
  const blocks = [...editor.querySelectorAll('p, li, h2, h3')]
    .filter(block => !block.closest('pre') && !block.querySelector('p, li'));
  const needle = before + term + after;
  const hits = [];
  for (const block of blocks) {
    const text = block.textContent;
    let index = text.indexOf(needle);
    while (index >= 0) {
      if (before !== '' || index === 0) hits.push({ block, start: index + before.length });
      index = text.indexOf(needle, index + 1);
    }
  }
  if (hits.length !== 1) throw new Error(`${hits.length} matches for context`);
  const { block, start } = hits[0];
  const walker = document.createTreeWalker(block, NodeFilter.SHOW_TEXT);
  let node, position = 0, startNode, startOffset, endNode, endOffset;
  while ((node = walker.nextNode())) {
    const length = node.nodeValue.length;
    if (!startNode && start < position + length) { startNode = node; startOffset = start - position; }
    if (startNode && start + term.length <= position + length) { endNode = node; endOffset = start + term.length - position; break; }
    position += length;
  }
  block.scrollIntoView({ block: 'center' });
  editor.focus();
  const range = document.createRange();
  range.setStart(startNode, startOffset);
  range.setEnd(endNode, endOffset);
  const selection = window.getSelection();
  selection.removeAllRanges();
  selection.addRange(range);
  document.dispatchEvent(new Event('selectionchange'));
  await new Promise(resolve => setTimeout(resolve, 600));
  if (selection.toString() !== term) throw new Error('selection is not the term');
  return 'selected';
}

function checkTextInEditor(needle) {
  const editor = document.querySelector('div.ProseMirror[contenteditable="true"]');
  const found = [...editor.querySelectorAll('p, li, h2, h3')]
    .some(block => !block.closest('pre') && block.textContent.includes(needle));
  if (!found) throw new Error('expected text not found');
  return { ok: true, anchors: editor.querySelectorAll('a[href]').length };
}
```

Batch pattern for one replacement (several can be chained in one `browser_batch`; a thrown assertion stops the batch):

```json
[
  {"name": "javascript_tool", "input": {"action": "javascript_exec", "tabId": 0, "text": "await selectTextInEditor('expone el famoso ', 'last_activity_at', ' de cada')"}},
  {"name": "computer", "input": {"action": "type", "text": "'last_activity_at'", "tabId": 0}},
  {"name": "computer", "input": {"action": "wait", "duration": 1, "tabId": 0}},
  {"name": "javascript_tool", "input": {"action": "javascript_exec", "tabId": 0, "text": "checkTextInEditor(\"expone el famoso 'last_activity_at' de cada\")"}}
]
```

To replace several whole blocks (for example a section rewrite), use the same pattern with a range from the first text node of the first block to the end of the last block. Assert the selected text's start and end, then dispatch `ClipboardEvent('paste')` with `text/html`. Run `findUnexpectedLinks` afterwards.

## Find and remove LinkedIn auto-links (Step 4b)

```js
function findUnexpectedLinks(manifest, frameWidth = 1568) {
  const k = frameWidth / window.innerWidth;
  const editor = document.querySelector('div.ProseMirror[contenteditable="true"]');
  const expected = new Set(manifest.expectedLinks.map(href => new URL(href).href));
  return [...editor.querySelectorAll('a[href]')]
    .filter(anchor => !expected.has(anchor.href))
    .map(anchor => {
      const rect = anchor.getBoundingClientRect();
      return {
        text: anchor.textContent.replace(/\./g, '·'),
        onScreen: rect.top > 80 && rect.bottom < window.innerHeight,
        x: Math.round((rect.left + rect.width / 2) * k),
        y: Math.round((rect.top + rect.height / 2) * k)
      };
    });
}
```

On the LinkedIn page, pass the lite manifest that `hydrateBundleAndPaste()` stored: `window.__liManifest`, or after a reload `JSON.parse(sessionStorage.getItem('__liManifest'))`. Auto-links typically point at `http://<token>/`, for example `http://user.name/` or `http://GitHub.com/`.

For each auto-link:

1. Scroll it on screen.
2. `double_click` its coordinates.
3. Assert `getSelection().toString() === <link text>`; compare inside JS, because dotted identifiers are blocked in tool output.
4. `type` the identical text. The link mark is dropped and the text is unchanged.
5. Re-run `findUnexpectedLinks`.

## Known dead ends (don't retry these)

- Creating a second tab in the MCP group to read the blog → it becomes the active tab and the LinkedIn tab turns `hidden`: screenshots time out and typing is silently lost.
- Typing or pressing keys while `document.visibilityState === 'hidden'` → the tool reports success, but nothing reaches the editor.
- Pressing `BackSpace` after a coordinate click without `assertFocus` → it deleted a character in the title.
- `ctrl+Home` + `Delete` to remove the leading empty paragraph → unreliable; use click on first text line + `Home` + `BackSpace`.
- Reading coordinates in the same call as `scrollIntoView` on the LinkedIn editor → stale by hundreds of px; LinkedIn re-scrolls.
- `triple_click` by `ref` on a marker paragraph → once selected the previous list item instead; prefer `scroll_to` + wait + coordinates, and always assert the selection.
- Toolbar Link button on a selected auto-link → opens an "Edit link" dialog (Cancel/Apply only); it does not unlink.
- Link popover trash icon → works when it shows, but it does not show reliably; use the retype method.
- Flattening tables into `Label | Column: value` paragraphs → unreadable; the user rejected it. Use Step 2b.
- Leaving inline `<code>` in the pasted HTML → LinkedIn silently drops the formatting; use single quotes.
- Returning dotted identifiers or URL hostnames in tool output → `[BLOCKED: JWT token]`; compare inside JS or replace dots.

- `fetch()` of ANY external URL or data-URL from the LinkedIn tab → CSP "Failed to fetch".
- Pasted `<img src="https://...">` → dropped by the editor schema.
- `window.open` / anchor `target=_blank` bridges → popup-blocked or new tab escapes the session tab group.
- `document.execCommand('insertHTML')` on ProseMirror → unreliable; use the paste event.
- Drag-and-drop `DragEvent` on the cover placeholder → ignored.
- `resize_window` / `save_to_disk` on screenshots → may be unavailable; don't build plans on them.
- Locating image positions by nearby paragraph text → fails with repeated prose, adjacent figures, galleries, or an image at the start.
- Re-pasting the complete body after images exist → duplicates or displaces editor state.
