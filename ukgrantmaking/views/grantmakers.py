from decimal import Decimal

from dateutil import parser
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
)
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.text import slugify

from ukgrantmaking.filters.grantmakers import GrantmakerFilter
from ukgrantmaking.models import CleaningStatus, FinancialYear, Funder, FunderTag
from ukgrantmaking.models.funder_utils import RecordStatus
from ukgrantmaking.models.funder_year import FunderYear


@login_required
def index(request):
    filters = GrantmakerFilter(
        request.GET,
        queryset=Funder.objects.all()
        .select_related("latest_year", "latest_year__checked_by")
        .prefetch_related("tags"),
    )
    paginator = Paginator(filters.qs, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(
        request, "grantmakers/index.html.j2", {"page_obj": page_obj, "filters": filters}
    )


@login_required
def task_index(request):
    current_fy = FinancialYear.objects.get(current=True)
    cleaning_tasks = CleaningStatus.objects.filter(
        type=CleaningStatus.CleaningStatusType.GRANTMAKER
    )
    base_qs = FunderYear.objects.filter(
        funder_financial_year__financial_year=current_fy
    ).select_related(
        "funder_financial_year__funder", "funder_financial_year__financial_year"
    )
    statuses = {task.id: task.get_status(base_qs) for task in cleaning_tasks}
    return render(
        request,
        "grantmakers/task/index.html.j2",
        {"object_list": cleaning_tasks, "statuses": statuses},
    )


@login_required
def task_detail(request, task_id):
    current_fy = FinancialYear.objects.get(current=True)
    try:
        cleaning_task = CleaningStatus.objects.filter(
            type=CleaningStatus.CleaningStatusType.GRANTMAKER
        ).get(id=task_id)
    except CleaningStatus.DoesNotExist:
        raise Http404("Task not found")
    base_qs = FunderYear.objects.filter(
        funder_financial_year__financial_year=current_fy
    ).select_related(
        "funder_financial_year__funder", "funder_financial_year__financial_year"
    )

    exclude_cleaned = "exclude_cleaned" in request.GET

    qs = cleaning_task.run(base_qs, exclude_cleaned=exclude_cleaned)
    status = cleaning_task.get_status(base_qs)
    paginator = Paginator(qs, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        "grantmakers/task/detail.html.j2",
        {
            "page_obj": page_obj,
            "object": cleaning_task,
            "current_fy": current_fy,
            "status": status,
        },
    )


@login_required
def detail(request, org_id):
    funder = get_object_or_404(Funder, org_id=org_id)
    return render(request, "grantmakers/detail.html.j2", {"object": funder})


@login_required
def htmx_edit_note(request, org_id, note_id=None):
    if not request.htmx:
        return HttpResponseBadRequest("This view is only accessible via htmx")
    funder = get_object_or_404(Funder, org_id=org_id)
    if request.method == "POST":
        note_content = request.POST.get("note")
        if note_id:
            note = funder.notes.get(id=note_id)
            note.note = note_content
            note.save()
            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=ContentType.objects.get_for_model(funder).pk,
                object_id=funder.pk,
                object_repr=funder.name,
                action_flag=CHANGE,
                change_message=f"Updated note {note.id}",
            )
        else:
            note = funder.notes.create(note=note_content, added_by=request.user)
            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=ContentType.objects.get_for_model(funder).pk,
                object_id=funder.pk,
                object_repr=funder.name,
                action_flag=CHANGE,
                change_message=f"Added note {note.id}",
            )
    return render(request, "grantmakers/partials/notes.html.j2", {"object": funder})


@login_required
def htmx_tags_edit(request, org_id):
    if not request.htmx:
        return HttpResponseBadRequest("This view is only accessible via htmx")
    funder = get_object_or_404(Funder, org_id=org_id)
    context = {"object": funder, "tags": FunderTag.objects.all(), "edit": True}
    if request.method == "POST":
        new_tags = []
        for tag in request.POST.getlist("tags"):
            if not tag:
                continue
            new_tag, _ = FunderTag.objects.get_or_create(
                slug=slugify(tag), defaults={"tag": tag}
            )
            new_tags.append(new_tag)
        funder.tags.set(new_tags)
        funder.save()
        LogEntry.objects.log_action(
            user_id=request.user.id,
            content_type_id=ContentType.objects.get_for_model(funder).pk,
            object_id=funder.pk,
            object_repr=funder.name,
            action_flag=CHANGE,
            change_message="Updated tags",
        )
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
    if not request.method == "POST":
        return HttpResponseNotAllowed(["POST"], "This view only accepts POST requests")
    funder = get_object_or_404(Funder, org_id=org_id)
    action = request.POST.get("action")
    change_message = None
    if action == "exclude":
        funder.included = False
        change_message = "Marked as excluded"
    elif action == "include":
        funder.included = True
        change_message = "Marked as included"
    elif action == "doesnt_make_grants_to_individuals":
        funder.makes_grants_to_individuals = False
        change_message = "Marked as not making grants to individuals"
    elif action == "makes_grants_to_individuals":
        funder.makes_grants_to_individuals = True
        change_message = "Marked as making grants to individuals"
    elif action == "marked_as_checked":
        if funder.latest_year:
            funder.latest_year.checked = RecordStatus.CHECKED
            funder.latest_year.checked_on = timezone.now()
            funder.latest_year.checked_by = request.user
            funder.latest_year.save()
            change_message = (
                f"Marked as checked for {funder.latest_year.financial_year.fy}"
            )
    elif action == "marked_as_unchecked":
        if funder.latest_year:
            funder.latest_year.checked = RecordStatus.UNCHECKED
            funder.latest_year.checked_on = timezone.now()
            funder.latest_year.checked_by = request.user
            funder.latest_year.save()
            change_message = (
                f"Marked as unchecked for {funder.latest_year.financial_year.fy}"
            )
    elif action == "mark_for_review":
        if funder.latest_year:
            funder.latest_year.checked = RecordStatus.FOR_REVIEW
            funder.latest_year.checked_on = timezone.now()
            funder.latest_year.checked_by = request.user
            funder.latest_year.save()
            change_message = (
                f"Marked for review for {funder.latest_year.financial_year.fy}"
            )
    elif action == "update_segment":
        old_segment = funder.segment
        funder.segment = request.POST.get("segment")
        change_message = f"Updated segment '{old_segment}' to '{funder.segment}'"
    elif action == "change_name":
        old_name = funder.name
        new_name = request.POST.get("name")
        if not new_name:
            new_name = None
        funder.name_manual = new_name
        change_message = f"Updated name from '{old_name}' to '{new_name}'"
    if change_message:
        LogEntry.objects.log_action(
            user_id=request.user.id,
            content_type_id=ContentType.objects.get_for_model(funder).pk,
            object_id=funder.pk,
            object_repr=funder.name,
            action_flag=CHANGE,
            change_message=change_message,
        )
    funder.save()

    template = "grantmakers/partials/funderstatus.html.j2"
    if request.headers.get("HX-Target") == "funder-header":
        template = "grantmakers/partials/funderheader.html.j2"

    return render(
        request, template, {"object": Funder.objects.get(org_id=funder.org_id)}
    )


