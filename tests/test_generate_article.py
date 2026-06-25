"""Offline tests for the Phase-2 grounding + body-image changes in
``generate_article.py``.

No network is performed. Runnable with ``python -m pytest tests/`` (from the repo
root) or directly with ``python tests/test_generate_article.py``.
"""

import json
import os
import sys
import tempfile

import yaml

# The automation scripts are plain modules (no package); make them importable.
_SCRIPTS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "automation", "scripts")
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import generate_article as ga  # noqa: E402

NOW_ISO = "2026-06-24T15:03:58+00:00"


def _source(url, *, title="T", date="2026-06-20", kind="primary", images=None, excerpt=None):
    """Build a SOURCES_FILE-shaped raw source entry."""
    entry = {"url": url, "title": title, "published_date": date, "kind": kind}
    if images is not None:
        entry["images"] = images
    if excerpt is not None:
        entry["excerpt"] = excerpt
    return entry


# -----------------------------------------------------------------------------
# Source validation + parsing (UNTRUSTED file input, allowlist defence in depth).
# -----------------------------------------------------------------------------


def test_validate_source_keeps_allowlisted_and_sanitises():
    record = ga.validate_source(
        _source(
            "https://devblogs.microsoft.com/dotnet/post",
            title="Novedades  en\n.NET",
            images=[{"url": "https://devblogs.microsoft.com/img.png", "description": "x"}],
        )
    )
    assert record is not None
    assert record["host"] == "devblogs.microsoft.com"
    assert record["title"] == "Novedades en .NET"  # whitespace collapsed
    assert record["kind"] == "primary"
    assert record["images"][0]["url"] == "https://devblogs.microsoft.com/img.png"


def test_validate_source_drops_off_allowlist_host():
    assert ga.validate_source(_source("https://example.com/x")) is None
    assert ga.validate_source(_source("https://microsoft.com.evil.example/x")) is None
    assert ga.validate_source({"title": "no url"}) is None


def test_validate_source_drops_off_allowlist_image_candidates():
    record = ga.validate_source(
        _source(
            "https://learn.microsoft.com/doc",
            images=[
                {"url": "https://evil.example/x.png", "description": "bad"},
                "https://learn.microsoft.com/ok.png",
            ],
        )
    )
    assert record is not None
    # Only the allowlisted image candidate survives.
    assert [img["url"] for img in record["images"]] == ["https://learn.microsoft.com/ok.png"]


def test_parse_sources_caps_dedupes_and_filters():
    raw = {
        "sources": [
            _source("https://learn.microsoft.com/a"),
            _source("https://learn.microsoft.com/a"),  # duplicate
            _source("https://example.com/bad"),  # off-allowlist
            _source("https://github.blog/b"),
            _source("https://azure.microsoft.com/c"),
            _source("https://devblogs.microsoft.com/d"),
            _source("https://techcommunity.microsoft.com/e"),
            _source("https://microsoft.com/f"),  # 6th valid -> over MAX_SOURCES
        ]
    }
    sources = ga.parse_sources(raw)
    urls = [s["url"] for s in sources]
    assert len(sources) == ga.MAX_SOURCES == 5
    assert "https://example.com/bad" not in urls
    assert urls.count("https://learn.microsoft.com/a") == 1


def test_load_sources_tolerates_absent_and_malformed(monkeypatch=None):
    # Absent env -> [].
    saved = os.environ.pop("SOURCES_FILE", None)
    try:
        assert ga.load_sources() == []
        with tempfile.TemporaryDirectory() as tmp:
            # Malformed JSON -> [] (warn, no crash).
            bad = os.path.join(tmp, "bad.json")
            with open(bad, "w", encoding="utf-8") as handle:
                handle.write("{ not json ")
            os.environ["SOURCES_FILE"] = bad
            assert ga.load_sources() == []

            # Bare list payload -> validated list.
            good = os.path.join(tmp, "good.json")
            with open(good, "w", encoding="utf-8") as handle:
                json.dump([_source("https://learn.microsoft.com/a")], handle)
            os.environ["SOURCES_FILE"] = good
            loaded = ga.load_sources()
            assert len(loaded) == 1 and loaded[0]["url"] == "https://learn.microsoft.com/a"
    finally:
        if saved is None:
            os.environ.pop("SOURCES_FILE", None)
        else:
            os.environ["SOURCES_FILE"] = saved


