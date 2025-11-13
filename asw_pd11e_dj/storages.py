from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings


class TemporaryS3Boto3Storage(S3Boto3Storage):
    """
    Custom S3 storage that works with temporary AWS credentials.
    """
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    access_key = settings.AWS_ACCESS_KEY_ID
    secret_key = settings.AWS_SECRET_ACCESS_KEY
    session_token = settings.AWS_SESSION_TOKEN
    default_acl = "public-read"  # optional, so files are accessible
