from django import forms

from ukgrantmaking.models.funder import Funder


class FunderForm(forms.ModelForm):
    org_id = forms.CharField(widget=forms.HiddenInput)
    name_registered = forms.CharField(widget=forms.HiddenInput, required=False)
    name_manual = forms.CharField(
        label="Name",
        required=False,
    )

    class Meta:
        model = Funder
        fields = [
            "org_id",
            "charity_number",
            "name_registered",
            "name_manual",
            "segment",
            "included",
            "makes_grants_to_individuals",
            # "successor",
            "status",
            "date_of_registration",
            "date_of_removal",
            "active",
            "activities",
            "website",
        ]

    def clean(self):
        data = self.cleaned_data
        if not data.get("name_registered") and data.get("name_manual"):
            data["name_registered"] = data["name_manual"]
        if not data.get("name_registered"):
            raise forms.ValidationError("Please provide a name for this funder.")
        return data


class FunderFormNoOrgID(FunderForm):
    org_id = forms.CharField()
