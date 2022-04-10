from django.conf import settings
from django.core.files.storage import default_storage
class FileUtility:
    def __init__(self):
        self.s3_storage_active = (not settings.DEBUG)

    def get_document_object_file_location(self, document_object, use_site_relative_path=False):
        """ Provided a Document object, return the file location using s3_storage_active boolean
        to determine whether to use absolute or relative path. If use_site_relative_path=True, must use relative. """

        if self.s3_storage_active:
            path = document_object.location.replace('/media/', 'media/')
        elif use_site_relative_path:
            # Document object location attribute is relative already (/media/documents/user/file.pdf)
            path = document_object.location
        else:
            path = document_object.location.replace('/media/', f'{settings.MEDIA_ROOT}/')
        return path

    def generate_path_to_user_document_folder(self, username, use_site_relative_path=False):
        """ Each user has their own folder (named with their username) in media/documents/;
        use s3_storage_active boolean to determine if absolute or relative path.
        If use_site_relative_path=True, must use relative. """
        if self.s3_storage_active:
            path = f'media/documents/{username}'
        elif use_site_relative_path:
            path = f'/media/documents/{username}'
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
        print(f'Recursively removing folder {folder_path}')
        dirs, files = default_storage.listdir(folder_path)
        for file in files:
            filepath = f'{folder_path}{file}'
            print(f'deleting {filepath}')
            default_storage.delete(filepath)
        for dir in dirs:
            new_dir = f'{folder_path}{dir}/'
            print(f'going to new dir {new_dir}')
            self.remove_folder_recursive(new_dir)


    def remove_file(self, path):
        """ remove a file """
        try:
            default_storage.delete(path)
        except Exception as e:
            print(e)


def clean_and_shorten_filename(filename):
    # Shorten filename if longer than 15 chars. Otherwise it causes problems.
    _extension = filename.split('.')[-1]
    end_index = min(15, len(filename)-(len(_extension) + 1))
    filename = f'{filename[:end_index]}.{_extension}'
    return filename.replace(' ','-').strip().lower()


