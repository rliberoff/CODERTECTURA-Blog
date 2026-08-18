"""Offline tests for the cover-refresh prompt builder."""

import os
import sys


_SCRIPTS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "automation", "scripts")
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import refresh_cover_prompt as rcp  # noqa: E402


def test_split_front_matter_returns_front_and_body():
    front, body = rcp.split_front_matter(
        "---\n"
        "title: Example\n"
        "description: Demo\n"
        "---\n"
        "Body text.\n"
    )

    assert front["title"] == "Example"
    assert front["description"] == "Demo"
    assert body == "Body text.\n"


def test_plain_text_excerpt_strips_markdown_noise():
    excerpt = rcp.plain_text_excerpt(
        "# Heading\n\n"
        "Texto con [enlace](https://example.com) y `codigo`.\n\n"
        "```bash\naz group list\n```\n\n"
        "- elemento\n"
        "{{img:hero}}\n"
    )

    assert "Heading" in excerpt
    assert "Texto con enlace y codigo." in excerpt
    assert "az group list" not in excerpt
    assert "{{img:hero}}" not in excerpt


def test_build_user_prompt_includes_article_context_and_brief():
    prompt = rcp.build_user_prompt(
        {
            "title": "Azure Container Apps en producción",
            "description": "Cómo desplegar con resiliencia",
            "tags": ["azure", "aca"],
            "categories": ["azure-applications"],
        },
        "Un cuerpo con ideas clave sobre despliegues y observabilidad.",
        "Haz la escena menos oscura y más centrada en operaciones.",
    )

    assert "Title: Azure Container Apps en producción" in prompt
    assert "Description: Cómo desplegar con resiliencia" in prompt
    assert "Tags: azure, aca" in prompt
    assert "Categories: azure-applications" in prompt
    assert "Requested cover changes: Haz la escena menos oscura" in prompt


def test_parse_image_prompt_validates_json_shape():
    prompt = rcp.parse_image_prompt(
        '{"image_prompt":"Ilustración editorial evocadora en un centro de operaciones cloud, con paneles de telemetría, un flujo de despliegue visible y una atmósfera más luminosa que subraye control y calma. La escena debe transmitir paso a producción con seguridad, usando una paleta de azules profundos con acentos ámbar para marcar los puntos críticos. La composición debe mantener el foco en la transición desde el entorno de desarrollo hacia la operación estable, con una metáfora visual de continuidad y observabilidad."}'
    )

    assert "Ilustración editorial evocadora" in prompt

