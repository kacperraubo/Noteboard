import enum
import json
import secrets
import typing
from http import HTTPStatus

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View

from account.models import Accounts
from utilities.aws import (
    download_file_from_aws,
    remove_file_from_aws,
    upload_file_to_aws,
)
from utilities.folder_history import get_folder_history, get_next_folders
from utilities.generate_meta_tags import generate_meta_tags
from utilities.resource_count import count_resources_in_folder
from utilities.responses import (
    ApiErrorKwargsResponse,
    ApiErrorMessageAndCodeResponse,
    ApiSuccessKwargsResponse,
    ApiSuccessResponse,
)

from .anonymous import AnonymousUser
from .anonymous import Folder as AnonymousFolder
from .anonymous import Note as AnonymousNote
from .forms import (
    ChangePermissionForm,
    CreateFolderForm,
    CreateNoteForm,
    MoveResourceForm,
    RenameResourceForm,
    SaveCanvasForm,
    SaveRoomForm,
    TransferResourceForm,
    UpdateCanvasBackgroundForm,
)
from .models import Canvas, Folder, Note, Room


class ErrorCode(enum.IntEnum):
    ROOM_NOT_FOUND = 1000
    NOTE_NOT_FOUND = 1001
    SAVE_ROOM_NOT_FOUND = 1023
    UNKNOWN_PERMISSION = 1004
    UNABLE_TO_CREATE_ROOM = 1005
    CHANGE_PERMISSION_ROOM_NOT_FOUND = 1006
    NO_EDIT_PERMISSION = 1007
    FOLDER_NOT_FOUND = 1007
    RENAME_ITEM_NOT_ALLOWED = 1008
    REMOVE_ITEM_NOT_ALLOWED = 1009
    MOVE_TO_SAME_FOLDER = 1010
    MOVE_DESTINATION_NOT_FOUND = 1011
    MOVE_ITEM_NOT_ALLOWED = 1012
    MOVE_ITEM_TYPE_INVALID = 1013
    CREATE_FOLDER_NOT_FOUND = 1014
    CHANGE_ORDER_INVALID_INPUT = 1015
    CHANGE_ORDER_MISSING_DATA = 1016
    CHANGE_ORDER_RESOURCE_NOT_FOUND = 1017
    CHANGE_ORDER_SAME_POSITION = 1018
    INVALID_FORM = 1019
    CHANGE_ORDER_INVALID_DESTINATION = 1020


class TextEditorRoom(View):
    text_editor_template = "text_editor.html"

    def get(self, request: HttpRequest, note_token: str, room_name: str):
        if not request.user.is_authenticated:
            user = AnonymousUser.from_request(request)
            note = user.get_note_by_token_and_room_name(note_token, room_name)

            if note is not None:
                meta_tags = generate_meta_tags(
                    f"Noteboard — {note.name}",
                    "A web-based notepad.",
                    request.build_absolute_uri(
                        reverse("text_editor_room", args=[note_token, room_name])
                    ),
                )

                context = {
                    "meta_tags": meta_tags,
                    "room": note.room,
                    "note": note,
                    "previous_folders": (
                        note.folder.get_folder_history(with_self=True)
                        if note.folder
                        else []
                    ),
                    "is_users_room": True,
                }

                return render(request, self.text_editor_template, context)

        room = get_object_or_404(Room, name=room_name)
        note = get_object_or_404(Note, token=note_token, room=room)

        if not room.user == request.user and not room.is_public:
            raise Http404("Not found")

        meta_tags = generate_meta_tags(
            f"Noteboard — {note.name}",
            "A web-based notepad.",
            request.build_absolute_uri(
                reverse("text_editor_room", args=[note_token, room_name])
            ),
        )

        context = {
            "meta_tags": meta_tags,
            "room": room,
            "note": note,
            "previous_folders": get_folder_history(
                note.folder, with_current_folder=True
            ),
            "is_users_room": room.user == request.user,
        }

        return render(request, self.text_editor_template, context)


