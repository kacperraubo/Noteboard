
from texteditor.storage import PrivateMediaStorage


def upload_file_to_aws(full_filename, file):
    media_storage = PrivateMediaStorage()
    media_storage.save(full_filename, file)


def remove_file_from_aws(source):
    media_storage = PrivateMediaStorage()
    try:
        media_storage.delete(f"{source}")
        return True
    except Exception as e:
        print(str(e))
        return False


def download_file_from_aws(source):

    with PrivateMediaStorage().open(str(source)) as s3_file:
        return s3_file
