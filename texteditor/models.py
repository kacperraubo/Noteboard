from __future__ import annotations

import secrets

from django.db import models

from account.models import Accounts
from texteditor.storage import PrivateMediaStorage
from utilities.aws import download_file_from_aws


def generate_file_name(note: Note):
    return f"{note.user.id}/{secrets.token_hex(16)}"


# Create your models here.
def note_upload_to(instance, filename):
    return generate_file_name(instance)


def get_token():
    return secrets.token_urlsafe(16)


class Room(models.Model):
    user = models.ForeignKey(Accounts, on_delete=models.CASCADE)
    name = models.CharField(max_length=32, null=True, blank=True, unique=True)
    is_editable = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name}"


class Folder(models.Model):
    user = models.ForeignKey(Accounts, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    token = models.CharField(max_length=100, default=get_token, unique=True)
    folder = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="folders"
    )
    date = models.DateTimeField(auto_now_add=True, null=True)
    index = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.name}"


class Canvas(models.Model):
    file = models.FileField(
        upload_to=note_upload_to, storage=PrivateMediaStorage, null=True, blank=True
    )
    background = models.CharField(max_length=7, default="#FBFCFF")

    @property
    def user(self):
        return self.note.user


class DefaultDisplay(models.TextChoices):
    TEXT = "text"
    CANVAS = "canvas"


class Note(models.Model):
    user = models.ForeignKey(Accounts, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=60)
    text_file = models.FileField(
        upload_to=note_upload_to, storage=PrivateMediaStorage, null=True, blank=True
    )
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True, null=True)
    token = models.CharField(max_length=100, default=get_token, unique=True)
    index = models.PositiveIntegerField(default=0)
    canvas_file = models.OneToOneField(Canvas, on_delete=models.CASCADE, related_name="note")
    display = models.CharField(
        max_length=6, choices=DefaultDisplay.choices, default=DefaultDisplay.TEXT
    )

    def __str__(self):
        return f"{self.name}"

    def get_text(self):
        if self.text_file:
            try:
                file = download_file_from_aws(self.text_file)
                return file.read().decode("utf-8")
            except Exception:
                return ""

        return ""
