import csv
from decimal import Decimal
from io import TextIOWrapper

import requests
from dateutil import parser
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from ukgrantmaking.filters.grantmakers import GrantmakerFilter
from ukgrantmaking.forms.funder import FunderForm
from ukgrantmaking.forms.funder_upload import FunderUploadForm
from ukgrantmaking.models.cleaningstatus import CleaningStatus, CleaningStatusType
from ukgrantmaking.models.financial_years import FinancialYear, FinancialYearStatus
from ukgrantmaking.models.funder import Funder, FunderTag
from ukgrantmaking.models.funder_financial_year import FunderFinancialYear
from ukgrantmaking.models.funder_utils import RecordStatus
from ukgrantmaking.models.funder_year import FunderYear
from ukgrantmaking.utils.text import to_titlecase


@login_required
def index(request):
    filters = GrantmakerFilter(
        request.GET,
        queryset=Funder.objects.all()
        .select_related("current_year", "current_year__checked_by")
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
    cleaning_tasks = CleaningStatus.objects.filter(type=CleaningStatusType.GRANTMAKER)
    base_qs = FunderFinancialYear.objects.filter(
        financial_year=current_fy
    ).select_related("funder", "financial_year")
    statuses = {task.id: task.get_status(base_qs) for task in cleaning_tasks}
    return render(
        request,
        "grantmakers/task/index.html.j2",
        {"object_list": cleaning_tasks, "statuses": statuses},
    )


@login_required
def task_detail(request, task_id, filetype=None):
    current_fy = FinancialYear.objects.get(current=True)
    try:
        cleaning_task = CleaningStatus.objects.filter(
            type=CleaningStatusType.GRANTMAKER
        ).get(id=task_id)
    except CleaningStatus.DoesNotExist:
        raise Http404("Task not found")
    base_qs = FunderFinancialYear.objects.filter(
        financial_year=current_fy
    ).select_related("funder", "financial_year")

    exclude_cleaned = "exclude_cleaned" in request.GET

    qs = cleaning_task.run(base_qs, exclude_cleaned=exclude_cleaned)

    if filetype == "csv":
        now = timezone.now()
        response = HttpResponse(
            content_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="ukgrantmaking-cleaning-{cleaning_task.slug}-{now:%Y-%m-%d}.csv"'
            },
        )
        writer = csv.writer(response)
        headers = None
        for row in qs:
            if not headers:
                headers = [field.name for field in row._meta.fields]
                writer.writerow(headers)
            writer.writerow([getattr(row, field) for field in headers])

        return response

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
            "exclude_cleaned": exclude_cleaned,
        },
    )


@login_required
def detail(request, org_id):
    org_id = org_id.removesuffix("/")
    try:
        funder = Funder.objects.get(org_id=org_id)
        return render(request, "grantmakers/detail.html.j2", {"object": funder})
    except Funder.DoesNotExist:
        if request.method == "POST":
            form = FunderForm(request.POST)
            if form.is_valid():
                funder = form.save()
                LogEntry.objects.log_actions(
                    user_id=request.user.id,
                    queryset=[funder],
                    action_flag=CHANGE,
                    change_message="Created funder",
                )
                funder.update_from_ftc()
                funder.save()
                return HttpResponseRedirect(
                    reverse("grantmakers:detail", args=[org_id])
                )
            return render(
                request,
                "grantmakers/notfound.html.j2",
                {"org_id": org_id, "object": None, "form": form},
            )
        try:
            r = requests.get(
                "{api_url}/organisations/{organisation_id}".format(
                    api_url=settings.FTC_API_URL, organisation_id=org_id
                )
            )
            r.raise_for_status()
        except requests.HTTPError:
            raise Http404(f"Funder with org_id {org_id} not found")
        data = r.json()
        if data.get("success"):
            form = FunderForm(
                initial={
                    "org_id": data["result"]["id"],
                    "charity_number": data["result"]["charityNumber"],
                    "name_registered": data["result"]["name"],
                    "name_manual": to_titlecase(data["result"]["name"]),
                    # "segment": data["result"]["id"],
                    "included": True,
                    # "makes_grants_to_individuals": data["result"]["id"],
                    # "successor": data["result"]["id"],
                    # "status": data["result"]["id"],
                    "date_of_registration": data["result"]["dateRegistered"],
                    "date_of_removal": data["result"]["dateRemoved"],
                    "active": data["result"]["active"],
                    "activities": data["result"]["description"],
                    "website": data["result"]["url"],
                }
            )
            return render(
                request,
                "grantmakers/notfound.html.j2",
                {"org_id": org_id, "object": data["result"], "form": form},
            )
        form = FunderForm(initial={"org_id": org_id})
        return render(
            request,
            "grantmakers/notfound.html.j2",
            {"org_id": org_id, "object": None, "form": form},
        )


