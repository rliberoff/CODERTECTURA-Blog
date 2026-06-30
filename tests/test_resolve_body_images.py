"""Offline tests for ``resolve_body_images.py``.

No network is performed: the MAI image client and the HTTP image download are both
mocked with in-memory fixtures. Runnable with ``python -m pytest tests/`` (from the
repo root) or directly with ``python tests/test_resolve_body_images.py``.
"""

import http.client
import json
import os
import sys
import tempfile
import urllib.request

# The automation scripts are plain modules (no package); make them importable.
_SCRIPTS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "automation", "scripts")
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import resolve_body_images as rb  # noqa: E402
from _foundry import FoundryError  # noqa: E402

# Minimal valid image fixtures (magic bytes + padding past the 100-byte AI floor).
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 200
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 200
WEBP = b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP" + b"\x00" * 200
GIF = b"GIF89a" + b"\x00" * 200
NOT_IMAGE = b"<html>not an image</html>" + b"\x00" * 80


def _raises(exc_type, func, *args, **kwargs):
    """Dual-mode assertion helper (works under plain ``python`` and pytest)."""
    try:
        func(*args, **kwargs)
    except exc_type:
        return True
    except Exception as exc:  # noqa: BLE001
        raise AssertionError(
            f"expected {exc_type.__name__}, got {type(exc).__name__}: {exc}"
        )
    raise AssertionError(f"expected {exc_type.__name__}, but nothing was raised")


class FakeImageClient:
    """In-memory stand-in for FoundryImageClient (no network)."""

    def __init__(self, data=None, error=None):
        self._data = data
        self._error = error
        self.calls = []

    def generate(self, prompt, *, size="1024x1024", output_compression=100):
        self.calls.append((prompt, size))
        if self._error is not None:
            raise self._error
        return self._data


def _make_downloader(result=None, error=None):
    """Build a fake downloader matching download_allowlisted_image's signature."""

    def _download(url, *, timeout, max_bytes):
        if error is not None:
            raise error
        return result

    return _download


class _FakeResponse:
    def __init__(self, data, final_url):
        self._data = data
        self._final = final_url
        self._pos = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def geturl(self):
        return self._final

    def read(self, n=-1):
        # Stateful, like a real socket: each read advances past the bytes already
        # returned so the loop-read in download_allowlisted_image terminates.
        if n is None or n < 0:
            chunk = self._data[self._pos:]
            self._pos = len(self._data)
            return chunk
        chunk = self._data[self._pos:self._pos + n]
        self._pos += len(chunk)
        return chunk


class _FakeOpener:
    def __init__(self, data, final_url):
        self._data = data
        self._final = final_url
        self.opened = []

    def open(self, request, timeout=None):
        self.opened.append((request.full_url, timeout))
        return _FakeResponse(self._data, self._final)


class _ChunkedResponse:
    """Response that yields at most ``chunk_size`` bytes per read (short reads)."""

    def __init__(self, data, final_url, chunk_size):
        self._data = data
        self._final = final_url
        self._chunk = chunk_size
        self._pos = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def geturl(self):
        return self._final

    def read(self, n=-1):
        remaining = len(self._data) - self._pos
        if n is None or n < 0:
            n = remaining
        take = min(n, self._chunk, remaining)
        chunk = self._data[self._pos:self._pos + take]
        self._pos += len(chunk)
        return chunk


class _ChunkedOpener:
    def __init__(self, data, final_url, chunk_size):
        self._data = data
        self._final = final_url
        self._chunk = chunk_size
        self.opened = []

    def open(self, request, timeout=None):
        self.opened.append((request.full_url, timeout))
        return _ChunkedResponse(self._data, self._final, self._chunk)


# -----------------------------------------------------------------------------
# Magic-byte detection + validation.
# -----------------------------------------------------------------------------


def test_detect_image_type_known_formats():
    assert rb.detect_image_type(PNG) == "png"
    assert rb.detect_image_type(JPEG) == "jpg"
    assert rb.detect_image_type(WEBP) == "webp"
    assert rb.detect_image_type(GIF) == "gif"


