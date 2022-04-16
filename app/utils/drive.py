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

    def __init__(self, request=None, user_id=None, verbose=False):
        self.setup_logging(verbose=verbose)
        self.connected = False
        self.service = None
        self.secrets_from_json = None
        self._init_secrets_from_json()
        self.code = None

        if request:
            self.request = request
            self.user_id = request.user.id
        elif user_id:
            self.request = None
            self.user_id = user_id

        self.flow = None
        self.token_folder = f'{settings.GOOGLE_DRIVE_FOLDER}/tokens'
        self._ensure_folder_exists(self.token_folder)
        self.access_token_file = f'{self.token_folder}/user-{self.user_id}-access.pickle'
        self.scopes = ['https://www.googleapis.com/auth/drive']
        # Access token for drive resource access; to be stored in access_token_file 
        self.creds = None
        if os.path.exists(self.access_token_file):
            self.load_creds_from_file()

    def setup_logging(self, verbose):
        """ set up self.logger for producer logging """
        self.logger = logging.getLogger('DriveAPI')
        formatter = logging.Formatter('%(prefix)s - %(message)s')
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.prefix = {'prefix': 'DriveAPI'}
        self.logger.addHandler(handler)
        self.logger = logging.LoggerAdapter(self.logger, self.prefix )
        if verbose:
            self.logger.setLevel(logging.DEBUG)
            self.logger.debug('Debug mode enabled', extra=self.prefix )
        else:
            self.logger.setLevel(logging.INFO)

    def debug(self, msg):
        self.logger.debug(msg, extra=self.prefix)

    def info(self, msg):
        self.logger.info(msg, extra=self.prefix)

    def error(self, msg):
        self.logger.error(msg, extra=self.prefix)

    def _init_secrets_from_json(self):
        with open(settings.GOOGLE_DRIVE_CREDENTIALS_JSON_FILE, 'r') as f:
            self.secrets_from_json = dict(json.load(f))['web']

    def _ensure_folder_exists(self, path):
        """ Given a path to a folder, ensure it exists"""
        if not os.path.exists(path):
            os.makedirs(path)

    def refresh(self):
        """ Refresh drive authorization for user """
        success = False
        if self.creds and self.creds.expired and self.creds.refresh_token:
            # token expired so refresh
            self.creds.refresh(Request())
            success = True
        return success

    def authorize(self,code=None):
        """ Update drive credentials for user """
        if not code:
            # request a new token
            # redirects user to google's auth endpoint which redirects to login
            # they login and then are redirected back to this app's auth view with a code
            # which can be used one time to obtain a token
            self.flow = InstalledAppFlow.from_client_secrets_file(
                settings.GOOGLE_DRIVE_CREDENTIALS_JSON_FILE, self.scopes,
                redirect_uri=settings.GOOGLE_DRIVE_AUTHENTICATE_REDIRECT_URI,
                )
        else:
            print('code provided; fetching token with code')
            response = self.fetch_token(code=code)
            print(f'response from fetch token = {response}')
            try:
                if 'refresh_token' in response:
                    refresh_token = response['refresh_token']
                else:
                    refresh_token = None
                self.creds = Credentials(
                    token=response['access_token'],
                    refresh_token=refresh_token,
                    token_uri=self.secrets_from_json['token_uri'],
                    client_id=self.secrets_from_json['client_id'],
                    client_secret=self.secrets_from_json['client_secret'],
                    scopes=self.scopes
                    )
                self.save_creds_to_file()
            except Exception as e:
                print(e)
    

    def fetch_token(self, code=None, ):
        """ Custom POST request to fetch a token from token endpoint in Google auth """
        token_endpoint = self.secrets_from_json['token_uri']
        data = {
            'code': code,
            'redirect_uri': settings.GOOGLE_DRIVE_AUTHENTICATE_REDIRECT_URI,
            'grant_type': 'authorization_code'
        }
        auth = (
            self.secrets_from_json['client_id'],
            self.secrets_from_json['client_secret'],
        )
        return requests.post(token_endpoint, data=data, auth=auth).json()

    def clear_user_creds(self): 
        """ Used when signing a user out of the app. no need to keep the Google token ;
        user will need to re-authorize after logging back in """
        self.info("Clearing user's google creds file")
        if default_storage.exists(self.access_token_file):
            default_storage.delete(self.access_token_file)

    def load_creds_from_file(self):
        # Read the token from the file and
        # store it in the variable self.creds
        if os.path.exists(self.access_token_file):
            with open(self.access_token_file, 'rb') as token:
                self.creds = pickle.load(token)

    def save_creds_to_file(self):
        """ Save the current access token in pickle file for future usage """
        with open(self.access_token_file, 'wb') as token:
            pickle.dump(self.creds, token)

    def has_valid_creds(self):
        """ set default to invalid """
        self.load_creds_from_file()
        return self.creds is not None and self.creds.valid

    def service_connected(self):
        """ Return whether service is active / connected """
        return self.service is not None

    def connect_drive_service(self):
        """ Connect the drive service """
        self.service = build('drive', 'v3', credentials=self.creds)
        self.connected = True

    def get_authorization_url(self):
        if not self.connected:
            return self.flow.authorization_url()

    def _export_file_as_pdf(self, file_id):
        """ Export a Doc Editors file as a PDF (only works with Docs Editors files, e.g. Slides, Document, Sheet, etc.) """
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
        response = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, response, chunksize=204800)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        return fh

    def download_file_as_pdf(self, file_id, parent_folder_path, file_name):
        """ Download a Drive file as a PDF"""
        print(f'Downloading file to parent_folder_path={parent_folder_path}, file_name={file_name}')
        #response = self.service.files().get_media(fileId=file_id)
        success = False
        print(f'Downloading file with id={file_id}')
        fh = None
        try:
            fh = self._export_file_as_pdf(file_id)
        except Exception as e:
            print('Export failed for file; falling back to "get file"')
        try:
            fh = self._get_file(file_id)
        except Exception as e:
            print(e)
        if fh:
            fh.seek(0)
            default_storage.save(name=f'{parent_folder_path}/{file_name}', content=io.BytesIO())
            with default_storage.open(f'{parent_folder_path}/{file_name}', 'wb') as f:
                print(f'shutil.copyfileobj(fh, f)')
                shutil.copyfileobj(fh, f)
                print(f'successfully created file')
            print("File Downloaded")
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
        folder_list = []
        page_token = None
        folders_mimeType = 'application/vnd.google-apps.folder'
        while True:
            response = self.service.files().list(q=f"mimeType='{folders_mimeType}'",
                                                 pageSize=100,
                                                 fields='nextPageToken, files(id, name)',
                                                 pageToken=page_token).execute()
            for folder in response.get('files', []):
                # each folder only has attributes id,name
                folder_list.append(folder)
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break

        return folder_list

    def get_folder_id(self, folder_name):
        if self.service == None:
            print("App not authenticated")
            return "0"
        response = self.service.files().list(q="mimeType='application/vnd.google-apps.folder' and trashed=false",
                                             fields='nextPageToken, files(id, name)').execute()
        print(response.get('files'))
        for folder in response.get('files'):
            print(f"Comparing \"{folder.get('name')}\" with \"{folder_name}\"")
            if folder.get('name') == folder_name:
                folder_id = folder.get('id')
                print(folder_id)
                return folder_id
        return "0"
