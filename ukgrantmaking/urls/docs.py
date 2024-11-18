from django.urls import path

from ukgrantmaking.views.docs import detail, index

app_name = "docs"

urlpatterns = [
    path(
        "",
        index,
        name="index",
    ),
    path(
        "<path:doc_path>",
        detail,
        name="detail",
    ),
]