def test_detect_image_type_rejects_junk_and_short():
    assert rb.detect_image_type(NOT_IMAGE) is None
    assert rb.detect_image_type(b"\x89PNG") is None  # too short
    assert rb.detect_image_type("not bytes") is None


def test_validate_image_bytes_accept_and_reject():
    assert rb.validate_image_bytes(PNG, max_bytes=1_000_000) == "png"
    _raises(FoundryError, rb.validate_image_bytes, NOT_IMAGE, max_bytes=1_000_000)
    _raises(FoundryError, rb.validate_image_bytes, PNG, max_bytes=4)  # over cap


# -----------------------------------------------------------------------------
# Redirect-safe, allowlisted download (SSRF / exfiltration defence).
# -----------------------------------------------------------------------------


def test_redirect_handler_blocks_off_allowlist():
    handler = rb._AllowlistRedirectHandler()
    req = urllib.request.Request("https://learn.microsoft.com/a")
    headers = http.client.HTTPMessage()
    # Redirect that would leave the allowlist must raise.
    _raises(
        FoundryError,
        handler.redirect_request,
        req,
        None,
        302,
        "Found",
        headers,
        "https://evil.example/x",
    )
    # Redirect that stays on the allowlist is permitted (returns a Request).
    allowed = handler.redirect_request(
        req, None, 302, "Found", headers, "https://learn.microsoft.com/b"
    )
    assert allowed is not None


def test_download_allowlisted_image_success():
    opener = _FakeOpener(PNG, "https://learn.microsoft.com/final.png")
    data, ext = rb.download_allowlisted_image(
        "https://learn.microsoft.com/i.png", timeout=5, max_bytes=1_000_000, opener=opener
    )
    assert ext == "png"
    assert data == PNG


def test_download_rejects_non_allowlisted_input_and_scheme():
    opener = _FakeOpener(PNG, "https://learn.microsoft.com/final.png")
    _raises(
        FoundryError,
        rb.download_allowlisted_image,
        "https://evil.example/i.png",
        timeout=5,
        max_bytes=1_000_000,
        opener=opener,
    )
    _raises(
        FoundryError,
        rb.download_allowlisted_image,
        "file:///etc/passwd",
        timeout=5,
        max_bytes=1_000_000,
        opener=opener,
    )


def test_download_rejects_off_allowlist_final_url():
    # Even if the requested host is allowlisted, a redirect that lands off the
    # allowlist (reflected in geturl) must be rejected.
    opener = _FakeOpener(PNG, "https://evil.example/final.png")
    _raises(
        FoundryError,
        rb.download_allowlisted_image,
        "https://learn.microsoft.com/i.png",
        timeout=5,
        max_bytes=1_000_000,
        opener=opener,
    )


def test_download_rejects_oversize_and_bad_bytes():
    big = _FakeOpener(PNG, "https://learn.microsoft.com/final.png")
    _raises(
        FoundryError,
        rb.download_allowlisted_image,
        "https://learn.microsoft.com/i.png",
        timeout=5,
        max_bytes=4,
        opener=big,
    )
    junk = _FakeOpener(NOT_IMAGE, "https://learn.microsoft.com/final.png")
    _raises(
        FoundryError,
        rb.download_allowlisted_image,
        "https://learn.microsoft.com/i.png",
        timeout=5,
        max_bytes=1_000_000,
        opener=junk,
    )


def test_download_accumulates_short_reads():
    # A socket that only yields 3 bytes per read must still reassemble the full
    # image via the loop-read (not a truncated buffer).
    opener = _ChunkedOpener(PNG, "https://learn.microsoft.com/final.png", chunk_size=3)
    data, ext = rb.download_allowlisted_image(
        "https://learn.microsoft.com/i.png", timeout=5, max_bytes=1_000_000, opener=opener
    )
    assert ext == "png"
    assert data == PNG  # fully reassembled across many short reads


