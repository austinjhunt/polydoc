from django.conf import settings
from django.core.files.storage import default_storage
import logging 
logger = logging.getLogger('FileUtility')
class FileUtility:
    def __init__(self):
        self.s3_storage_active = (not settings.DEBUG)

    def get_document_object_file_location(self, document_object):
        """ Provided a Document object, return the file location using s3_storage_active boolean
        to determine whether to use absolute or relative path. """

        if self.s3_storage_active:
            path = document_object.location.replace('/media/', 'media/')
        else:
            path = document_object.location.replace('/media/', f'')
        return path

    def generate_path_to_user_document_folder(self, username):
        """ Each user has their own folder (named with their username) in media/documents/;
        use s3_storage_active boolean to determine if absolute or relative path. """
        if self.s3_storage_active:
            path = f'media/documents/{username}'
        else:
            path = f'{settings.MEDIA_ROOT}/documents/{username}'
        return path

    def clean_filename(self, filename):
        """ Clean up a filename to avoid naming / character / length issues """
        if len(filename) > 15:
            # Shorten filename if longer than 15 chars. Otherwise it causes problems.
            _extension = filename.split('.')[-1]
            end_index = min(15, len(filename)-(len(_extension) + 1))
            filename = f'{filename[:end_index]}.{_extension}'
        return filename.replace(' ', '-').strip().lower()

    def remove_folder_recursive(self, folder_path):
        """ recursively remove a folder given its path """
        logger.info(f'Recursively removing folder {folder_path}')
        try:
            dirs, files = default_storage.listdir(folder_path)
            if not folder_path.endswith('/'):
                folder_path = f'{folder_path}/'
            for file in files:
                filepath = f'{folder_path}{file}'
                logger.info(f'deleting {filepath}')
                default_storage.delete(filepath)
            for dir in dirs:
                new_dir = f'{folder_path}{dir}/'
                self.remove_folder_recursive(new_dir)
            self.remove_file(folder_path)
        except FileNotFoundError as e:
            logger.error(f'File not found. Not deleting {folder_path}')


    def remove_file(self, path):
        """ remove a file """
        try:
            logger.info(f'Removing file {path}')
            default_storage.delete(path)
        except Exception as e:
            logger.error(e)