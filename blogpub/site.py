"""Render posts and an index into a static site for GitHub Pages."""

from __future__ import annotations

import html
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from .pull import PostInfo

STYLE = """
body {
    max-width: 720px;
    margin: 3rem auto;
    padding: 0 1.5rem;
    font-family: Georgia, "Times New Roman", serif;
    color: #111;
    background: #fdfdfb;
    line-height: 1.5;
}
h1, h2 { font-weight: normal; }
a { color: #111; }
.post-date { color: #666; font-size: 0.9rem; }
.page-image {
    width: 100%;
    border: 1px solid #ddd;
    margin: 1.5rem 0;
    display: block;
}
ul.post-list { list-style: none; padding: 0; }
ul.post-list li { margin-bottom: 1.2rem; }
footer { margin-top: 4rem; color: #999; font-size: 0.85rem; }
"""


def slugify(name: str) -> str:
    """Turn a notebook name into a URL-safe slug fragment.

    Parameters
    ----------
    name : str
        Notebook name.

    Returns
    -------
    str
        Lowercase, hyphenated slug fragment (not guaranteed unique on its
        own -- see :func:`post_slug`).
    """
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "untitled"


def post_slug(post: PostInfo) -> str:
    """Build a unique, stable slug for a post's output filename.

    Includes a short UUID fragment so two notebooks with the same (or
    equivalent-once-slugified) name don't overwrite each other's output.

    Parameters
    ----------
    post : PostInfo
        The post to build a slug for.

    Returns
    -------
    str
        A unique slug, e.g. ``"my-notebook-a1b2c3d4"``.
    """
    return f"{slugify(post.name)}-{post.uuid[:8]}"


def _format_date(created_time_ms: str) -> str:
    try:
        dt = datetime.fromtimestamp(int(created_time_ms) / 1000, tz=timezone.utc)
        return dt.strftime("%B %-d, %Y")
    except (ValueError, OSError):
        return ""


def render_post(post: PostInfo, page_image_paths: list[str]) -> str:
    """Render a single post's HTML page.

    Parameters
    ----------
    post : PostInfo
        The notebook being rendered.
    page_image_paths : list of str
        Relative (from the post HTML file) paths to each page's PNG image.

    Returns
    -------
    str
        Full HTML document for this post.
    """
    title = html.escape(post.name)
    images_html = "\n".join(
        f'<img class="page-image" src="{path}" alt="Page {i + 1}">'
        for i, path in enumerate(page_image_paths)
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>{STYLE}</style>
</head>
<body>
<p><a href="../index.html">&larr; back</a></p>
<h1>{title}</h1>
<p class="post-date">{_format_date(post.created_time)}</p>
{images_html}
<footer>Written by hand, published from a reMarkable.</footer>
</body>
</html>
"""


def render_index(posts: list[PostInfo]) -> str:
    """Render the site index listing all posts, newest first.

    Parameters
    ----------
    posts : list of PostInfo
        All published posts.

    Returns
    -------
    str
        Full HTML document for the index page.
    """
    ordered = sorted(posts, key=lambda p: p.created_time, reverse=True)
    items = "\n".join(
        f'<li><a href="posts/{post_slug(p)}.html">{html.escape(p.name)}</a> '
        f'<span class="post-date">{_format_date(p.created_time)}</span></li>'
        for p in ordered
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Handwritten</title>
<style>{STYLE}</style>
</head>
<body>
<h1>Handwritten</h1>
<ul class="post-list">
{items}
</ul>
<footer>Written by hand, published from a reMarkable.</footer>
</body>
</html>
"""


def write_site(
    posts_with_pages: list[tuple[PostInfo, list[Path]]], docs_dir: Path
) -> None:
    """Write the full static site (index + posts + images) into a docs directory.

    Replaces the entire ``posts/`` and ``images/`` subdirectories on each
    run, so notebooks removed from the Blog folder don't linger as stale
    published pages.

    Parameters
    ----------
    posts_with_pages : list of (PostInfo, list of Path)
        Each post paired with its ordered page PNG paths.
    docs_dir : Path
        Output directory (e.g. a repo's ``docs/`` folder for GitHub Pages).
    """
    posts_dir = docs_dir / "posts"
    images_dir = docs_dir / "images"
    shutil.rmtree(posts_dir, ignore_errors=True)
    shutil.rmtree(images_dir, ignore_errors=True)
    posts_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)

    for post, page_paths in posts_with_pages:
        slug = post_slug(post)
        post_image_dir = images_dir / slug
        post_image_dir.mkdir(parents=True, exist_ok=True)

        relative_paths = []
        for i, src in enumerate(page_paths):
            dest = post_image_dir / f"page_{i:03d}.png"
            dest.write_bytes(src.read_bytes())
            relative_paths.append(f"../images/{slug}/page_{i:03d}.png")

        (posts_dir / f"{slug}.html").write_text(render_post(post, relative_paths))

    (docs_dir / "index.html").write_text(render_index([p for p, _ in posts_with_pages]))