class Home(View):
    text_editor_template = "home.html"

    def get(self, request: HttpRequest, folder_token: typing.Optional[str] = None):
        if not request.user.is_authenticated:
            user = AnonymousUser.from_request(request)
            folder = user.get_folder_by_token(folder_token) if folder_token else None
            resources = user.get_resources_in_folder(folder, order_by="index")
            previous_folders = folder.get_folder_history() if folder else []

        else:
            if folder_token:
                folder = get_object_or_404(
                    Folder, token=folder_token, user=request.user
                )
            else:
                folder = None

            notes = Note.objects.filter(user=request.user, folder=folder)
            folders = Folder.objects.filter(
                user=request.user, folder=folder if folder else None
            )
            resources = sorted([*notes, *folders], key=lambda item: item.index)
            previous_folders = get_folder_history(folder)

        meta_tags = generate_meta_tags(
            f"Noteboard — {folder.name}" if folder else "Noteboard",
            "A web-based notepad.",
            request.build_absolute_uri(reverse("home")),
        )

        context = {
            "meta_tags": meta_tags,
            "resources": resources,
            "current_folder": folder,
            "previous_folders": previous_folders,
        }

        return render(request, self.text_editor_template, context)


class SaveRoom(View):
    def post(self, request: HttpRequest, note_token: str):
        form = SaveRoomForm(request.POST, request.FILES)

        if form.is_valid():
            if not request.user.is_authenticated and form.cleaned_data.get("own"):
                text = form.cleaned_data.get("text")

                if text is None:
                    return ApiErrorMessageAndCodeResponse(
                        "Text is required.",
                        ErrorCode.INVALID_FORM,
                    )

                user = AnonymousUser.from_request(request)

                room = (
                    None
                    if user.get_note_by_token(note_token) is None
                    else user.get_note_by_token(note_token).room
                )
                if room is None:
                    return ApiErrorMessageAndCodeResponse(
                        "This room does not exist.",
                        ErrorCode.ROOM_NOT_FOUND,
                    )

                room.note.text = text
                user.save(request.session)

                return ApiSuccessResponse("File saved successfully.")

            file = form.cleaned_data.get("file")

            if file is None:
                return ApiErrorMessageAndCodeResponse(
                    "File is required.",
                    ErrorCode.INVALID_FORM,
                )

            try:
                note = Note.objects.get(token=note_token)
                room = note.room
            except Note.DoesNotExist:
                return ApiErrorMessageAndCodeResponse(
                    "This room does not exist.",
                    ErrorCode.SAVE_ROOM_NOT_FOUND,
                )

            if not room.user == request.user and not room.is_editable:
                return ApiErrorMessageAndCodeResponse(
                    "You do not have permission to change this file.",
                    ErrorCode.NO_EDIT_PERMISSION,
                    HTTPStatus.FORBIDDEN,
                )

            try:
                note = Note.objects.get(room=room)
            except Note.DoesNotExist:
                return ApiErrorMessageAndCodeResponse(
                    "This note does not exist.",
                    ErrorCode.NOTE_NOT_FOUND,
                )

            if note.text_file:
                path = note.text_file.name
                upload_file_to_aws(path, file)
            else:
                note.text_file = file
                note.save()

            return ApiSuccessResponse("File saved successfully.")
        else:
            return ApiErrorKwargsResponse(
                status=HTTPStatus.BAD_REQUEST,
                errors=form.errors,
                message="Invalid form.",
                code=ErrorCode.INVALID_FORM,
            )


class SaveCanvas(View):
    def post(self, request: HttpRequest, note_token: str):
        form = SaveCanvasForm(request.POST, request.FILES)

        if not form.is_valid():
            return ApiErrorKwargsResponse(
                status=HTTPStatus.BAD_REQUEST,
                errors=form.errors,
                message="Invalid form.",
                code=ErrorCode.INVALID_FORM,
            )

        file = form.cleaned_data.get("file")

        try:
            note = Note.objects.get(token=note_token)
        except Note.DoesNotExist:
            return ApiErrorMessageAndCodeResponse(
                "Note not found.",
                ErrorCode.NOTE_NOT_FOUND,
            )

        if not request.user == note.user and not note.room.is_editable:
            return ApiErrorMessageAndCodeResponse(
                "You do not have permission to save this canvas.",
                ErrorCode.NO_EDIT_PERMISSION,
                HTTPStatus.FORBIDDEN,
            )

        if not Canvas.objects.filter(note=note).exists():
            note.canvas_file = Canvas.objects.create()
            note.save()

        if note.canvas_file.file:
            path = note.canvas_file.file.name
            upload_file_to_aws(path, file)
        else:
            note.canvas_file.file = file
            note.save()
            note.canvas_file.save()

        return ApiSuccessResponse("Canvas saved successfully.")