def test_build_sources_block_surfaces_images_and_excerpt():
    sources = ga.parse_sources(
        {
            "sources": [
                _source(
                    "https://devblogs.microsoft.com/dotnet/post",
                    title="Post",
                    excerpt="var x = 1;\nConsole.WriteLine(x);",
                    images=[
                        {"url": "https://devblogs.microsoft.com/diagram.png", "description": "diagram"}
                    ],
                )
            ]
        }
    )
    block = ga.build_sources_block(sources)
    assert ga.UNTRUSTED_OPEN in block and ga.UNTRUSTED_CLOSE in block
    assert "https://devblogs.microsoft.com/dotnet/post" in block
    # Image URL is now SURFACED so the model can echo back EXACTLY one (still inside
    # the UNTRUSTED block, and re-validated against the provided set afterwards).
    assert "https://devblogs.microsoft.com/diagram.png" in block
    assert "diagram" in block  # image description shared
    assert "Console.WriteLine" in block  # excerpt surfaced for code grounding
    assert ga.build_sources_block([]) == ""


# -----------------------------------------------------------------------------
# Body-image contract validation.
# -----------------------------------------------------------------------------


def test_normalise_placeholder_variants():
    assert ga.normalise_placeholder("{{img:diagram1}}") == "{{img:diagram1}}"
    assert ga.normalise_placeholder("  {{ img : d_1 }} ") == "{{img:d_1}}"
    assert ga.normalise_placeholder("bare-id") == "{{img:bare-id}}"
    assert ga.normalise_placeholder("has spaces") is None
    assert ga.normalise_placeholder(None) is None


def test_select_body_images_ai_valid_and_missing_prompt():
    body = "Intro.\n\n{{img:good}}\n\nMore.\n\n{{img:bad}}\n"
    raw = [
        {"placeholder": "{{img:good}}", "type": "ai", "alt": "a", "caption": "c", "prompt_en": "a robot"},
        {"placeholder": "{{img:bad}}", "type": "ai", "alt": "a", "caption": "c"},  # no prompt
    ]
    specs = ga.select_body_images(raw, body_markdown=body, sources=[])
    assert len(specs) == 1
    assert specs[0]["placeholder"] == "{{img:good}}"
    assert specs[0]["type"] == "ai"
    assert specs[0]["prompt_en"] == "a robot"


def test_select_body_images_source_baked_with_image_url():
    sources = ga.parse_sources(
        {
            "sources": [
                _source(
                    "https://devblogs.microsoft.com/dotnet/post",
                    images=["https://devblogs.microsoft.com/diagram.png"],
                )
            ]
        }
    )
    body = "Texto.\n\n{{img:src1}}\n"
    raw = [
        {
            "placeholder": "{{img:src1}}",
            "type": "source",
            "alt": "diagrama",
            "caption": "pie",
            "source_url": "https://devblogs.microsoft.com/dotnet/post",
        }
    ]
    specs = ga.select_body_images(raw, body_markdown=body, sources=sources)
    assert len(specs) == 1
    spec = specs[0]
    assert spec["type"] == "source"
    assert spec["image_url"] == "https://devblogs.microsoft.com/diagram.png"  # baked by orchestrator
    assert spec["host"] == "devblogs.microsoft.com"
    assert spec["source_url"] == "https://devblogs.microsoft.com/dotnet/post"


def test_select_body_images_source_accepts_model_image_url():
    # The model now MAY name a concrete image_url; it is accepted only when it is
    # EXACTLY one of the provided, allowlisted candidates for the cited source.
    sources = ga.parse_sources(
        {
            "sources": [
                _source(
                    "https://devblogs.microsoft.com/dotnet/post",
                    images=[
                        "https://devblogs.microsoft.com/a.png",
                        "https://devblogs.microsoft.com/b.png",
                    ],
                )
            ]
        }
    )
    body = "Texto.\n\n{{img:src1}}\n"
    raw = [
        {
            "placeholder": "{{img:src1}}",
            "type": "source",
            "alt": "diagrama",
            "caption": "pie",
            "source_url": "https://devblogs.microsoft.com/dotnet/post",
            "image_url": "https://devblogs.microsoft.com/b.png",  # the model's explicit choice
        }
    ]
    specs = ga.select_body_images(raw, body_markdown=body, sources=sources)
    assert len(specs) == 1
    assert specs[0]["image_url"] == "https://devblogs.microsoft.com/b.png"  # honoured, not the first
    assert specs[0]["source_url"] == "https://devblogs.microsoft.com/dotnet/post"


