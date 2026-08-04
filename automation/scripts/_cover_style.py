"""Single source of truth for the cover-image art direction.

The cover pipeline splits art direction in two, on purpose:

* ``COVER_BRIEF_SPEC`` tells the TEXT model (both passes in
  ``generate_article.py``) what to put in the article's ``image_prompt``. The
  brief owns everything article-specific: concept, subject, setting, colour
  palette and mood.
* ``COVER_STYLE_SUFFIX`` is appended to that brief by ``generate_image.py`` at
  image-generation time and carries only the non-negotiable FORMAT rules the
  brief cannot know: medium, safe area, full-bleed canvas, quiet lower portion
  for the title overlay, and the no-text/no-faces safety floor.

Keeping each rule in exactly one place stops the two halves from contradicting
each other inside the final image prompt (they are concatenated there). The
schematic body-image style in ``resolve_body_images.py``
(``BODY_STYLE_SUFFIX``) intentionally stays separate.

Bump ``PROMPT_VERSION`` in ``generate_article.py`` on any material change to
either constant.
"""

from __future__ import annotations

# What the text model must write into "image_prompt". Designed to read
# naturally after both lead-ins used in generate_article.py:
#   draft:  '- "image_prompt": ' + COVER_BRIEF_SPEC
#   polish: '- "image_prompt": after rewriting the article, replace the draft
#            prompt with ' + COVER_BRIEF_SPEC
COVER_BRIEF_SPEC = (
    "an art-direction brief IN SPANISH (es-ES), 3-5 sentences, for an EVOCATIVE "
    "PAINTERLY COVER ILLUSTRATION, based on the FINAL article's specific thesis, the "
    "concrete benefit for the reader and its central tension or transformation. "
    "Express ONE instantly legible, article-specific idea through a symbolic scene or "
    "visual metaphor with narrative weight: a contrast, a threshold, a journey or a "
    "transformation the reader can feel at a glance. State the subject, its action, "
    "the setting, the composition, the atmosphere, dramatic lighting (for example a "
    "warm focal glow against a deep cool ambience) and a purposeful colour palette "
    "whose meaning comes from the article — the brief owns concept, subject, setting "
    "and palette. Ground every element in the CONTEMPORARY world of software and "
    "technology: modern people, present-day devices and workplaces, cloud and code "
    "concepts, or abstract flows of light and data. When specific products or "
    "services are central to the article, name them so their real logos can appear "
    "in the scene; otherwise leave brands out. Framing, canvas and safety rules "
    "(safe area, full-bleed, title space, no text, no faces) are appended "
    "automatically at image-generation time, so do not restate them."
)

# Format-only suffix appended to the brief when calling the image model. It
# defers concept, subject, setting, palette and mood to the brief above.
COVER_STYLE_SUFFIX = (
    " -- evocative editorial cover art for a professional technology publication, "
    "executed as a cinematic digital painting / concept-art illustration: painterly, "
    "non-photorealistic rendering with rich texture and atmospheric depth. Follow "
    "the supplied brief for the concept, subject, setting, colour palette and mood, "
    "keep every element grounded in the contemporary world of software and "
    "technology, and render product logos or brands only when the brief names them. "
    "Communicate one idea immediately at thumbnail size with confident visual "
    "hierarchy, and keep the essential subject and metaphor within the central 70% "
    "safe area so the image survives wide 2:1 LinkedIn and blog-card crops. Paint "
    "the FULL canvas edge to edge as one continuous scene, and make the lower "
    "portion of the scene quieter and less detailed (floor, water, mist, shadow) so "
    "a title can be overlaid, keeping it fully painted as part of the scene. Render "
    "any people as stylised figures or silhouettes. No baked-in text, no watermarks, "
    "no recognisable real human faces."
)