class UpdatePermission(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, room_id: int, permission: str):
        form = ChangePermissionForm(json.loads(request.body))

        if form.is_valid():
            value = form.cleaned_data.get("value")

            try:
                room = Room.objects.get(id=room_id, user=request.user)
            except Room.DoesNotExist:
                return ApiErrorMessageAndCodeResponse(
                    "This room does not exist.",
                    ErrorCode.CHANGE_PERMISSION_ROOM_NOT_FOUND,
                )

            if permission == "editable":
                room.is_editable = value

                if room.is_editable:
                    room.is_public = True

                room.save()

                return ApiSuccessKwargsResponse(
                    permission="editable",
                    changed_to=room.is_editable,
                    is_editable=room.is_editable,
                    is_public=room.is_public,
                )
            elif permission == "publicity":
                room.is_public = value

                if not room.is_public:
                    room.is_editable = False

                room.save()

                return ApiSuccessKwargsResponse(
                    permission="publicity",
                    changed_to=room.is_public,
                    is_public=room.is_public,
                    is_editable=room.is_editable,
                )
            else:
                return ApiErrorMessageAndCodeResponse(
                    "Unknown permission.",
                    ErrorCode.UNKNOWN_PERMISSION,
                )
        else:
            return ApiErrorKwargsResponse(
                status=HTTPStatus.BAD_REQUEST,
                errors=form.errors,
                message="Invalid form.",
                code=ErrorCode.INVALID_FORM,
            )


class CreateNote(View):
    def post(self, request: HttpRequest):
        form = CreateNoteForm(json.loads(request.body))

        if form.is_valid():
            folder_id: typing.Optional[int] = form.cleaned_data.get("folder_id")

            if not request.user.is_authenticated:
                user = AnonymousUser.from_request(request)
                folder = (
                    user.get_folder_by_id(folder_id) if folder_id is not None else None
                )
                note = user.add_note(folder=folder)
                user.save(request.session)

                path = reverse("text_editor_room", args=[note.token, note.room.name])

                return ApiSuccessKwargsResponse(path=path)
            else:
                try:
                    folder = (
                        Folder.objects.get(user=request.user, id=folder_id)
                        if folder_id is not None
                        else None
                    )
                except Folder.DoesNotExist:
                    return ApiErrorMessageAndCodeResponse(
                        "Folder does not exist.",
                        ErrorCode.FOLDER_NOT_FOUND,
                    )

            user_notes = Note.objects.filter(user=request.user)
            room = Room.objects.create(user=request.user, name=secrets.token_hex(16))
            resource_count_in_folder = count_resources_in_folder(folder, request.user)

            if user_notes:
                for index in range(len(user_notes) + 1):
                    if f"Note{str(index+1)}" not in user_notes.values_list(
                        "name", flat=True
                    ):
                        note = Note(
                            user=request.user,
                            name=f"Note{index+1}",
                            room=room,
                            index=resource_count_in_folder,
                            canvas_file=Canvas.objects.create(),
                        )
                        break
            else:
                note = Note(
                    user=request.user,
                    name="Note1",
                    room=room,
                    index=resource_count_in_folder,
                    canvas_file=Canvas.objects.create(),
                )

            note.folder = folder
            note.save()

            path = reverse("text_editor_room", args=[note.token, room.name])

            return ApiSuccessKwargsResponse(path=path)


