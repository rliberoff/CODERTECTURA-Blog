"""Offline tests for the article-specific cover-image style contract."""

import os
import sys


_SCRIPTS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "automation", "scripts")
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import generate_image as gi  # noqa: E402


def test_cover_style_preserves_article_direction_and_social_crops():
    style = gi.STYLE_SUFFIX.lower()

    assert "preserve the article-specific concept" in style
    assert "thumbnail size" in style
    assert "central 70% safe area" in style
    assert "2:1 linkedin" in style


def test_cover_style_does_not_impose_the_previous_recurring_scene():
    style = gi.STYLE_SUFFIX.lower()

    assert "deep midnight navy-to-black base" not in style
    assert "moody volumetric lighting" not in style
    assert "allowed subjects include" not in style


def test_cover_style_is_painterly_not_photorealistic_advertising():
    style = gi.STYLE_SUFFIX.lower()

    assert "digital painting" in style
    assert "painterly" in style
    assert "not photorealistic" in style
    assert "premium advertising key visual" not in style
    assert "polished materials" not in style
    assert "production-quality detail" not in style


def test_cover_style_stays_contemporary_and_fills_the_canvas():
    style = gi.STYLE_SUFFIX.lower()

    assert "contemporary" in style
    assert "avoid fantasy" in style
    assert "steampunk" in style
    assert "edge to edge" in style
    assert "letterboxing" in style
    assert "keep the lower band visually calm" not in style