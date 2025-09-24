from typing import Optional

from account.models import Accounts
from texteditor.models import Folder, Note


def count_folders_in_folder(folder: Optional[Folder], user: Accounts) -> int:
    return Folder.objects.filter(folder=folder, user=user).count()


def count_notes_in_folder(folder: Optional[Folder], user: Accounts) -> int:
    return Note.objects.filter(folder=folder, user=user).count()


def count_resources_in_folder(folder: Optional[Folder], user: Accounts) -> int:
    return count_folders_in_folder(folder, user) + count_notes_in_folder(folder, user)