@login_required
def upload_csv(request):
    form = FunderUploadForm()
    if request.method == "POST":
        form = FunderUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data["file"]
            tag_defaults = {}
            tag_cache = {}
            if form.cleaned_data.get("parent_tag"):
                parent_tag_name = form.cleaned_data.get("parent_tag").strip()
                parent_tag, parent_tag_created = FunderTag.objects.get_or_create(
                    tag=parent_tag_name
                )
                if parent_tag_created:
                    messages.info(request, f"Created parent tag '{parent_tag}'.")
                else:
                    messages.info(request, f"Using existing parent tag '{parent_tag}'.")
                tag_defaults["parent"] = parent_tag
                tag_cache[parent_tag_name] = {"tag": parent_tag, "orgs": []}
            reader = csv.DictReader(TextIOWrapper(csv_file, encoding="utf-8-sig"))
            for row in reader:
                if "org_id" not in row:
                    messages.error(request, "'org_id' column not found")
                    break
                if "tag" not in row:
                    messages.error(request, "'tag' column not found")
                    break
                funder_id = row["org_id"].strip()
                if not funder_id:
                    messages.warning(request, "funder_id not found")

                tag_name = row["tag"].strip()

                if tag_name not in tag_cache:
                    tag, tag_created = FunderTag.objects.update_or_create(
                        tag=row["tag"].strip(), defaults=tag_defaults
                    )
                    tag_cache[tag_name] = {"tag": tag, "orgs": []}
                    if tag_created:
                        messages.info(request, f"Created tag '{tag}'.")

                tag_cache[tag_name]["orgs"].append(funder_id)

            current_fy = FinancialYear.objects.filter(
                current=True, status=FinancialYearStatus.OPEN
            ).first()

            for tag_name, tag in tag_cache.items():
                # get funders that exist
                funders = Funder.objects.filter(org_id__in=tag["orgs"]).values_list(
                    "org_id", flat=True
                )

                for org_id in tag["orgs"]:
                    if org_id not in funders:
                        messages.warning(
                            request,
                            f"Funder with org_id {org_id} not found. Tag '{tag_name}' not applied.",
                        )
                        continue

                tag["tag"].funders.add(*funders)
                messages.success(
                    request, f"{tag_name}: {len(funders):,.0f} funders updated."
                )
                if current_fy:
                    tag["tag"].funder_financial_years.add(
                        *FunderFinancialYear.objects.filter(
                            funder_id__in=tag["orgs"], financial_year=current_fy
                        ).values_list("id", flat=True)
                    )
                    messages.success(
                        request,
                        f"{tag_name}: {len(funders):,.0f} funder years updated for ({current_fy}).",
                    )

            return HttpResponseRedirect(reverse("grantmakers:upload_csv"))
    return render(request, "grantmakers/upload.html.j2", {"form": form})


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
            LogEntry.objects.log_actions(
                user_id=request.user.id,
                queryset=[funder],
                action_flag=CHANGE,
                change_message=f"Updated note {note.id}",
            )
        else:
            note = funder.notes.create(note=note_content, added_by=request.user)
            LogEntry.objects.log_actions(
                user_id=request.user.id,
                queryset=[funder],
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
        LogEntry.objects.log_actions(
            user_id=request.user.id,
            queryset=[funder],
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
    elif action == "refresh_ftc":
        funder.save()
        funder.update_from_ftc()
        funder.save()
        funder.refresh_from_db()
        change_message = "Refreshed from Find that Charity"
    elif action == "doesnt_make_grants_to_individuals":
        funder.makes_grants_to_individuals = False
        change_message = "Marked as not making grants to individuals"
    elif action == "makes_grants_to_individuals":
        funder.makes_grants_to_individuals = True
        change_message = "Marked as making grants to individuals"
    elif action == "marked_as_checked":
        if funder.current_year:
            funder.current_year.checked = RecordStatus.CHECKED
            funder.current_year.checked_on = timezone.now()
            funder.current_year.checked_by = request.user
            funder.current_year.save()
            change_message = (
                f"Marked as checked for {funder.current_year.financial_year.fy}"
            )
    elif action == "marked_as_unchecked":
        if funder.current_year:
            funder.current_year.checked = RecordStatus.UNCHECKED
            funder.current_year.checked_on = timezone.now()
            funder.current_year.checked_by = request.user
            funder.current_year.save()
            change_message = (
                f"Marked as unchecked for {funder.current_year.financial_year.fy}"
            )
    elif action == "mark_for_review":
        if funder.current_year:
            funder.current_year.checked = RecordStatus.FOR_REVIEW
            funder.current_year.checked_on = timezone.now()
            funder.current_year.checked_by = request.user
            funder.current_year.save()
            change_message = (
                f"Marked for review for {funder.current_year.financial_year.fy}"
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
        LogEntry.objects.log_actions(
            user_id=request.user.id,
            queryset=[funder],
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

    if "note" in request.POST and request.POST.get("note"):
        funder_year.notes.create(
            added_by=request.user,
            note=request.POST.get("note"),
        )
        changed_values.append(f"Note added {funder_year.notes}")

    if changed_values:
        funder_year.funder_financial_year.checked_on = timezone.now()
        funder_year.funder_financial_year.checked_by = request.user
        funder_year.save()

        LogEntry.objects.log_actions(
            user_id=request.user.id,
            queryset=[funder],
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
            LogEntry.objects.log_actions(
                user_id=request.user.id,
                queryset=[funder],
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
            LogEntry.objects.log_actions(
                user_id=request.user.id,
                queryset=[funder],
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