def test_download_rejects_oversize_delivered_in_short_reads():
    # An over-cap payload trickled in small chunks must STILL be caught by the cap:
    # the loop reads at most max_bytes+1 bytes, which is enough to detect over-cap.
    big = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50  # 58 bytes
    opener = _ChunkedOpener(big, "https://learn.microsoft.com/final.png", chunk_size=4)
    _raises(
        FoundryError,
        rb.download_allowlisted_image,
        "https://learn.microsoft.com/i.png",
        timeout=5,
        max_bytes=10,  # cap below the payload -> must reject even via short reads
        opener=opener,
    )


def test_download_rejects_denylisted_image_url():
    saved = os.environ.get("IMAGE_URL_DENYLIST")
    try:
        os.environ["IMAGE_URL_DENYLIST"] = "tracker-pixel, badpath"
        opener = _FakeOpener(PNG, "https://learn.microsoft.com/final.png")
        # Allowlisted host but the URL contains a denylisted substring -> refused
        # BEFORE any network call (the opener is never opened).
        _raises(
            FoundryError,
            rb.download_allowlisted_image,
            "https://learn.microsoft.com/badpath/x.png",
            timeout=5,
            max_bytes=1_000_000,
            opener=opener,
        )
        assert opener.opened == []
        # Unset -> not blocked (default behaviour unchanged).
        os.environ.pop("IMAGE_URL_DENYLIST", None)
        data, ext = rb.download_allowlisted_image(
            "https://learn.microsoft.com/badpath/x.png",
            timeout=5,
            max_bytes=1_000_000,
            opener=opener,
        )
        assert ext == "png"
    finally:
        if saved is None:
            os.environ.pop("IMAGE_URL_DENYLIST", None)
        else:
            os.environ["IMAGE_URL_DENYLIST"] = saved


# -----------------------------------------------------------------------------
# Shortcode-safe quoting + figure rendering.
# -----------------------------------------------------------------------------


def test_shortcode_safe_strips_dangerous_chars():
    out = rb.shortcode_safe('he said "hi" <b>{x}</b> `code`')
    for char in ('"', "<", ">", "{", "}", "`"):
        assert char not in out


def test_figure_shortcode_format():
    out = rb.figure_shortcode(src="/images/post/body-1.png", alt="alt", caption="cap")
    assert out == '{{< figure src="/images/post/body-1.png" alt="alt" caption="cap" >}}{{< /figure >}}'


def test_normalise_placeholder():
    assert rb.normalise_placeholder("{{img:a_1}}") == "{{img:a_1}}"
    assert rb.normalise_placeholder("a1") == "{{img:a1}}"
    assert rb.normalise_placeholder("nope nope") is None


# -----------------------------------------------------------------------------
# Markdown rewriting.
# -----------------------------------------------------------------------------


def test_rewrite_markdown_replaces_and_strips():
    body = "Intro.\n\n{{img:a}}\n\nMiddle.\n\n{{img:b}}\n\nEnd.\n"
    replacements = {"{{img:a}}": '{{< figure src="/images/p/body-1.png" >}}{{< /figure >}}'}
    out = rb.rewrite_markdown(body, replacements)
    assert '{{< figure src="/images/p/body-1.png" >}}{{< /figure >}}' in out
    assert "{{img:a}}" not in out  # replaced
    assert "{{img:b}}" not in out  # unresolved -> stripped
    assert "\n\n\n" not in out


def test_rewrite_markdown_renders_repeated_placeholder_everywhere():
    # A placeholder used twice renders the figure at BOTH occurrences (chosen
    # behaviour: replace-all), leaving no raw token behind.
    body = "Intro {{img:a}} medio.\n\nY otra vez {{img:a}} al final.\n"
    figure = '{{< figure src="/images/p/body-1.png" alt="a" >}}{{< /figure >}}'
    out = rb.rewrite_markdown(body, {"{{img:a}}": figure})
    assert out.count("{{< figure") == 2
    assert "{{img:a}}" not in out


# -----------------------------------------------------------------------------
# Per-image resolution (AI + source), with mocks.
# -----------------------------------------------------------------------------