def test_select_body_images_source_drops_unprovided_or_offallowlist_image_url():
    sources = ga.parse_sources(
        {
            "sources": [
                _source(
                    "https://devblogs.microsoft.com/dotnet/post",
                    images=["https://devblogs.microsoft.com/a.png"],
                )
            ]
        }
    )
    body = "Texto.\n\n{{img:s1}}\n\n{{img:s2}}\n"
    # (1) image_url not among the provided candidates for that source -> drop.
    raw_unprovided = [
        {
            "placeholder": "{{img:s1}}",
            "type": "source",
            "alt": "x",
            "caption": "y",
            "source_url": "https://devblogs.microsoft.com/dotnet/post",
            "image_url": "https://devblogs.microsoft.com/UNPROVIDED.png",
        }
    ]
    assert ga.select_body_images(raw_unprovided, body_markdown=body, sources=sources) == []
    # (2) off-allowlist image_url -> drop (never substituted).
    raw_off = [
        {
            "placeholder": "{{img:s2}}",
            "type": "source",
            "alt": "x",
            "caption": "y",
            "source_url": "https://devblogs.microsoft.com/dotnet/post",
            "image_url": "https://evil.example/x.png",
        }
    ]
    assert ga.select_body_images(raw_off, body_markdown=body, sources=sources) == []


def test_select_body_images_source_drops_invented_source_url_even_with_image_url():
    sources = ga.parse_sources(
        {
            "sources": [
                _source(
                    "https://devblogs.microsoft.com/dotnet/post",
                    images=["https://devblogs.microsoft.com/a.png"],
                )
            ]
        }
    )
    body = "Texto.\n\n{{img:s}}\n"
    raw = [
        {
            "placeholder": "{{img:s}}",
            "type": "source",
            "alt": "x",
            "caption": "y",
            "source_url": "https://devblogs.microsoft.com/INVENTED",  # not a provided source
            "image_url": "https://devblogs.microsoft.com/a.png",
        }
    ]
    assert ga.select_body_images(raw, body_markdown=body, sources=sources) == []


def test_select_body_images_drops_source_not_in_provided_sources():
    sources = ga.parse_sources(
        {"sources": [_source("https://learn.microsoft.com/a", images=["https://learn.microsoft.com/i.png"])]}
    )
    body = "Texto.\n\n{{img:s}}\n"
    # source_url is allowlisted but was NOT one of the provided sources -> drop.
    raw = [
        {
            "placeholder": "{{img:s}}",
            "type": "source",
            "alt": "x",
            "caption": "y",
            "source_url": "https://learn.microsoft.com/OTHER",
        }
    ]
    assert ga.select_body_images(raw, body_markdown=body, sources=sources) == []


def test_select_body_images_drops_source_without_image_candidate():
    sources = ga.parse_sources({"sources": [_source("https://learn.microsoft.com/a")]})  # no images
    body = "Texto.\n\n{{img:s}}\n"
    raw = [
        {
            "placeholder": "{{img:s}}",
            "type": "source",
            "alt": "x",
            "caption": "y",
            "source_url": "https://learn.microsoft.com/a",
        }
    ]
    assert ga.select_body_images(raw, body_markdown=body, sources=sources) == []


def test_select_body_images_requires_placeholder_in_body():
    body = "No placeholder here.\n"
    raw = [{"placeholder": "{{img:x}}", "type": "ai", "alt": "a", "caption": "c", "prompt_en": "p"}]
    assert ga.select_body_images(raw, body_markdown=body, sources=[]) == []


def test_apply_body_image_placeholders_strips_unkept_only():
    body = "Intro.\n\n{{img:keep}}\n\nMiddle.\n\n{{img:drop}}\n\nEnd.\n"
    specs = [{"placeholder": "{{img:keep}}"}]
    out = ga.apply_body_image_placeholders(body, specs)
    assert "{{img:keep}}" in out
    assert "{{img:drop}}" not in out
    assert "\n\n\n" not in out  # blank runs collapsed


# -----------------------------------------------------------------------------
# Full document assembly: grounding provenance + backward compatibility.
# -----------------------------------------------------------------------------


def _front_matter(document):
    assert document.startswith("---\n")
    closing = document.index("\n---", 3)
    return yaml.safe_load(document[4:closing])


