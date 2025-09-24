import re

from django import forms

from .models import Folder, Note


class FolderForm(forms.ModelForm):
    error_css_class = "error_text"

    class Meta:
        model = Folder

        fields = ["name"]

    def clean_name(self):
        folder_name = self.cleaned_data.get("name")

        pattern = re.compile(r"^[a-zA-Z0-9_ -]+$")
        if not pattern.match(folder_name):
            raise forms.ValidationError(
                "The folder name can contain letters, numbers and the characters _ and -."
            )

        return folder_name


class NoteForm(forms.ModelForm):
    error_css_class = "error_text"

    class Meta:
        model = Note

        fields = ["name"]


class SaveRoomForm(forms.Form):
    file = forms.FileField(allow_empty_file=True, required=False)
    text = forms.CharField(required=False)
    own = forms.BooleanField(required=False, initial=True)


class ChangePermissionForm(forms.Form):
    value = forms.BooleanField(required=False)


class CreateNoteForm(forms.Form):
    folder_id = forms.IntegerField(required=False)


class RenameResourceForm(forms.Form):
    name = forms.CharField()

    def clean_name(self):
        return self.cleaned_data.get("name").strip()


class CreateFolderForm(forms.Form):
    parent_folder_id = forms.IntegerField(required=False)
    name = forms.CharField()


class TransferResourceForm(forms.Form):
    moved_resource_id = forms.IntegerField()
    moved_resource_token = forms.CharField()
    destination_folder_token = forms.CharField(required=False, empty_value=None)


class MoveResourceForm(forms.Form):
    moved_resource_id = forms.IntegerField()
    moved_resource_token = forms.CharField()
    destination_index = forms.IntegerField()


class SaveCanvasForm(forms.Form):
    file = forms.FileField(allow_empty_file=True, required=True)


class UpdateCanvasBackgroundForm(forms.Form):
    background = forms.CharField()

    def clean_background(self):
        background = self.cleaned_data.get("background")

        if not re.match(r"^#[0-9a-fA-F]{6}$", background):
            raise forms.ValidationError(
                "The background color must be a valid hex color."
            )

        return background