def test_resolve_image_ai_success_writes_file():
    with tempfile.TemporaryDirectory() as tmp:
        images_dir = os.path.join(tmp, "post")
        client = FakeImageClient(data=PNG)
        shortcode = rb.resolve_image(
            {"placeholder": "{{img:d}}", "type": "ai", "alt": "a", "caption": "c", "prompt_en": "robot"},
            1,
            slug="post",
            images_dir=images_dir,
            image_client=client,
            downloader=_make_downloader(),
            size="1024x1024",
            max_bytes=1_000_000,
            download_timeout=5,
        )
        assert shortcode is not None
        assert 'src="/images/post/body-1.png"' in shortcode
        assert os.path.isfile(os.path.join(images_dir, "body-1.png"))
        assert client.calls and client.calls[0][0].startswith("robot")


def test_resolve_image_ai_failure_returns_none():
    with tempfile.TemporaryDirectory() as tmp:
        client = FakeImageClient(error=FoundryError("boom"))
        result = rb.resolve_image(
            {"placeholder": "{{img:d}}", "type": "ai", "alt": "a", "caption": "c", "prompt_en": "x"},
            1,
            slug="post",
            images_dir=os.path.join(tmp, "post"),
            image_client=client,
            downloader=_make_downloader(),
            size="1024x1024",
            max_bytes=1_000_000,
            download_timeout=5,
        )
        assert result is None
        # No image client at all also fails open.
        assert (
            rb.resolve_image(
                {"placeholder": "{{img:d}}", "type": "ai", "alt": "a", "caption": "c", "prompt_en": "x"},
                1,
                slug="post",
                images_dir=os.path.join(tmp, "post"),
                image_client=None,
                downloader=_make_downloader(),
                size="1024x1024",
                max_bytes=1_000_000,
                download_timeout=5,
            )
            is None
        )


def test_resolve_image_source_success_has_attribution():
    with tempfile.TemporaryDirectory() as tmp:
        images_dir = os.path.join(tmp, "post")
        shortcode = rb.resolve_image(
            {
                "placeholder": "{{img:s}}",
                "type": "source",
                "alt": "diagrama",
                "caption": "pie",
                "source_url": "https://learn.microsoft.com/dotnet/article",
                "image_url": "https://learn.microsoft.com/img.png",
            },
            2,
            slug="post",
            images_dir=images_dir,
            image_client=None,
            downloader=_make_downloader(result=(PNG, "png")),
            size="1024x1024",
            max_bytes=1_000_000,
            download_timeout=5,
        )
        assert shortcode is not None
        assert 'src="/images/post/source-2.png"' in shortcode
        assert "Fuente: [learn.microsoft.com](https://learn.microsoft.com/dotnet/article)" in shortcode
        assert os.path.isfile(os.path.join(images_dir, "source-2.png"))


def test_resolve_image_source_failure_and_offlist():
    with tempfile.TemporaryDirectory() as tmp:
        images_dir = os.path.join(tmp, "post")
        # Download blocked -> None (placeholder will be removed).
        assert (
            rb.resolve_image(
                {
                    "placeholder": "{{img:s}}",
                    "type": "source",
                    "alt": "a",
                    "caption": "c",
                    "source_url": "https://learn.microsoft.com/a",
                    "image_url": "https://learn.microsoft.com/i.png",
                },
                1,
                slug="post",
                images_dir=images_dir,
                image_client=None,
                downloader=_make_downloader(error=FoundryError("blocked")),
                size="1024x1024",
                max_bytes=1_000_000,
                download_timeout=5,
            )
            is None
        )
        # Off-allowlist image_url -> None without ever calling the downloader.
        assert (
            rb.resolve_image(
                {
                    "placeholder": "{{img:s}}",
                    "type": "source",
                    "alt": "a",
                    "caption": "c",
                    "source_url": "https://learn.microsoft.com/a",
                    "image_url": "https://evil.example/i.png",
                },
                1,
                slug="post",
                images_dir=images_dir,
                image_client=None,
                downloader=_make_downloader(result=(PNG, "png")),
                size="1024x1024",
                max_bytes=1_000_000,
                download_timeout=5,
            )
            is None
        )


# -----------------------------------------------------------------------------
# End-to-end process() rewrite + spec loading + no-op behaviour.
# -----------------------------------------------------------------------------