class DeleteResource(View):
    def post(self, request: HttpRequest, item_id: int, item_token: str):
        if not request.user.is_authenticated:
            user = AnonymousUser.from_request(request)
            resource = user.get_resource_by_id_and_token(item_id, item_token)

            if resource is None:
                return redirect("home")
            else:
                resource.delete()
                user.save(request.session)

            return redirect("home")

        try:
            item = Note.objects.get(user=request.user, token=item_token, id=item_id)
        except Note.DoesNotExist:
            try:
                item = Folder.objects.get(
                    user=request.user, token=item_token, id=item_id
                )
            except Folder.DoesNotExist:
                return redirect("home")

        if isinstance(item, Folder):
            folders_to_delete = get_next_folders(item)

            for folder in folders_to_delete:
                notes = Note.objects.filter(folder=folder)

                for note in notes:
                    remove_file_from_aws(note.text_file.name)

                folder.delete()
        else:
            remove_file_from_aws(item.text_file.name)

        resources_with_higher_index_in_folder = list(
            Note.objects.filter(
                user=request.user, folder=item.folder, index__gt=item.index
            )
        ) + list(
            Folder.objects.filter(
                user=request.user,
                folder=item.folder,
                index__gt=item.index,
            )
        )

        for resource in resources_with_higher_index_in_folder:
            resource.index -= 1
            resource.save()

        item.delete()

        return redirect("home")


class RenameResource(View):
    def post(self, request: HttpRequest, item_id: int, item_token: str):
        form = RenameResourceForm(json.loads(request.body))

        if not form.is_valid():
            return ApiErrorKwargsResponse(
                status=HTTPStatus.BAD_REQUEST,
                errors=form.errors,
                message="Invalid form.",
                code=ErrorCode.INVALID_FORM,
            )

        name = form.cleaned_data.get("name")

        if name == "":
            return ApiErrorMessageAndCodeResponse(
                "Name cannot be empty.",
                ErrorCode.INVALID_FORM,
            )

        if not request.user.is_authenticated:
            user = AnonymousUser.from_request(request)
            resource = user.get_resource_by_id_and_token(item_id, item_token)

            if resource is None:
                return ApiErrorMessageAndCodeResponse(
                    "You are not allowed to rename this resource.",
                    ErrorCode.RENAME_ITEM_NOT_ALLOWED,
                )
            else:
                resource.name = name
                user.save(request.session)

                return ApiSuccessKwargsResponse(
                    message="Resource renamed successfully."
                )

        try:
            item = Note.objects.get(user=request.user, token=item_token, id=item_id)
        except Note.DoesNotExist:
            try:
                item = Folder.objects.get(
                    user=request.user, token=item_token, id=item_id
                )
            except Folder.DoesNotExist:
                return ApiErrorMessageAndCodeResponse(
                    "You are not allowed to rename this resource.",
                    ErrorCode.RENAME_ITEM_NOT_ALLOWED,
                )

        item.name = name
        item.save()

        return ApiSuccessKwargsResponse(message="Resource renamed successfully.")


class CreateFolder(View):
    def post(self, request: HttpRequest):
        form = CreateFolderForm(json.loads(request.body))

        if form.is_valid():
            parent_folder_id = form.cleaned_data.get("parent_folder_id")
            name = form.cleaned_data.get("name")

            if not request.user.is_authenticated:
                user = AnonymousUser.from_request(request)
                parent_folder = (
                    user.get_folder_by_id(parent_folder_id)
                    if parent_folder_id is not None
                    else None
                )
                user.add_folder(name, folder=parent_folder)
                user.save(request.session)

                return ApiSuccessResponse("Folder created successfully.")

            if parent_folder_id:
                try:
                    parent_folder = Folder.objects.get(
                        user=request.user,
                        id=parent_folder_id,
                    )
                except Folder.DoesNotExist:
                    return ApiErrorMessageAndCodeResponse(
                        "Folder does not exist.",
                        ErrorCode.CREATE_FOLDER_NOT_FOUND,
                    )
            else:
                parent_folder = None

            resource_count_in_folder = count_resources_in_folder(
                parent_folder, request.user
            )

            folder = Folder(
                user=request.user,
                name=name,
                index=resource_count_in_folder,
                folder=parent_folder,
            )

            folder.save()

            return ApiSuccessResponse("Folder created successfully.")
        else:
            return ApiErrorKwargsResponse(
                status=HTTPStatus.BAD_REQUEST,
                errors=form.errors,
                message="Invalid form.",
                code=ErrorCode.INVALID_FORM,
            )


