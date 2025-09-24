from texteditor.models import Folder


def get_folder_history(folder, only_public=False, with_current_folder=False):
    previous_folders = list()
    prev_folder = folder

    if not with_current_folder:
        prev_folder = folder.folder if folder else None

    while prev_folder:
        previous_folders.insert(0, prev_folder)
        if only_public:
            if prev_folder.folder and prev_folder.folder.is_public:
                prev_folder = prev_folder.folder
            else:
                prev_folder = None
        else:
            prev_folder = prev_folder.folder

    return previous_folders


def get_next_folders(folder, only_public=False):
    next_folders = list()
    current_folders = Folder.objects.filter(folder=folder)

    while current_folders:
        next_folders.extend(current_folders)
        temp_folders = [*current_folders]
        current_folders.clear()
        for folder in temp_folders:
            if only_public:
                temp_folder = Folder.objects.filter(folder=folder, is_public=True)
                current_folders.extend(temp_folder)
            else:
                temp_folder = Folder.objects.filter(folder=folder)
                current_folders.extend(temp_folder)
    return next_folders