def edit_funderyear(funder_year: FunderYear, request, suffix: str = "cy"):
    changed_values = []
    if request.POST.get(f"fye-{suffix}"):
        existing_fy = funder_year.financial_year_end
        funder_year.financial_year_end = parser.parse(request.POST.get(f"fye-{suffix}"))
        if existing_fy != funder_year.financial_year_end:
            changed_values.append(
                f"Financial year end from {existing_fy} to {funder_year.financial_year_end}"
            )

    funder = funder_year.funder_financial_year.funder

    for field in funder_year.editable_fields():
        current_value = getattr(funder_year, field.name)
        value = request.POST.get(f"{field.name}-{suffix}")
        if value is not None and value != "":
            value = Decimal(value.replace(",", ""))
            setattr(funder_year, field.manual.name, value)
        else:
            setattr(funder_year, field.manual.name, None)
        new_value = getattr(funder_year, field.manual.name)
        if current_value != new_value:
            changed_values.append(f"{field.name} from {current_value} to {new_value}")

    if "note" in request.POST:
        existing_value = funder_year.notes
        funder_year.notes = request.POST.get("note")
        if existing_value != funder_year.notes:
            changed_values.append(f"Note from {existing_value} to {funder_year.notes}")

    if changed_values:
        funder_year.funder_financial_year.checked_on = timezone.now()
        funder_year.funder_financial_year.checked_by = request.user
        funder_year.save()

        LogEntry.objects.log_action(
            user_id=request.user.id,
            content_type_id=ContentType.objects.get_for_model(funder).pk,
            object_id=funder.pk,
            object_repr=f"{funder.name} {funder_year.financial_year_end}",
            action_flag=CHANGE,
            change_message=(
                [f"Edited funder year {funder_year.financial_year_end}"]
                + changed_values
            ),
        )
    funder_year.refresh_from_db()
    return funder_year


@login_required
def htmx_edit_funderyear(request, org_id, funderyear_id=None):
    if not request.htmx:
        return HttpResponseBadRequest("This view is only accessible via htmx")
    funder = get_object_or_404(Funder, org_id=org_id)
    funder_year = None
    funder_year_py = None
    if funderyear_id:
        funder_year = FunderYear.objects.filter(
            funder_financial_year__funder=funder, id=funderyear_id
        ).first()
        if not funder_year:
            return HttpResponseBadRequest("Invalid funderyear_id")
        funder_year_py = (
            FunderYear.objects.filter(
                funder_financial_year__funder=funder,
                financial_year_end__lt=funder_year.financial_year_end,
            )
            .order_by("-financial_year_end")
            .first()
        )

        if request.method == "DELETE":
            funder_year.delete()
            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=ContentType.objects.get_for_model(funder).pk,
                object_id=funder.pk,
                object_repr=f"{funder.name} {funder_year.financial_year_end}",
                action_flag=CHANGE,
                change_message=f"Deleted funder year {funder_year.financial_year_end}",
            )
            return HttpResponse("")
    else:
        funder_financial_year = funder.funder_financial_years.filter(
            financial_year__current=True
        ).first()
        if funder_financial_year:
            funder_year = funder_financial_year.funder_years.create(
                financial_year_end=funder_financial_year.financial_year.grants_end_date
            )
            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=ContentType.objects.get_for_model(funder).pk,
                object_id=funder.pk,
                object_repr=f"{funder.name} {funder_year.financial_year_end}",
                action_flag=CHANGE,
                change_message=f"Deleted funder year {funder_year.financial_year_end}",
            )

    context = {
        "object": funder,
        "funder_year": funder_year,
        "funder_year_py": funder_year_py,
        "edit": True,
    }
    if request.method == "POST":
        if request.POST.get("action") == "cancel":
            context["edit"] = False
        else:
            context["funder_year"] = edit_funderyear(funder_year, request, suffix="cy")

            if request.POST.get("py-id"):
                context["funder_year_py"] = FunderYear.objects.filter(
                    funder_financial_year__funder=funder, id=request.POST.get("py-id")
                ).first()

            if context["funder_year_py"]:
                context["funder_year_py"] = edit_funderyear(
                    context["funder_year_py"], request, suffix="py"
                )
            context["edit"] = False
    return render(
        request,
        "grantmakers/partials/funderyear.html.j2",
        context,
    )
