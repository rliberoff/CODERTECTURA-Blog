from pathlib import Path


def test_gallery_shortcode_adds_lightbox_data_attributes():
    template = Path("layouts/shortcodes/gallery.html").read_text(encoding="utf-8")

    assert 'data-lightbox-image' in template
    assert 'data-lightbox-group' in template