class TransferResource(View):
    def move_for_anonymous_user(
        self,
        request: HttpRequest,
        user: AnonymousUser,
        moved_resource: typing.Union[AnonymousNote, AnonymousFolder],
        destination_folder: typing.Optional[AnonymousFolder],
    ):
        resources_with_higher_index_in_source_folder = (
            user.get_resources_with_index_gt_in_folder(
                moved_resource.folder, moved_resource.index
            )
        )

        resource_count_in_destination_folder = user.get_resource_count_in_folder(
            destination_folder
        )
        moved_resource.folder = destination_folder
        moved_resource.folder_id = destination_folder.id if destination_folder else None
        moved_resource.index = resource_count_in_destination_folder

        for resource in resources_with_higher_index_in_source_folder:
            resource.index -= 1

        user.save(request.session)

        return ApiSuccessResponse(
            {
                "message": "Resource moved successfully.",
                "item_id": moved_resource.id,
                "item_token": moved_resource.token,
            }
        )

    def move_for_authenticated_user(
        self,
        user: Accounts,
        moved_resource: typing.Union[Note, Folder],
        destination_folder: typing.Optional[Folder],
    ):
        resources_with_higher_index_in_source_folder = list(
            Note.objects.filter(
                folder=moved_resource.folder, index__gt=moved_resource.index
            ).exclude(id=moved_resource.id)
        ) + list(
            Folder.objects.filter(
                folder=moved_resource.folder if moved_resource.folder else None,
                index__gt=moved_resource.index,
            ).exclude(id=moved_resource.id)
        )

        moved_resource.folder = destination_folder

        resource_count_in_destination_folder = count_resources_in_folder(
            destination_folder, user
        )
        moved_resource.index = resource_count_in_destination_folder

        for resource in resources_with_higher_index_in_source_folder:
            resource.index -= 1
            resource.save()

        moved_resource.save()

        return ApiSuccessResponse(
            {
                "message": "Resource moved successfully.",
                "item_id": moved_resource.id,
                "item_token": moved_resource.token,
            }
        )

    def post(self, request: HttpRequest):
        form = TransferResourceForm(json.loads(request.body))

        if not form.is_valid():
            return ApiErrorKwargsResponse(
                status=HTTPStatus.BAD_REQUEST,
                errors=form.errors,
                message="Invalid form.",
                code=ErrorCode.INVALID_FORM,
            )

        moved_resource_id: int = form.cleaned_data.get("moved_resource_id")
        moved_resource_token: str = form.cleaned_data.get("moved_resource_token")
        destination_folder_token: typing.Optional[str] = form.cleaned_data.get(
            "destination_folder_token"
        )

        resource_not_found_response = ApiErrorMessageAndCodeResponse(
            "Resource not found.",
            ErrorCode.MOVE_ITEM_NOT_ALLOWED,
        )

        folder_not_found_response = ApiErrorMessageAndCodeResponse(
            "Folder not found.",
            ErrorCode.MOVE_DESTINATION_NOT_FOUND,
        )

        if not request.user.is_authenticated:
            user = AnonymousUser.from_request(request)
            moved_resource = user.get_resource_by_id_and_token(
                moved_resource_id, moved_resource_token
            )
            if moved_resource is None:
                return resource_not_found_response

            destination_folder = (
                user.get_folder_by_token(destination_folder_token)
                if destination_folder_token is not None
                else None
            )
            if destination_folder is None and destination_folder_token is not None:
                return folder_not_found_response

            return self.move_for_anonymous_user(
                request, user, moved_resource, destination_folder
            )
        else:
            try:
                moved_resource = Note.objects.get(
                    user=request.user, token=moved_resource_token, id=moved_resource_id
                )
            except Note.DoesNotExist:
                try:
                    moved_resource = Folder.objects.get(
                        user=request.user,
                        token=moved_resource_token,
                        id=moved_resource_id,
                    )
                except Folder.DoesNotExist:
                    return resource_not_found_response

            if destination_folder_token:
                try:
                    destination_folder = Folder.objects.get(
                        user=request.user, token=destination_folder_token
                    )
                except Folder.DoesNotExist:
                    return folder_not_found_response
            else:
                destination_folder = None

            return self.move_for_authenticated_user(
                request.user, moved_resource, destination_folder
            )


