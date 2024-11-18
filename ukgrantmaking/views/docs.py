import dataclasses
import os

import markdown
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render

DOCS_DIR = os.path.join(settings.BASE_DIR, "docs")


@dataclasses.dataclass
class Doc:
    location: str
    filename: str

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

    @property
    def content(self):
        with open(self.location, "r") as f:
            return markdown.markdown(
                f.read(), extensions=["fenced_code", "md_in_html", "tables", "abbr"]
            )


def get_docs():
    for root, dirs, files in os.walk(DOCS_DIR):
        for file in files:
            if not file.endswith(".md"):
                continue
            yield Doc(location=os.path.join(root, file), filename=file)


@login_required
def index(request):
    return render(request, "docs/index.html", context={"object_list": get_docs()})


@login_required
def detail(request, doc_path):
    docs = list(get_docs())
    for doc in docs:
        if doc.doc_path == doc_path:
            return render(request, "docs/detail.html", context={"object": doc})
    raise Http404("Doc not found")
