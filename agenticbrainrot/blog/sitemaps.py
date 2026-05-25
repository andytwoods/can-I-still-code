import datetime
from pathlib import Path

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .views import _cached_meta

POSTS_DIR = Path(__file__).parent / "posts"


class BlogPostSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return [p.stem for p in sorted(POSTS_DIR.glob("*.md"), reverse=True)]

    def location(self, item):
        return reverse("blog:post_detail", kwargs={"slug": item})

    def lastmod(self, item):
        path = POSTS_DIR / f"{item}.md"
        meta = _cached_meta(path)
        raw_date = meta.get("date")
        if raw_date:
            try:
                return datetime.date.fromisoformat(str(raw_date))
            except (ValueError, TypeError):
                pass
        return None
