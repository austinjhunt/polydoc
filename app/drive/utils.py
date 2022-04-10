import pickle
import shutil
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from django.conf import settings
import os
import json
import requests

class DriveAPI:


    def __init__(self, request):
        self.connected = False
        self.service = None
        self.secrets_from_json = None
        self._init_secrets_from_json()
        self.code = None
        self.request = request
        self.user_id = request.user.id
        self.flow = None
        self.token_folder = f'{settings.GOOGLE_DRIVE_FOLDER}/tokens'
        self._ensure_folder_exists(self.token_folder)
        self.access_token_file = f'{self.token_folder}/user-{self.user_id}-access.pickle'
        self.refresh_token_file = f'{self.token_folder}/user-{self.user_id}-refresh.pickle'
        self.scopes = ['https://www.googleapis.com/auth/drive']
        # Access token for drive resource access
        self.creds = None

        # The file token.pickle stores the
        # user's access and refresh tokens. It is
        # created automatically when the authorization
        # flow completes for the first time.

        if os.path.exists(self.access_token_file):
            self.load_creds_from_file()

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
            # request a new token ; this will trigger AuthView which updates request.session['drivecode']
            # redirects user to google's auth endpoint which redirects to login
            # they login and then are redirected back to this app's auth view with a code
            # which can be used one time to obtain a token
            self.flow = InstalledAppFlow.from_client_secrets_file(
                settings.GOOGLE_DRIVE_CREDENTIALS_JSON_FILE, self.scopes,
                redirect_uri=settings.GOOGLE_DRIVE_AUTHENTICATE_REDIRECT_URI,
                )
        else:
            print('code provided; fetching token with code')
            # request a new token ; this will trigger AuthView which updates request.session['drivecode']
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
        print(f'fetching token')
        print(f' data={data}')
        print(f'client id = {self.secrets_from_json["client_id"][:6]}...')
        return requests.post(token_endpoint, data=data, auth=auth).json()


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
        print(response.to_json())
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, response, chunksize=204800)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        return fh

    def download_file_as_pdf(self, file_id, parent_folder_path, file_name):
        #response = self.service.files().get_media(fileId=file_id)
        success = False
        print(f'Downloading file with id={file_id}')
        fh = None
        try:
            fh = self._export_file_as_pdf(file_id)
        except Exception as e:
            print('export file only works for Doc Editor files; fallback to "get file"')
        try:
            fh = self._get_file(file_id)
        except Exception as e:
            print(e)
        if fh:
            fh.seek(0)
            if not os.path.exists( parent_folder_path):
                os.makedirs( parent_folder_path)
            # Write the received data to the file
            with open(f'{parent_folder_path}/{file_name}', 'wb') as f:
                shutil.copyfileobj(fh, f)
            print("File Downloaded")
            success = True
        return success


    def get_files_in_folder(self, folder_id):
        """ Given a folder ID, pull a list of files in that folder  """
        files_in_folder = []
        page_token = None
        while True:
            response = self.service.files().list(q=f"'{folder_id}' in parents",
                                                 pageSize=100,
                                                 fields='nextPageToken, files(id, name)',
                                                 pageToken=page_token).execute()
            for f in response.get('files', []):
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


'''
folderId = drive.files().list(q = "mimeType = 'application/vnd.google-apps.folder' and name = 'thumbnails'", pageSize=10, fields="nextPageToken, files(id, name)").execute()
# this gives us a list of all folders with that name
folderIdResult = folderId.get('files', [])
# however, we know there is only 1 folder with that name, so we just get the id of the 1st item in the list
id = folderIdResult[0].get('id')

# Now, using the folder ID gotten above, we get all the files from
# that particular folder
results = drive.files().list(q = "'" + id + "' in parents", pageSize=10, fields="nextPageToken, files(id, name)").execute()
items = results.get('files', [])

# Now we can loop through each file in that folder, and do whatever (in this case, download them and open them as images in OpenCV)
for f in range(0, len(items)):
    fId = items[f].get('id')
    fileRequest = drive.files().get_media(fileId=fId)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, fileRequest)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
    fh.seek(0)
    fhContents = fh.read()

    baseImage = cv2.imdecode(np.fromstring(fhContents, dtype=np.uint8), cv2.IMREAD_COLOR)
'''
