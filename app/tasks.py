""" Celery tasks - asynchronous processes e.g. for progress bars """
from django.core.files.storage import default_storage
from celery import shared_task
from celery_progress.backend import ProgressRecorder
import traceback
import sys
from .utils.fileutility import FileUtility
from .utils.drive import DriveAPI
import logging
from celery.utils.log import get_task_logger
from .models import Document, DocumentContainer
# don't make this a method of the DriveAPI class because
# self needs to refer to the task, not the DriveAPI instance
logger = get_task_logger(__name__)
logger.addHandler(logging.FileHandler(filename='celery-tasks.log'))

@shared_task(bind=True)
def import_drive_folder(self, userid, username, folder_id, folder_name):
    logger.info('importing drive folder')
    drive = DriveAPI(user_id=userid)
    progress_recorder = ProgressRecorder(self)
    if not folder_name or not folder_id:
        logger.error('drive folder id or name not provided')
        return 'drive folder id or name not provided'
    if not drive.has_valid_creds():
        logger.error('drive not connected')
        return 'drive not connected'
    if not drive.service_connected():
        drive.connect_drive_service()
    try:
        files_in_selected_folder = drive.get_files_in_folder(folder_id=folder_id)
        num_files = len(files_in_selected_folder)
        # used as site-relative href value on front-end
        relative_folder_path = f'/media/documents/{username}'
        futil = FileUtility()
        full_folder_path = futil.generate_path_to_user_document_folder(username=username)
        # create a document container with same name as folder
        document_container = DocumentContainer(
            name=folder_name,
            user_id=userid
        )
        document_container.save()
        for i, f in enumerate(files_in_selected_folder):
            logger.info(f'updating progress on progress_recorder with current={i+1}, total={num_files}')
            progress_recorder.set_progress(current=i+1, total=num_files, description=f'Importing {i+1} of {num_files} files')
            _fname = f.get('name') + ".pdf"
            clean_filename = futil.clean_filename(filename=_fname)
            clean_filepath = f'{full_folder_path}/{clean_filename}'
            # Download file as a pdf from drive
            download_success = drive.download_file_as_pdf(
                file_id=f.get('id'),
                parent_folder_path=full_folder_path,
                file_name=clean_filename)

            if download_success:
                logger.info('download successful; creating doc')
                new_doc = Document(
                    notes='',
                    title=clean_filename,
                    location=f'{relative_folder_path}/{clean_filename}',
                    user_id=userid
                )
                logger.info('created doc')
                # associate saved file with saved object
                logger.info(f'opening clean_filepath={clean_filepath}')
                with default_storage.open(clean_filepath, 'rb') as file:
                    # The default behaviour of Django's Storage class
                    # is to append a series of random characters to
                    # the end of the filename when the filename already exists
                    # so delete original file after calling save()
                    logger.info(f'calling new_doc.file.save({clean_filename}, file)')
                    new_doc.file.save(clean_filename, file)
                logger.info(f'removing file {clean_filepath} (extra file)')
                futil.remove_file(clean_filepath)
                # Update the clean_filename and clean_filepath values to reflect the rename
                clean_filename = new_doc.get_filename()
                clean_filepath = f'{full_folder_path}/{clean_filename}'
                logger.info(f'saving doc')
                new_doc.save()
                new_doc.containers.add(document_container.id)
                new_doc.save()
                logger.info(f'creating page images(document_path={clean_filepath}')
                new_doc.create_page_images(document_path=clean_filepath)
        result = 'Success'
    except Exception as e:
        logger.error(e)
        logger.error("-"*60)
        traceback.print_exc(file=sys.stdout)
        logger.error("-"*60)
        result = f'failed: {e}'
    return result

