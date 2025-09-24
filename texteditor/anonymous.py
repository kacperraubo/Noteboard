from __future__ import annotations

import dataclasses
import datetime
import typing

from django.db import transaction
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.http import HttpRequest

from account.models import Accounts
from texteditor.models import (
    Note as NoteModel,
    Folder as FolderModel,
    Room as RoomModel,
)

from .models import get_token, generate_file_name


@dataclasses.dataclass
class Room:
    _user: AnonymousUser
    id: int
    name: str

    def serialize(self) -> typing.Dict[str, typing.Any]:
        return {
            "id": self.id,
            "name": self.name,
        }

    @classmethod
    def deserialize(
        cls: typing.Type[Room],
        data: typing.Dict[str, typing.Any],
        user: User,
    ) -> Room:
        return cls(
            user,
            **data,
        )

    def delete(self) -> None:
        self._user.delete_room(self)

    @property
    def note(self) -> Note:
        return self._user.get_note_by_room(self)


@dataclasses.dataclass
class Folder:
    _user: AnonymousUser
    id: int
    name: str
    token: str
    index: int
    room: typing.Optional[Room] = None
    room_id: typing.Optional[int] = None
    folder: typing.Optional[Folder] = None
    folder_id: typing.Optional[int] = None
    date: datetime.datetime = dataclasses.field(default_factory=datetime.datetime.now)
    folders: typing.List[Folder] = dataclasses.field(default_factory=list)
    notes: typing.List[Note] = dataclasses.field(default_factory=list)

    def serialize(self) -> typing.Dict[str, typing.Any]:
        return {
            "id": self.id,
            "name": self.name,
            "token": self.token,
            "room": None,
            "room_id": self.room_id,
            "folder": None,
            "folder_id": self.folder_id,
            "date": self.date.isoformat(),
            "index": self.index,
        }

    @classmethod
    def deserialize(
        cls: typing.Type[Folder],
        data: typing.Dict[str, typing.Any],
        user: AnonymousUser,
    ) -> Folder:
        return cls(
            user,
            **{**data, "date": datetime.datetime.fromisoformat(data["date"])},
        )

    def delete(self) -> None:
        self._user.delete_folder(self)

    def get_folder_history(self, with_self: bool = False) -> typing.List[Folder]:
        if with_self:
            folders = [self]
        else:
            folders = []

        folder = self.folder
        while folder:
            folders.append(folder)
            folder = folder.folder

        return folders

    @property
    def note_count(self) -> int:
        return len(self.notes)

    @property
    def folder_count(self) -> int:
        return len(self.folders)

    @property
    def resource_count(self) -> int:
        return self.note_count + self.folder_count


@dataclasses.dataclass
class Note:
    _user: AnonymousUser
    id: int
    name: str
    token: str
    index: int
    text: str
    room: typing.Optional[Room] = None
    room_id: typing.Optional[int] = None
    folder: typing.Optional[Folder] = None
    folder_id: typing.Optional[int] = None
    date: datetime.datetime = dataclasses.field(default_factory=datetime.datetime.now)

    def get_text(self) -> str:
        return self.text

    def delete(self) -> None:
        self._user.delete_note(self)

    def serialize(self) -> typing.Dict[str, typing.Any]:
        return {
            "id": self.id,
            "name": self.name,
            "token": self.token,
            "room": None,
            "room_id": self.room_id,
            "folder": None,
            "folder_id": self.folder_id,
            "date": self.date.isoformat(),
            "index": self.index,
            "text": self.text,
        }

    @classmethod
    def deserialize(
        cls: typing.Type[Note],
        data: typing.Dict[str, typing.Any],
        user: AnonymousUser,
    ) -> Note:
        return cls(
            user,
            **{**data, "date": datetime.datetime.fromisoformat(data["date"])},
        )

    def get_folder_history(self) -> typing.List[Folder]:
        folders = []

        folder = self.folder
        while folder:
            folders.append(folder)
            folder = folder.folder

        return folders


