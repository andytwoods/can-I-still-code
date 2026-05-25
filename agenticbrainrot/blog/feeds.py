import datetime
from pathlib import Path

from django.contrib.syndication.views import Feed
from django.urls import reverse

from .views import _cached_html, _cached_meta

POSTS_DIR = Path(__file__).parent / "posts"


class BlogFeed(Feed):
    title = "Can I Still Code – Blog"
    description = "Research notes, data updates, and methodology from the Can I Still Code citizen-science study."

    def link(self):
        return reverse("blog:post_list")

    def items(self):
        return [_cached_meta(p) for p in sorted(POSTS_DIR.glob("*.md"), reverse=True)]

    def item_title(self, item):
        return item.get("title", "")

    def item_description(self, item):
        return item.get("summary", "")

    def item_link(self, item):
        return reverse("blog:post_detail", kwargs={"slug": item["slug"]})

    def item_pubdate(self, item):
        raw = item.get("date")
        if raw:
            try:
                d = datetime.date.fromisoformat(str(raw))
                return datetime.datetime(d.year, d.month, d.day)
            except (ValueError, TypeError):
                pass
        return None

    def item_author_name(self, item):
        return item.get("author", "")