def test_build_document_grounded_with_body_images():
    sources = ga.parse_sources(
        {
            "sources": [
                _source(
                    "https://devblogs.microsoft.com/dotnet/post",
                    title="Origen",
                    images=["https://devblogs.microsoft.com/d.png"],
                )
            ]
        }
    )
    article = {
        "title": "Novedades de .NET",
        "slug": "novedades-net",
        "description": "Una descripción.",
        "categories": [".NET"],
        "tags": ["dotnet", "azure"],
        "image_prompt": "A clean abstract illustration about .NET news.",
        "body_markdown": "Intro.\n\n{{img:fig}}\n\nDesarrollo del artículo.\n",
        "body_images": [
            {
                "placeholder": "{{img:fig}}",
                "type": "source",
                "alt": "diagrama",
                "caption": "pie",
                "source_url": "https://devblogs.microsoft.com/dotnet/post",
            }
        ],
    }
    slug, document, image_prompt, specs = ga.build_document(
        article, deployment="gpt-5.4-mini", now_iso=NOW_ISO, sources=sources, want_body_images=True
    )
    assert slug == "novedades-net"
    assert image_prompt == "A clean abstract illustration about .NET news."
    assert len(specs) == 1 and specs[0]["image_url"] == "https://devblogs.microsoft.com/d.png"

    front = _front_matter(document)
    assert front["ai"]["sources"][0]["url"] == "https://devblogs.microsoft.com/dotnet/post"
    assert front["ai"]["sources"][0]["published_date"] == "2026-06-20"
    # The kept placeholder remains for the resolver to swap.
    assert "{{img:fig}}" in document


def test_build_document_backward_compatible_without_sources():
    # No sources and body images disabled (manual flow): placeholders stripped,
    # no ai.sources key, no specs.
    article = {
        "title": "Tema manual",
        "description": "desc",
        "body_markdown": "Texto.\n\n{{img:orphan}}\n\nFin.\n",
        "categories": ["Azure"],
        "tags": ["azure"],
        "image_prompt": "Cover.",
        "body_images": [
            {"placeholder": "{{img:orphan}}", "type": "ai", "alt": "a", "caption": "c", "prompt_en": "p"}
        ],
    }
    slug, document, image_prompt, specs = ga.build_document(
        article, deployment="gpt-5.4-mini", now_iso=NOW_ISO
    )
    assert specs == []
    assert "{{img:orphan}}" not in document  # stripped -> no raw token shipped
    front = _front_matter(document)
    assert "sources" not in front["ai"]
    assert front["draft"] is True


def test_build_document_grounded_sources_without_images_or_excerpt():
    # A grounded run whose sources carry NO images and NO excerpt (older ledger /
    # hand-authored SOURCES_FILE) must still produce a valid draft and a buildable
    # UNTRUSTED block.
    sources = ga.parse_sources(
        {"sources": [_source("https://learn.microsoft.com/a", title="Doc")]}
    )
    assert sources[0]["images"] == [] and sources[0]["excerpt"] == ""
    article = {
        "title": "Tema sin imágenes",
        "description": "desc",
        "body_markdown": "Cuerpo del artículo.\n",
        "categories": ["Azure"],
        "tags": ["azure"],
        "image_prompt": "Cover.",
    }
    slug, document, image_prompt, specs = ga.build_document(
        article,
        deployment="gpt-5.4-mini",
        now_iso=NOW_ISO,
        sources=sources,
        want_body_images=True,
    )
    assert specs == []
    front = _front_matter(document)
    assert front["ai"]["sources"][0]["url"] == "https://learn.microsoft.com/a"
    block = ga.build_sources_block(sources)
    assert ga.UNTRUSTED_OPEN in block  # builds fine with empty images/excerpt


# -----------------------------------------------------------------------------
# Prose-link allowlist validation (Rai R2): neutralise off-allowlist links while
# leaving code, relative links and allowlisted links verbatim.
# -----------------------------------------------------------------------------


def test_neutralise_offallowlist_inline_link_keeps_text():
    body = "Mira [este recurso](https://evil.example/post) para más detalles."
    out = ga.neutralise_offallowlist_links(body)
    assert "este recurso" in out  # visible text kept
    assert "evil.example" not in out  # off-allowlist URL dropped
    assert "](" not in out  # the link markup is gone


def test_neutralise_keeps_allowlisted_and_relative_links():
    body = (
        "Según [la doc](https://learn.microsoft.com/dotnet) y "
        "[la guía](/posts/guia) lo veréis claro."
    )
    assert ga.neutralise_offallowlist_links(body) == body  # untouched


