from django import forms


class FunderUploadForm(forms.Form):
    parent_tag = forms.CharField(
        required=False, help_text="Attach all tags to a parent tag"
    )
    file = forms.FileField(required=True)
    delete_tag = forms.CharField(
        required=False, help_text="Remove this tag from all funders in the file"
    )