class AnonymousUser:
    def __init__(self, user: User):
        self.user = user
        self.folders: typing.List[Folder] = []
        self._folder_map: typing.Dict[int, Folder] = {}
        self.notes: typing.List[Note] = []
        self._note_map: typing.Dict[int, Note] = {}
        self.rooms: typing.List[Room] = []
        self._room_map: typing.Dict[int, Room] = {}
        self._next_folder_id = 0
        self._next_note_id = 0
        self._next_room_id = 0

    @classmethod
    def from_request(cls, request: HttpRequest) -> AnonymousUser:
        raw_folders = request.session.get("_anonymous_folders", [])
        raw_notes = request.session.get("_anonymous_notes", [])
        raw_rooms = request.session.get("_anonymous_rooms", [])

        user = AnonymousUser(request.user)

        for raw_folder in raw_folders:
            folder = Folder.deserialize(raw_folder, user)
            user.folders.append(folder)
            user._folder_map[raw_folder["id"]] = folder

            if folder.id >= user._next_folder_id:
                user._next_folder_id = folder.id + 1

        for raw_note in raw_notes:
            note = Note.deserialize(raw_note, user)
            user.notes.append(note)
            user._note_map[raw_note["id"]] = note

            if note.id >= user._next_note_id:
                user._next_note_id = note.id + 1

        for raw_room in raw_rooms:
            room = Room.deserialize(raw_room, user)
            user.rooms.append(room)
            user._room_map[raw_room["id"]] = room

            if room.id >= user._next_room_id:
                user._next_room_id = room.id + 1

        for resource in user.folders + user.notes:
            if resource.folder_id is not None:
                resource.folder = user._folder_map[resource.folder_id]

                if isinstance(resource, Folder):
                    resource.folder.folders.append(resource)
                else:
                    resource.folder.notes.append(resource)

            if resource.room_id is not None:
                resource.room = user._room_map[resource.room_id]

        return user

    def save(self, session: typing.Dict[str, typing.Any]) -> None:
        session.update(
            {
                "_anonymous_folders": [folder.serialize() for folder in self.folders],
                "_anonymous_notes": [note.serialize() for note in self.notes],
                "_anonymous_rooms": [room.serialize() for room in self.rooms],
            }
        )

    def get_folder_by_id(self, folder_id: int) -> typing.Optional[Folder]:
        return self._folder_map.get(folder_id, None)

    def get_folder_by_token(self, token: str) -> typing.Optional[Folder]:
        for folder in self.folders:
            if folder.token == token:
                return folder

        return None

    def get_note_by_id(self, note_id: int) -> typing.Optional[Note]:
        return self._note_map.get(note_id, None)

    def get_note_by_token(self, token: str) -> typing.Optional[Note]:
        for note in self.notes:
            if note.token == token:
                return note

        return None

    def get_note_by_id_and_token(
        self, note_id: int, token: str
    ) -> typing.Optional[Note]:
        note = self.get_note_by_id(note_id)

        if note and note.token == token:
            return note
        else:
            return None

    def get_note_by_name(self, name: str) -> typing.Optional[Note]:
        for note in self.notes:
            if note.name == name:
                return note

        return None

    def get_note_by_room(self, room: Room) -> typing.Optional[Note]:
        for note in self.notes:
            if note.room == room:
                return note

        return None

    def get_note_by_name_and_room_name(
        self, note_name: str, room_name: str
    ) -> typing.Optional[Note]:
        for note in self.notes:
            if note.name == note_name and note.room.name == room_name:
                return note

        return None

    def get_note_by_token_and_room_name(
        self, note_token: str, room_name: str
    ) -> typing.Optional[Note]:
        for note in self.notes:
            if note.token == note_token and note.room.name == room_name:
                return note

        return None

    def get_room_by_id(self, room_id: int) -> typing.Optional[Room]:
        return self._room_map.get(room_id, None)

    def get_room_by_token(self, token: str) -> typing.Optional[Room]:
        for room in self.rooms:
            if room.token == token:
                return room

        return None

    def add_folder(
        self,
        name: str,
        index: typing.Optional[int] = None,
        folder: typing.Optional[Folder] = None,
    ) -> Folder:
        if index is None:
            index = self.get_resource_count_in_folder(folder)

        folder = Folder(
            self,
            id=self._next_folder_id,
            name=name,
            token=get_token(),
            folder=folder,
            folder_id=folder.id if folder else None,
            date=datetime.datetime.now(),
            index=index,
        )

        self.folders.append(folder)
        self._folder_map[folder.id] = folder
        self._next_folder_id += 1

        if folder.folder:
            folder.folder.folders.append(folder)

        return folder

    def add_note(
        self,
        text: str = "",
        index: typing.Optional[int] = None,
        folder: typing.Optional[Folder] = None,
        name: typing.Optional[str] = None,
    ) -> Note:
        if name is None:
            i = 1
            name = f"Note{i}"

            while self.get_note_by_name(name):
                i += 1
                name = f"Note{i}"

        if index is None:
            index = self.get_resource_count_in_folder(folder)

        room = Room(
            self,
            id=self._next_room_id,
            name=get_token(),
        )

        self.rooms.append(room)
        self._room_map[room.id] = room
        self._next_room_id += 1

        note = Note(
            self,
            id=self._next_note_id,
            name=name,
            token=get_token(),
            folder=folder,
            folder_id=folder.id if folder else None,
            date=datetime.datetime.now(),
            index=index,
            text=text,
            room=room,
            room_id=room.id,
        )

        self.notes.append(note)
        self._note_map[note.id] = note
        self._next_note_id += 1

        if note.folder:
            note.folder.notes.append(note)

        return note

    def delete_folder(self, folder: Folder) -> None:
        for nested_folder in folder.folders:
            self.delete_folder(nested_folder)

        for note in folder.notes:
            self.delete_note(note)

        if folder.folder:
            folder.folder.folders.remove(folder)

        self.folders.remove(folder)
        del self._folder_map[folder.id]

    def delete_note(self, note: Note) -> None:
        if note.room:
            self.delete_room(note.room)

        if note.folder:
            note.folder.notes.remove(note)

        self.notes.remove(note)
        del self._note_map[note.id]

    def delete_room(self, room: Room) -> None:
        self.rooms.remove(room)
        del self._room_map[room.id]

    def get_resources_in_folder(
        self,
        folder: typing.Optional[Folder],
        order_by: typing.Optional[str] = None,
        reverse: bool = False,
    ) -> typing.List[typing.Union[Folder, Note]]:
        resources = []

        if folder:
            resources = folder.folders + folder.notes
        else:
            for resource in self.folders + self.notes:
                if not resource.folder:
                    resources.append(resource)

        if order_by:
            resources.sort(
                key=lambda resource: getattr(resource, order_by), reverse=reverse
            )

        return resources

    def get_resource_count_in_folder(self, folder: typing.Optional[Folder]) -> int:
        return len(self.get_resources_in_folder(folder))

    def get_resources_with_index_gt_in_folder(
        self, folder: typing.Optional[Folder], index: int
    ) -> typing.List[typing.Union[Folder, Note]]:
        resources = []

        for resource in self.get_resources_in_folder(folder):
            if resource.index > index:
                resources.append(resource)

        return resources

    def get_resources_with_index_lt_in_folder(
        self, folder: typing.Optional[Folder], index: int
    ) -> typing.List[typing.Union[Folder, Note]]:
        resources = []

        for resource in self.get_resources_in_folder(folder):
            if resource.index < index:
                resources.append(resource)

        return resources

    def get_resources_with_index_in_range_in_folder(
        self, folder: typing.Optional[Folder], start: int, end: int
    ) -> typing.List[typing.Union[Folder, Note]]:
        resources = []

        for resource in self.get_resources_in_folder(folder):
            if start <= resource.index <= end:
                resources.append(resource)

        return resources

    def get_resource_by_id_and_token(
        self, id: int, token: str
    ) -> typing.Union[Folder, Note, None]:
        note = self.get_note_by_id(id)
        folder = self.get_folder_by_id(id)

        if note and note.token == token:
            return note
        elif folder and folder.token == token:
            return folder
        else:
            return None

    def save_to_database(self, user: Accounts):
        with transaction.atomic():
            folder_map = {}

            for folder in self.folders:
                folder_model = FolderModel(
                    user=user,
                    name=folder.name,
                    token=folder.token,
                    date=folder.date,
                    index=folder.index,
                )
                folder_model.save()
                folder_map[folder.id] = folder_model

            for folder in self.folders:
                if folder.folder and folder.folder.id in folder_map:
                    folder_model = folder_map[folder.id]
                    folder_model.folder = folder_map[folder.folder.id]
                    folder_model.save()

            room_map = {}
            for room in self.rooms:
                room_model = RoomModel(
                    user=user,
                    name=room.name,
                )
                room_model.save()
                room_map[room.id] = room_model

            for note in self.notes:
                if note.room.id in room_map:
                    note_model = NoteModel(
                        user=user,
                        name=note.name,
                        date=note.date,
                        index=note.index,
                        token=note.token,
                        room=room_map[note.room.id],
                    )

                    if note.folder and note.folder.id in folder_map:
                        note_model.folder = folder_map[note.folder.id]

                    note_model.save()

                    note_model.text_file = ContentFile(
                        note.get_text().encode(), generate_file_name(note_model)
                    )
                    note_model.save()
