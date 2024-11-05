from dateutil import parser
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.utils import timezone

from ukgrantmaking.filters.grantmakers import GrantmakerFilter
from ukgrantmaking.models import Funder
from ukgrantmaking.models.funder import FunderTag


@login_required
def index(request):
    filters = GrantmakerFilter(request.GET, queryset=Funder.objects.all())
    paginator = Paginator(filters.qs, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(
        request, "grantmakers/index.html.j2", {"page_obj": page_obj, "filters": filters}
    )


@login_required
def detail(request, org_id):
    funder = Funder.objects.get(org_id=org_id)
    return render(request, "grantmakers/detail.html.j2", {"object": funder})


@login_required
def htmx_edit_note(request, org_id, note_id=None):
    if not request.htmx:
        return HttpResponseBadRequest("This view is only accessible via htmx")
    funder = Funder.objects.get(org_id=org_id)
    if note_id:
        note = funder.notes.get(id=note_id)
        note.note = request.POST["note"]
        note.save()
    else:
        funder.notes.create(note=request.POST["note"], added_by=request.user.username)
    return render(request, "grantmakers/partials/notes.html.j2", {"object": funder})


@login_required
def htmx_tags_edit(request, org_id):
    if not request.htmx:
        return HttpResponseBadRequest("This view is only accessible via htmx")
    funder = Funder.objects.get(org_id=org_id)
    context = {"object": funder, "tags": FunderTag.objects.all(), "edit": True}
    if request.method == "POST":
        funder.tags.set(FunderTag.objects.filter(tag__in=request.POST.getlist("tags")))
        context["edit"] = False
    return render(
        request,
        "grantmakers/partials/tags.html.j2",
        context,
    )


@login_required
def htmx_edit_funder(request, org_id):
    if not request.htmx:
        return HttpResponseBadRequest("This view is only accessible via htmx")
    funder = Funder.objects.get(org_id=org_id)
    action = request.POST.get("action")
    if action == "exclude":
        funder.included = False
    elif action == "include":
        funder.included = True
    elif action == "doesnt_make_grants_to_individuals":
        funder.makes_grants_to_individuals = False
    elif action == "makes_grants_to_individuals":
        funder.makes_grants_to_individuals = True
    elif action == "marked_as_checked":
        if funder.latest_year:
            funder.latest_year.checked_on = timezone.now()
            funder.latest_year.checked_by = request.user.username
            funder.latest_year.save()
    elif action == "update_segment":
        funder.segment = request.POST.get("segment")
    elif action == "change_name":
        new_name = request.POST.get("name")
        if not new_name:
            new_name = None
        funder.name_manual = new_name
    funder.save()

    template = "grantmakers/partials/funderstatus.html.j2"
    if request.headers.get("HX-Target") == "funder-header":
        template = "grantmakers/partials/funderheader.html.j2"

    return render(
        request, template, {"object": Funder.objects.get(org_id=funder.org_id)}
    )


@login_required
def htmx_edit_funderyear(request, org_id, funderyear_id=None):
    if not request.htmx:
        return HttpResponseBadRequest("This view is only accessible via htmx")
    funder = Funder.objects.get(org_id=org_id)
    funder_year = None
    funder_year_py = None
    if funderyear_id:
        funder_year = funder.funderyear_set.get(id=funderyear_id)
        funder_year_py = (
            funder.funderyear_set.filter(
                financial_year_end__lt=funder_year.financial_year_end
            )
            .order_by("-financial_year_end")
            .first()
        )

        if request.method == "DELETE":
            funder_year.delete()
            return HttpResponse("")
    else:
        funder_year = funder.funderyear_set.create(financial_year_end=timezone.now())

    context = {
        "object": funder,
        "funder_year": funder_year,
        "funder_year_py": funder_year_py,
        "edit": True,
    }
    if request.method == "POST":
        funder_year.financial_year_end = parser.parse(request.POST.get("fye-cy"))
        for field in funder_year.editable_fields():
            value = request.POST.get(f"{field['name']}-cy")
            if value is not None and value != "":
                value = value.replace(",", "")
                setattr(funder_year, field["manual"].name, value)
            else:
                setattr(funder_year, field["manual"].name, None)
        funder_year.checked_on = timezone.now()
        funder_year.checked_by = request.user.username
        if "note" in request.POST:
            funder_year.notes = request.POST.get("note")
        funder_year.save()
        context["funder_year"] = funder.funderyear_set.get(id=funder_year.id)

        if request.POST.get("py-id"):
            context["funder_year_py"] = funder.funderyear_set.get(
                id=request.POST.get("py-id")
            )

        if context["funder_year_py"]:
            if "fye-py" in request.POST:
                context["funder_year_py"].financial_year_end = parser.parse(
                    request.POST.get("fye-py")
                )
            for field in funder_year.editable_fields():
                value = request.POST.get(f"{field['name']}-py")
                if value is not None and value != "":
                    value = value.replace(",", "")
                    setattr(context["funder_year_py"], field["manual"].name, value)
                else:
                    setattr(context["funder_year_py"], field["manual"].name, None)
            context["funder_year_py"].checked_on = timezone.now()
            context["funder_year_py"].checked_by = request.user.username
            context["funder_year_py"].save()
            context["funder_year_py"] = funder.funderyear_set.get(
                id=context["funder_year_py"].id
            )
        context["edit"] = False
    return render(
        request,
        "grantmakers/partials/funderyear.html.j2",
        context,
    )