class MoveResource(View):
    def post(self, request: HttpRequest):
        form = MoveResourceForm(json.loads(request.body))

        if not form.is_valid():
            return ApiErrorKwargsResponse(
                status=HTTPStatus.BAD_REQUEST,
                errors=form.errors,
                message="Invalid form.",
                code=ErrorCode.INVALID_FORM,
            )

        resource_id: int = form.cleaned_data.get("moved_resource_id")
        resource_token: str = form.cleaned_data.get("moved_resource_token")
        destination_index: int = form.cleaned_data.get("destination_index")

        resource_not_found_response = ApiErrorMessageAndCodeResponse(
            "Resource not found.",
            ErrorCode.CHANGE_ORDER_RESOURCE_NOT_FOUND,
        )
        invalid_index_response = ApiErrorMessageAndCodeResponse(
            "Invalid destination index.",
            ErrorCode.CHANGE_ORDER_INVALID_DESTINATION,
        )

        if not request.user.is_authenticated:
            user = AnonymousUser.from_request(request)
            moved_resource = user.get_resource_by_id_and_token(
                resource_id, resource_token
            )
            if moved_resource is None:
                return resource_not_found_response

            largest_index = len(user.get_resources_in_folder(moved_resource.folder)) - 1
            if largest_index < 0:
                largest_index = 0

            if destination_index > largest_index or destination_index < 0:
                return invalid_index_response

            return self.change_order_for_anonymous_user(
                request, user, moved_resource, destination_index
            )
        else:
            try:
                moved_resource = Note.objects.get(
                    user=request.user, token=resource_token, id=resource_id
                )
            except Note.DoesNotExist:
                try:
                    moved_resource = Folder.objects.get(
                        user=request.user, token=resource_token, id=resource_id
                    )
                except Folder.DoesNotExist:
                    return resource_not_found_response

            largest_index = (
                Note.objects.filter(
                    folder=moved_resource.folder, user=request.user
                ).count()
                + Folder.objects.filter(
                    folder=moved_resource.folder, user=request.user
                ).count()
            ) - 1
            if largest_index < 0:
                largest_index = 0

            if destination_index > largest_index or destination_index < 0:
                return invalid_index_response

            return self.change_order_for_authenticated_user(
                request.user, moved_resource, destination_index
            )

    def change_order_for_anonymous_user(
        self,
        request: HttpRequest,
        user: AnonymousUser,
        moved_resource: typing.Union[AnonymousNote, AnonymousFolder],
        destination_index: int,
    ):
        if moved_resource.index == destination_index:
            return ApiSuccessResponse("Resource order changed successfully.")

        parent_folder = moved_resource.folder

        if moved_resource.index < destination_index:
            range_start = moved_resource.index + 1
            range_end = destination_index
        else:
            range_start = destination_index
            range_end = moved_resource.index - 1

        resources_to_update = user.get_resources_with_index_in_range_in_folder(
            parent_folder, range_start, range_end
        )
        for resource in resources_to_update:
            resource.index += 1 if moved_resource.index > destination_index else -1

        moved_resource.index = destination_index

        user.save(request.session)

        return ApiSuccessResponse("Resource order changed successfully.")

    def change_order_for_authenticated_user(
        self,
        user: Accounts,
        moved_resource: typing.Union[Note, Folder],
        destination_index: int,
    ):
        if moved_resource.index == destination_index:
            return ApiSuccessResponse("Resource order changed successfully.")

        parent_folder = moved_resource.folder

        largest_index = (
            Note.objects.filter(folder=parent_folder, user=user).count()
            + Folder.objects.filter(folder=parent_folder, user=user).count()
        ) - 1

        if largest_index < 0:
            largest_index = 0

        if destination_index > largest_index:
            return ApiErrorMessageAndCodeResponse(
                "Invalid destination index.",
                ErrorCode.CHANGE_ORDER_INVALID_DESTINATION,
            )

        if moved_resource.index < destination_index:
            range_start = moved_resource.index + 1
            range_end = destination_index
        else:
            range_start = destination_index
            range_end = moved_resource.index - 1

        notes_to_update = Note.objects.filter(
            folder=parent_folder, index__range=(range_start, range_end)
        )
        folders_to_update = Folder.objects.filter(
            folder=parent_folder, index__range=(range_start, range_end)
        )
        resources_to_update = [*notes_to_update, *folders_to_update]

        for resource in resources_to_update:
            resource.index += 1 if moved_resource.index > destination_index else -1
            resource.save()

        moved_resource.index = destination_index
        moved_resource.save()

        return ApiSuccessResponse("Resource order changed successfully.")


