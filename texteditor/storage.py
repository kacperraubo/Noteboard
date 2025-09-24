from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class PrivateMediaStorage(S3Boto3Storage):
    bucket_name = (
        "dev-nb-s33-83928491491" if settings.DEBUG else "nb-s33-88444666337"
    )
    location = " "