def test_process_rewrites_post_fail_open_per_image():
    with tempfile.TemporaryDirectory() as tmp:
        post_path = os.path.join(tmp, "post.md")
        body = (
            "---\ntitle: X\n---\n\nIntro.\n\n{{img:ai}}\n\nMedio.\n\n{{img:src}}\n\nFin.\n"
        )
        with open(post_path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)

        spec = {
            "slug": "post",
            "images": [
                {"placeholder": "{{img:ai}}", "type": "ai", "alt": "a", "caption": "c", "prompt_en": "p"},
                {
                    "placeholder": "{{img:src}}",
                    "type": "source",
                    "alt": "a",
                    "caption": "c",
                    "source_url": "https://learn.microsoft.com/a",
                    "image_url": "https://learn.microsoft.com/i.png",
                },
            ],
        }
        count = rb.process(
            spec,
            post_path=post_path,
            slug="post",
            static_images_dir=os.path.join(tmp, "static", "images"),
            image_client=FakeImageClient(data=PNG),
            downloader=_make_downloader(error=FoundryError("blocked")),  # source fails
            size="1024x1024",
            max_bytes=1_000_000,
            download_timeout=5,
        )
        assert count == 1  # only the AI image succeeded
        with open(post_path, "r", encoding="utf-8") as handle:
            out = handle.read()
        assert 'src="/images/post/body-1.png"' in out  # AI figure placed
        assert "{{img:ai}}" not in out
        assert "{{img:src}}" not in out  # failed source -> placeholder removed
        assert os.path.isfile(os.path.join(tmp, "static", "images", "post", "body-1.png"))


def test_load_spec_absent_empty_malformed():
    assert rb.load_spec("") is None
    with tempfile.TemporaryDirectory() as tmp:
        empty = os.path.join(tmp, "empty.json")
        with open(empty, "w", encoding="utf-8") as handle:
            handle.write("   ")
        assert rb.load_spec(empty) is None

        bad = os.path.join(tmp, "bad.json")
        with open(bad, "w", encoding="utf-8") as handle:
            handle.write("{ not json")
        assert rb.load_spec(bad) is None

        good = os.path.join(tmp, "good.json")
        with open(good, "w", encoding="utf-8") as handle:
            json.dump({"slug": "p", "images": []}, handle)
        assert rb.load_spec(good) == {"slug": "p", "images": []}


def test_main_noop_when_spec_empty():
    saved = {key: os.environ.get(key) for key in ("BODY_IMAGES_FILE", "POST_PATH", "POST_SLUG")}
    try:
        os.environ.pop("POST_PATH", None)
        os.environ.pop("POST_SLUG", None)
        with tempfile.TemporaryDirectory() as tmp:
            spec_path = os.path.join(tmp, "spec.json")
            with open(spec_path, "w", encoding="utf-8") as handle:
                json.dump({"slug": "p", "images": []}, handle)
            os.environ["BODY_IMAGES_FILE"] = spec_path
            # No post exists; an empty spec must be a silent no-op (returns None).
            assert rb.main() is None
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def test_main_hard_fails_on_unresolvable_post():
    # A NON-empty spec whose post cannot be resolved is a genuine misconfiguration
    # and must hard-fail via fail() (SystemExit), not silently succeed.
    saved = {key: os.environ.get(key) for key in ("BODY_IMAGES_FILE", "POST_PATH", "POST_SLUG")}
    try:
        os.environ.pop("POST_PATH", None)
        os.environ.pop("POST_SLUG", None)
        with tempfile.TemporaryDirectory() as tmp:
            spec_path = os.path.join(tmp, "spec.json")
            with open(spec_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "slug": "p",
                        "post_path": os.path.join(tmp, "does-not-exist.md"),
                        "images": [
                            {"placeholder": "{{img:a}}", "type": "ai", "prompt_en": "x"}
                        ],
                    },
                    handle,
                )
            os.environ["BODY_IMAGES_FILE"] = spec_path
            _raises(SystemExit, rb.main)
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


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
