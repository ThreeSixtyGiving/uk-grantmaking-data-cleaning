import csv
from io import TextIOWrapper
from urllib.parse import unquote

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import HttpResponseRedirect, QueryDict, StreamingHttpResponse
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.text import slugify


class Echo:
    """An object that implements just the write method of the file-like
    interface.

    https://docs.djangoproject.com/en/5.0/howto/outputting-csv/#streaming-csv-files
    """

    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value.encode("utf-8")


class CSVUploadModelAdmin(admin.ModelAdmin):
    def get_urls(self):
        app_label = self.opts.app_label
        model_name = self.model._meta.model_name
        urls = super().get_urls()
        new_urls = [
            path(
                "upload/",
                self.admin_site.admin_view(self.upload_csv_file),
                name=f"{app_label}_{model_name}_upload",
            ),
            path(
                "export/",
                self.admin_site.admin_view(self.export_csv_file),
                name=f"{app_label}_{model_name}_export",
            ),
        ]
        return new_urls + urls

    def export_csv_file(self, request):
        filters = request.GET.get("_changelist_filters")
        if filters:
            request.GET = QueryDict(filters)
            filename = f"{self.model._meta.verbose_name_plural}_{slugify(unquote(filters))}.csv"
        else:
            request.GET = QueryDict()
            filename = f"{self.model._meta.verbose_name_plural}.csv"
        cl = self.get_changelist_instance(request)
        fields = [f.get_attname() for f in self.model._meta.fields]
        many_to_many_fields = [
            f.name
            for f in self.model._meta.get_fields()
            if f.many_to_many and not f.auto_created
        ]
        buffer = Echo()
        writer = csv.DictWriter(buffer, fieldnames=fields + many_to_many_fields)

        def csv_generator():
            yield writer.writeheader()
            for obj in cl.get_queryset(request).prefetch_related(*many_to_many_fields):
                record = {f: getattr(obj, f) for f in fields}
                for f in many_to_many_fields:
                    record[f] = ", ".join(str(x) for x in getattr(obj, f).all())
                yield writer.writerow(record)

        return StreamingHttpResponse(
            csv_generator(),
            content_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    def handle_file_upload(
        self, file, pk_fields, fields, request, skip_blanks=False, add_new_rows=True
    ):
        reader = csv.DictReader(TextIOWrapper(file, encoding="utf-8-sig"))
        for pk_field in pk_fields:
            if pk_field.get_attname() not in reader.fieldnames:
                raise ValueError(f"'{pk_field}' column not found in file")
        keys_found = [k for k in reader.fieldnames if k in fields]
        if not keys_found:
            raise ValueError("No data in file")
        bulk_updates = []
        for row in reader:
            obj_pks = {
                pk_field.get_attname(): row[pk_field.get_attname()]
                for pk_field in pk_fields
            }
            try:
                obj = self.model.objects.get(**obj_pks)
            except self.model.DoesNotExist:
                if add_new_rows:
                    obj = self.model.objects.create(**obj_pks)
                else:
                    obj_pk = ", ".join([f"{k}: {v}" for k, v in obj_pks.items()])
                    messages.add_message(
                        request,
                        messages.ERROR,
                        f"Row with {obj_pk} not found",
                    )
                    continue
            for k, v in row.items():
                if k in keys_found:
                    if skip_blanks and v == "":
                        continue
                    if fields[k].get_internal_type() == "BooleanField":
                        if v.lower() in ["true", "yes", "1", "t"]:
                            v = True
                        elif v.lower() in ["false", "no", "0", "f"]:
                            v = False
                        else:
                            v = None
                    setattr(obj, k, v)
            bulk_updates.append(obj)
        if bulk_updates:
            return self.model.objects.bulk_update(
                bulk_updates, keys_found, batch_size=1_000
            )

    def upload_csv_file(self, request):
        non_readonly_fields = [
            f
            for f in self.model._meta.fields
            if (f.name not in self.readonly_fields)
            and (not f.auto_created)
            and (not f.primary_key)
            and (not f.generated)
            and (f.concrete)
        ]
        fields = {}
        for f in non_readonly_fields:
            if f.choices:
                fields[f.get_attname()] = f
            else:
                fields[f.get_attname()] = f
        pk_fields = None
        for unique_fields in self.model._meta.unique_together:
            pk_fields = [self.model._meta.get_field(f) for f in unique_fields]
        if not pk_fields:
            pk_fields = [self.model._meta.get_field(self.model._meta.pk.name)]
        for field in pk_fields:
            if field.name in fields:
                fields.pop(field.name)

        class UploadCSVForm(forms.Form):
            file = forms.FileField()
            handle_blanks = forms.ChoiceField(
                choices=[
                    ("skip", "Skip - blank values in the CSV will be skipped"),
                    (
                        "update",
                        "Update - blank values in the file will make the value blank",
                    ),
                ],
                label="Handle blank values",
                help_text="Choose whether to update fields with blank values",
            )
            add_new_rows = forms.ChoiceField(
                choices=[
                    ("true", "Yes - add new rows to the database"),
                    (
                        "false",
                        "No - only update existing rows in the database",
                    ),
                ],
                label="Add new rows",
                help_text="Choose whether to add new rows for missing primary keys",
            )

        context = dict(
            self.admin_site.each_context(request),
            opts=self.opts,
            title="Upload new {} data".format(self.model._meta.verbose_name_plural),
            subtitle="Upload a CSV file to update {} information".format(
                self.model._meta.verbose_name_plural
            ),
            fields=fields,
            pk_field=pk_fields,
        )

        # check if form was submitted
        if request.method == "POST":
            form = UploadCSVForm(request.POST, request.FILES)
            if form.is_valid():
                file = request.FILES["file"]
                try:
                    result = self.handle_file_upload(
                        file,
                        pk_fields,
                        fields,
                        request,
                        skip_blanks=form.cleaned_data["handle_blanks"] == "skip",
                        add_new_rows=form.cleaned_data["add_new_rows"] == "true",
                    )
                    messages.add_message(
                        request,
                        messages.INFO,
                        "{} {} updated".format(
                            result or 0,
                            (
                                self.model._meta.verbose_name
                                if result == 1
                                else self.model._meta.verbose_name_plural
                            ),
                        ),
                    )
                except (
                    ValueError,
                    ValidationError,
                    IntegrityError,
                ) as e:
                    if hasattr(e, "messages"):
                        for message in e.messages:
                            messages.add_message(request, messages.ERROR, str(message))
                    else:
                        messages.add_message(request, messages.ERROR, str(e))
                return HttpResponseRedirect(request.path_info)
            else:
                messages.add_message(request, messages.ERROR, "No file submitted")
            pass
        else:
            form = UploadCSVForm()
        context["form"] = form

        return TemplateResponse(
            request,
            "admin/{}/{}/upload.html".format(
                self.model._meta.app_label, self.model._meta.model_name
            ),
            context,
        )
