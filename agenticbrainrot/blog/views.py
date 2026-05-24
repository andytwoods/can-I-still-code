from pathlib import Path

import markdown as md
from django.core.cache import cache
from django.http import Http404
from django.shortcuts import render

POSTS_DIR = Path(__file__).parent / "posts"


def _parse_frontmatter(content):
    """Parse ---\\nkey: value\\n--- header. Returns (meta_dict, body)."""
    if not content.startswith("---\n"):
        return {}, content
    try:
        end = content.index("\n---\n", 4)
    except ValueError:
        return {}, content
    meta = {}
    for line in content[4:end].splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            meta[key.strip().lower()] = val.strip()
    return meta, content[end + 5:]


def _cached_meta(path: Path) -> dict:
    mtime = path.stat().st_mtime
    key = f"blog:meta:{path.stem}:{mtime}"
    meta = cache.get(key)
    if meta is None:
        raw = path.read_text(encoding="utf-8")
        meta, _ = _parse_frontmatter(raw)
        meta["slug"] = path.stem
        cache.set(key, meta, timeout=None)
    return meta


def _cached_html(path: Path) -> str:
    mtime = path.stat().st_mtime
    key = f"blog:html:{path.stem}:{mtime}"
    html = cache.get(key)
    if html is None:
        raw = path.read_text(encoding="utf-8")
        _, body = _parse_frontmatter(raw)
        html = md.markdown(
            body,
            extensions=["fenced_code", "tables", "toc", "attr_list"],
            output_format="html",
        )
        cache.set(key, html, timeout=None)
    return html


def post_list(request):
    posts = [_cached_meta(p) for p in sorted(POSTS_DIR.glob("*.md"), reverse=True)]
    return render(request, "blog/post_list.html", {"posts": posts})


def post_detail(request, slug):
    path = POSTS_DIR / f"{slug}.md"
    if not path.exists():
        raise Http404
    return render(request, "blog/post_detail.html", {
        "meta": _cached_meta(path),
        "content": _cached_html(path),
    })