class GetNoteText(View):
    def get(self, request: HttpRequest, note_token: str):
        if not request.user.is_authenticated:
            user = AnonymousUser.from_request(request)
            note = user.get_note_by_token(note_token)

            if note is not None:
                return ApiSuccessKwargsResponse(text=note.get_text())

        try:
            note = Note.objects.get(token=note_token)
        except Note.DoesNotExist:
            return ApiErrorMessageAndCodeResponse(
                "Note not found.",
                ErrorCode.NOTE_NOT_FOUND,
            )

        if not request.user == note.user and not note.room.is_public:
            return ApiErrorMessageAndCodeResponse(
                "You do not have permission to view this note.",
                ErrorCode.NO_EDIT_PERMISSION,
                HTTPStatus.FORBIDDEN,
            )

        return ApiSuccessKwargsResponse(text=note.get_text())


class GetNoteCanvas(View):
    def get(self, request: HttpRequest, note_token: str):
        try:
            note = Note.objects.get(token=note_token)
        except Note.DoesNotExist:
            return ApiErrorMessageAndCodeResponse(
                "Note not found.",
                ErrorCode.NOTE_NOT_FOUND,
            )

        if not request.user == note.user and not note.room.is_public:
            return ApiErrorMessageAndCodeResponse(
                "You do not have permission to view this canvas.",
                ErrorCode.NO_EDIT_PERMISSION,
                HTTPStatus.FORBIDDEN,
            )

        if not note.canvas_file.file:
            return ApiErrorMessageAndCodeResponse(
                "Canvas not found.",
                ErrorCode.NOTE_NOT_FOUND,
            )

        file = download_file_from_aws(note.canvas_file.file)
        bytes = file.read()

        return HttpResponse(bytes, content_type="image/png")


class UpdateCanvasBackground(View):
    def post(self, request: HttpRequest, note_id: int):
        form = UpdateCanvasBackgroundForm(json.loads(request.body))

        if not form.is_valid():
            return ApiErrorKwargsResponse(
                status=HTTPStatus.BAD_REQUEST,
                errors=form.errors,
                message="Invalid form.",
                code=ErrorCode.INVALID_FORM,
            )

        background = form.cleaned_data.get("background")

        try:
            note = Note.objects.get(id=note_id)
        except Note.DoesNotExist:
            return ApiErrorMessageAndCodeResponse(
                "Note not found.",
                ErrorCode.NOTE_NOT_FOUND,
            )

        if not request.user == note.user and not note.room.is_editable:
            return ApiErrorMessageAndCodeResponse(
                "You do not have permission to change this canvas.",
                ErrorCode.NO_EDIT_PERMISSION,
                HTTPStatus.FORBIDDEN,
            )

        note.canvas_file.background = background
        note.canvas_file.save()

        return ApiSuccessResponse("Canvas background updated successfully.")


class UpdateDefaultDisplay(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, note_id: int):
        type = json.loads(request.body).get("type")

        if type not in ["text", "canvas"]:
            return ApiErrorMessageAndCodeResponse(
                "Invalid display type.",
                ErrorCode.INVALID_FORM,
            )

        try:
            note = Note.objects.get(user=request.user, id=note_id)
        except Note.DoesNotExist:
            return ApiErrorMessageAndCodeResponse(
                "Note not found.",
                ErrorCode.NOTE_NOT_FOUND,
            )

        note.display = type
        note.save()

        return ApiSuccessKwargsResponse(
            message="Default display updated successfully.", display=note.display
        )
