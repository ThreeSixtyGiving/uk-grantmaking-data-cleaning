import dataclasses
import os

import markdown
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import render

DOCS_DIR = os.path.join(settings.BASE_DIR, "docs")


@dataclasses.dataclass
class Doc:
    location: str
    filename: str
    content: str = None
    meta: dict = None
    toc: str = None

    @property
    def title(self):
        return (
            self.filename.replace(".md", "").replace("-", " ").replace("_", " ").title()
        )

    @property
    def path(self):
        return os.path.relpath(self.location, DOCS_DIR)

    @property
    def doc_path(self):
        return self.path.removesuffix(".md")

    def fetch(self):
        md = markdown.Markdown(
            extensions=[
                "fenced_code",
                "md_in_html",
                "tables",
                "abbr",
                "toc",
                "meta",
                "footnotes",
            ]
        )

        with open(self.location, "r", encoding="utf-8") as f:
            self.content = md.convert(f.read())
            self.meta = md.Meta
            self.toc = md.toc


def get_docs():
    for root, dirs, files in os.walk(DOCS_DIR):
        for file in files:
            if not file.endswith(".md"):
                continue
            yield Doc(location=os.path.join(root, file), filename=file)


def get_images():
    for root, dirs, files in os.walk(DOCS_DIR):
        for file in files:
            if not file.endswith(".png"):
                continue
            yield Doc(location=os.path.join(root, file), filename=file)


@login_required
def index(request):
    return render(request, "docs/index.html", context={"object_list": get_docs()})


@login_required
def detail(request, doc_path):
    if doc_path.endswith(".png"):
        for image in get_images():
            if os.path.normpath(image.path) == os.path.normpath(doc_path):
                with open(image.location, "rb") as f:
                    return HttpResponse(f.read(), content_type="image/png")
        raise Http404("Image not found")
    docs = list(get_docs())
    for doc in docs:
        if doc.doc_path == doc_path:
            doc.fetch()
            return render(request, "docs/detail.html", context={"object": doc})
    raise Http404("Doc not found")
