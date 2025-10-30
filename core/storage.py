"""
MinIO storage backends for different file types
"""
from storages.backends.s3boto3 import S3Boto3Storage


class MinIOStorage(S3Boto3Storage):
    """Base MinIO storage class"""
    bucket_name = 'sauvini'
    custom_domain = None
    file_overwrite = False


class ProfessorStorage(MinIOStorage):
    """Storage for professor files (CVs, etc.)"""
    bucket_name = 'professors'
    location = 'professors'


class ProfilePictureStorage(MinIOStorage):
    """Storage for profile pictures"""
    bucket_name = 'profile-pictures'
    location = 'profile-pictures'


class ModuleStorage(MinIOStorage):
    """Storage for module files (images, etc.)"""
    bucket_name = 'modules'
    location = 'modules'


class LessonStorage(MinIOStorage):
    """Storage for lesson files (videos, PDFs)"""
    bucket_name = 'lessons'
    location = 'lessons'