def test_neutralise_autolink_offallowlist_becomes_inert_code():
    body = "Fuente dudosa: <https://evil.example/y>."
    out = ga.neutralise_offallowlist_links(body)
    assert "`https://evil.example/y`" in out  # inert code, not a live link
    assert "<https://evil.example/y>" not in out


def test_neutralise_keeps_allowlisted_autolink():
    body = "Oficial: <https://github.blog/post>."
    assert ga.neutralise_offallowlist_links(body) == body


def test_neutralise_leaves_fenced_code_links_verbatim():
    body = (
        "Texto previo con [malo](https://evil.example/a).\n"
        "```python\n"
        'requests.get("https://evil.example/in-code")\n'
        "# ver [ref](https://evil.example/b)\n"
        "```\n"
        "Y un [malo2](https://evil.example/c) después."
    )
    out = ga.neutralise_offallowlist_links(body)
    # Links inside the fence are preserved verbatim...
    assert 'requests.get("https://evil.example/in-code")' in out
    assert "[ref](https://evil.example/b)" in out
    # ...while prose links outside the fence are neutralised (text kept, link gone).
    assert "](https://evil.example/a)" not in out
    assert "](https://evil.example/c)" not in out
    assert "malo" in out and "malo2" in out


def test_neutralise_leaves_indented_code_links_verbatim():
    body = (
        "Ejemplo:\n\n"
        "    curl [x](https://evil.example/i)\n\n"
        "Fin del [parrafo](https://evil.example/p)."
    )
    out = ga.neutralise_offallowlist_links(body)
    assert "[x](https://evil.example/i)" in out  # indented code untouched
    assert "](https://evil.example/p)" not in out  # prose link neutralised


def test_neutralise_does_not_mangle_image_syntax():
    # Image markup ![alt](url) must NOT be reduced to bare alt text (the negative
    # lookbehind on '!'); body images are handled by the image pipeline, not here.
    body = "![diagrama](https://evil.example/img.png)"
    assert ga.neutralise_offallowlist_links(body) == body


def test_build_document_neutralises_offallowlist_body_link():
    article = {
        "title": "Tema",
        "description": "desc",
        "body_markdown": "Intro con [enlace](https://evil.example/x) dudoso.\n",
        "categories": ["Azure"],
        "tags": ["azure"],
        "image_prompt": "Cover.",
    }
    _slug, document, _prompt, _specs = ga.build_document(
        article, deployment="gpt-5.4-mini", now_iso=NOW_ISO
    )
    assert "evil.example" not in document  # off-allowlist link stripped from the draft
    assert "enlace" in document  # visible text preserved


# -----------------------------------------------------------------------------
# Image-URL denylist hook (Rai R4): an optional post-incident kill-switch.
# -----------------------------------------------------------------------------


def test_validate_source_images_drops_denylisted(monkeypatch=None):
    saved = os.environ.get("IMAGE_URL_DENYLIST")
    try:
        os.environ["IMAGE_URL_DENYLIST"] = "tracker"
        kept = ga._validate_source_images(
            [
                "https://learn.microsoft.com/clean.png",
                "https://learn.microsoft.com/tracker/pixel.png",  # denylisted substring
            ]
        )
        assert [img["url"] for img in kept] == ["https://learn.microsoft.com/clean.png"]
        # Unset -> both kept (default behaviour unchanged).
        os.environ.pop("IMAGE_URL_DENYLIST", None)
        both = ga._validate_source_images(
            [
                "https://learn.microsoft.com/clean.png",
                "https://learn.microsoft.com/tracker/pixel.png",
            ]
        )
        assert len(both) == 2
    finally:
        if saved is None:
            os.environ.pop("IMAGE_URL_DENYLIST", None)
        else:
            os.environ["IMAGE_URL_DENYLIST"] = saved


def _run_all():
    """Tiny runner so the file also works under plain ``python``."""
    failures = 0
    for name, func in sorted(globals().items()):
        if name.startswith("test_") and callable(func):
            try:
                func()
                print(f"PASS {name}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL {name}: {exc}")
            except Exception as exc:  # noqa: BLE001 - surface any error in the runner
                failures += 1
                print(f"ERROR {name}: {exc!r}")
    if failures:
        print(f"\n{failures} test(s) failed")
        raise SystemExit(1)
    print("\nAll tests passed")


if __name__ == "__main__":
    _run_all()
