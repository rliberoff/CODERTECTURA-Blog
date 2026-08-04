"""Offline tests for the article-specific cover-image style contract."""

import os
import sys


_SCRIPTS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "automation", "scripts")
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import _cover_style  # noqa: E402
import generate_image as gi  # noqa: E402


def test_cover_style_suffix_is_the_shared_single_source_of_truth():
    assert gi.COVER_STYLE_SUFFIX is _cover_style.COVER_STYLE_SUFFIX
    # The companion brief spec (used by generate_article.py) exists alongside it.
    assert _cover_style.COVER_BRIEF_SPEC.strip()


def test_cover_style_defers_concept_to_the_brief_and_survives_crops():
    style = gi.COVER_STYLE_SUFFIX.lower()

    assert "follow the supplied brief" in style
    assert "thumbnail size" in style
    assert "central 70% safe area" in style
    assert "2:1 linkedin" in style


def test_cover_style_does_not_impose_the_previous_recurring_scene():
    style = gi.COVER_STYLE_SUFFIX.lower()

    assert "deep midnight navy-to-black base" not in style
    assert "moody volumetric lighting" not in style
    assert "allowed subjects include" not in style


def test_cover_style_is_painterly_not_photorealistic_advertising():
    style = gi.COVER_STYLE_SUFFIX.lower()

    assert "digital painting" in style
    assert "painterly" in style
    assert "non-photorealistic" in style
    assert "premium advertising key visual" not in style
    assert "polished materials" not in style
    assert "production-quality detail" not in style


def test_cover_style_is_format_only_with_positive_grounding():
    style = gi.COVER_STYLE_SUFFIX.lower()

    # Positive grounding and full-bleed format rules.
    assert "contemporary world of software and technology" in style
    assert "edge to edge" in style

    # The old banned-imagery negation list is gone: grounding is stated
    # positively instead of enumerating what to avoid.
    for banned_term in (
        "avoid fantasy",
        "fairy-tale",
        "steampunk",
        "brass",
        "parchment",
        "wizards",
        "letterboxing",
    ):
        assert banned_term not in style

    # Only the minimal safety negatives remain.
    assert "no baked-in text" in style
    assert "no watermarks" in style
    assert "no recognisable real human faces" in style
