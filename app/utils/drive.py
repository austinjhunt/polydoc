import pickle
import shutil
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from django.core.files.storage import default_storage
from googleapiclient.http import MediaIoBaseDownload
from django.conf import settings
import os
import json
import requests
import logging


# don't make this a method of the DriveAPI class because
# self needs to refer to the task, not the DriveAPI instance
class DriveAPI:

    def __init__(self, request=None, user_id=None):
        self.setup_logging()
        self.connected = False
        self.service = None
        self.secrets_from_json = None
        self._init_secrets()
        self.code = None
        if request:
            self.request = request
            self.user_id = request.user.id
        elif user_id:
            self.request = None
            self.user_id = user_id

        self.flow = None 
        self.token_folder = f'{settings.GOOGLE_DRIVE_FOLDER}/tokens'
        self.access_token_file = f'{self.token_folder}/user-{self.user_id}-access.pickle'
        self.scopes = ['https://www.googleapis.com/auth/drive']
        # Access token for drive resource access; to be stored in access_token_file 
        self.creds = None
        if default_storage.exists(self.access_token_file):
            self.load_creds_from_file()

    def setup_logging(self):
        """ set up self.logger for producer logging """
        self.logger = logging.getLogger('DriveAPI')

    def debug(self, msg):
        self.logger.debug(msg)

    def info(self, msg):
        self.logger.info(msg)

    def error(self, msg):
        self.logger.error(msg)

    def _init_secrets(self):
        """ In prod, uses GOOGLE_CREDENTIALS_JSON environment var content; in dev, uses drive/credentials.json """
        self.info('Initializing OAuth creds')
        try:
            self.secrets_from_json = settings.GOOGLE_CREDENTIALS_JSON
        except Exception as e:
            self.error(e)

    def refresh(self):
        """ Refresh drive authorization for user """
        success = False
        if self.creds and self.creds.expired and self.creds.refresh_token:
            # token expired so refresh
            self.info("Creds exist and are expired and refresh_token exists; refreshing")
            self.creds.refresh(Request())
            success = True
        else:
            if not self.creds:
                self.error("Creds do not exist")
            if self.creds and not self.creds.expired:
                self.error("Creds exist and are not expired")
            if self.creds and not self.creds.refresh_token:
                self.error("Creds exist and refresh_token missing")
            self.error("Not refreshing")

        return success

    def authorize(self,code=None):
        """ Update drive credentials for user """
        if not code:
            self.info(f'Requesting a new token' )
            # redirects user to google's auth endpoint which redirects to login
            # they login and then are redirected back to this app's auth view with a code
            # which can be used one time to obtain a token
            self.flow = InstalledAppFlow.from_client_config(
                client_config=settings.GOOGLE_CREDENTIALS_JSON,
                scopes=self.scopes,
                redirect_uri=settings.GOOGLE_DRIVE_AUTHENTICATE_REDIRECT_URI,
                )
        else:
            self.info('Code provided; fetching token with code')
            response = self.fetch_token(code=code)
            self.info(f'response from fetch token = {response}')
            try:
                if 'refresh_token' in response:
                    refresh_token = response['refresh_token']
                else:
                    refresh_token = None
                self.creds = Credentials(
                    token=response['access_token'],
                    refresh_token=refresh_token,
                    token_uri=self.secrets_from_json['web']['token_uri'],
                    client_id=self.secrets_from_json['web']['client_id'],
                    client_secret=self.secrets_from_json['web']['client_secret'],
                    scopes=self.scopes
                    )
                self.save_creds_to_file()
            except Exception as e:
                self.info(e)
    

    def fetch_token(self, code=None, ):
        """ Custom POST request to fetch a token from token endpoint in Google auth """
        self.info('Fetching token from Google auth token_uri')
        token_endpoint = self.secrets_from_json['web']['token_uri']
        data = {
            'code': code,
            'redirect_uri': settings.GOOGLE_DRIVE_AUTHENTICATE_REDIRECT_URI,
            'grant_type': 'authorization_code'
        }
        auth = (
            self.secrets_from_json['web']['client_id'],
            self.secrets_from_json['web']['client_secret'],
        )
        try:
            response = requests.post(token_endpoint, data=data, auth=auth).json()
            self.info(f"Token fetch response: {response}")
        except Exception as e:
            self.error(e)
            response = None 
        return response 

    def clear_user_creds(self): 
        """ Used when signing a user out of the app. no need to keep the Google token ;
        user will need to re-authorize after logging back in """
        self.info("Clearing user's google creds file")
        if default_storage.exists(self.access_token_file):
            default_storage.delete(self.access_token_file)
        else:
            self.error(f"User's creds file ({self.access_token_file}) does not exist")

    def load_creds_from_file(self):
        """ Read the creds from the file and store it in the variable self.creds"""
        if default_storage.exists(self.access_token_file):
            try:
                self.info(f"Reading creds from {self.access_token_file}")
                with default_storage.open(self.access_token_file, 'rb') as token:
                    self.creds = pickle.load(token)
            except Exception as e:
                self.error(e)
        else:
            self.error(f"{self.access_token_file} does not exist, cannot load creds")

    def save_creds_to_file(self):
        """ Save the current access token in pickle file for future usage """
        self.info(f"Saving credentials to file {self.access_token_file}")
        try:
            with default_storage.open(self.access_token_file, 'wb') as token:
                pickle.dump(self.creds, token)
            self.info(f'Successfully saved creds to {self.access_token_file}')
        except Exception as e:
            self.error(e)

    def has_valid_creds(self):
        """ set default to invalid """
        self.info("Checking for valid Drive creds")
        self.load_creds_from_file()
        valid = self.creds is not None and self.creds.valid
        self.info(f"creds valid? -> {valid}")
        return valid 

    def service_connected(self):
        """ Return whether service is active / connected """
        self.info("Checking if drive service is connected")
        c = self.service is not None
        self.info(f"Service connected? -> {c}")


    def connect_drive_service(self):
        """ Connect the drive service """
        self.info("Connecting Drive Service")
        try:
            self.service = build('drive', 'v3', credentials=self.creds)
            self.connected = True 
        except Exception as e:
            self.error(e)
            self.connected = False 
        self.info(f"Drive Service Connected? -> {self.connected}")

    def get_authorization_url(self):
        """ Get the authorization URL for drive """
        if not self.connected:
            self.info("Not connected; getting authorization URL for Drive")
            return self.flow.authorization_url()
        else:
            self.info("Already connected")

    def _export_file_as_pdf(self, file_id):
        """ Export a Doc Editors file as a PDF (only works with Docs Editors files, e.g. Slides, Document, Sheet, etc.) """
        self.info(f"Exporting file {file_id} as PDF with .export()")
        response = self.service.files().export(
                fileId=file_id, mimeType='application/pdf')
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, response, chunksize=204800)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        return fh

    def _get_file(self, file_id):
        """ Simply get a file (fallback in case export operation fails) """
        self.info(f"Getting file {file_id} with .get_media()")
        response = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, response, chunksize=204800)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        return fh

    def download_file_as_pdf(self, file_id, parent_folder_path, file_name):
        """ Download a Drive file as a PDF"""
        self.info(f'Downloading file to parent_folder_path={parent_folder_path}, file_name={file_name}')
        #response = self.service.files().get_media(fileId=file_id)
        success = False
        self.info(f'Downloading file with id={file_id}')
        fh = None
        try:
            fh = self._export_file_as_pdf(file_id)
        except Exception as e:
            self.info('Export failed for file; falling back to "get file"')
        try:
            fh = self._get_file(file_id)
        except Exception as e:
            self.info(e)
        if fh:
            fh.seek(0)
            default_storage.save(name=f'{parent_folder_path}/{file_name}', content=io.BytesIO())
            with default_storage.open(f'{parent_folder_path}/{file_name}', 'wb') as f:
                self.info(f'shutil.copyfileobj(fh, f)')
                shutil.copyfileobj(fh, f)
                self.info(f'successfully created file')
            self.info("File Downloaded")
            success = True
        return success

    def get_files_in_folder(self, folder_id):
        """ Given a folder ID, pull a list of files in that folder  """
        files_in_folder = []
        self.info(f'Getting files in folder {folder_id}')
        page_token = None
        while True:
            response = self.service.files().list(q=f"'{folder_id}' in parents",
                                                 pageSize=100,
                                                 fields='nextPageToken, files(id, name)',
                                                 pageToken=page_token).execute()
            self.info(f'Response from get files: {response}')
            for f in response.get('files', []):
                self.info(f'Appending file {f}')
                files_in_folder.append(f)
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
        return files_in_folder

    def get_folder_list(self):
        """ Get all folders on a user's drive account"""
        self.info("Getting folder list from Drive account")
        folder_list = []
        page_token = None
        folders_mimeType = 'application/vnd.google-apps.folder'
        while True:
            response = self.service.files().list(q=f"mimeType='{folders_mimeType}'",
                                                 pageSize=100,
                                                 fields='nextPageToken, files(id, name)',
                                                 pageToken=page_token).execute()
            folders = response.get('files', [])
            self.info(f"Retrieved {len(folders)} folders from Drive")
            for folder in folders:
                # each folder only has attributes id,name
                folder_list.append(folder)
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
        return folder_list
    
    def import_drive_folder(self, userid, username, folder_id, folder_name):
        from ..models import DocumentContainer, Document
        from .fileutility import FileUtility
        self.info('importing drive folder')
        if not folder_name or not folder_id:
            self.error('drive folder id or name not provided')
            return 'drive folder id or name not provided'
        if not self.has_valid_creds():
            self.refresh()
        if not self.service_connected():
            self.connect_drive_service()
        try:
            self.info(f'getting files in selected folder {folder_id}')
            files_in_selected_folder = self.get_files_in_folder(folder_id=folder_id)
            num_files = len(files_in_selected_folder)
            self.info(f'{num_files} total files in selected folder')
            # used as site-relative href value on front-end
            relative_folder_path = f'/media/documents/{username}'
            futil = FileUtility()
            full_folder_path = futil.generate_path_to_user_document_folder(username=username)
            # create a document container with same name as folder
            self.info(f'creating document container')
            document_container = DocumentContainer(
                name=folder_name,
                user_id=userid
            )
            document_container.save()
            self.info(f'created document container')
            for i, f in enumerate(files_in_selected_folder):
                self.info(f'updating progress on progress_recorder with current={i+1}, total={num_files}')
                _fname = f.get('name') + ".pdf"
                clean_filename = futil.clean_filename(filename=_fname)
                clean_filepath = f'{full_folder_path}/{clean_filename}'
                # Download file as a pdf from drive
                download_success = self.download_file_as_pdf(
                    file_id=f.get('id'),
                    parent_folder_path=full_folder_path,
                    file_name=clean_filename)

                if download_success:
                    self.info('download successful; creating doc')
                    new_doc = Document(
                        notes='',
                        title=clean_filename,
                        location=f'{relative_folder_path}/{clean_filename}',
                        user_id=userid
                    )
                    self.info('created doc')
                    # associate saved file with saved object
                    self.info(f'opening clean_filepath={clean_filepath}')
                    with default_storage.open(clean_filepath, 'rb') as file:
                        # The default behaviour of Django's Storage class
                        # is to append a series of random characters to
                        # the end of the filename when the filename already exists
                        # so delete original file after calling save()
                        self.info(f'calling new_doc.file.save({clean_filename}, file)')
                        new_doc.file.save(clean_filename, file)
                    self.info(f'removing file {clean_filepath} (extra file)')
                    futil.remove_file(clean_filepath)
                    # Update the clean_filename and clean_filepath values to reflect the rename
                    clean_filename = new_doc.get_filename()
                    clean_filepath = f'{full_folder_path}/{clean_filename}'
                    self.info(f'saving doc')
                    new_doc.save()
                    new_doc.containers.add(document_container.id)
                    new_doc.save()
                    self.info(f'creating page images(document_path={clean_filepath}')
                    new_doc.create_page_images(document_path=clean_filepath)
            result = 'Success'
        except Exception as e:
            self.error(e)
            result = f'failed: {e}'
        return result

