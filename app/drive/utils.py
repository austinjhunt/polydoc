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
        self.secrets_from_json = None
        self._init_secrets_from_json()
        self.code = None
        self.request = request
        self.user_id = request.user.id
        self.flow = None
        self.token_folder = f'{settings.GOOGLE_DRIVE_FOLDER}/tokens'
        self._ensure_folder_exists(self.token_folder)
        self.token_file = f'{self.token_folder}/user-{self.user_id}.pickle'
        self.scopes = ['https://www.googleapis.com/auth/drive']
        # Access token for drive resource access
        self.creds = None

        # The file token.pickle stores the
        # user's access and refresh tokens. It is
        # created automatically when the authorization
        # flow completes for the first time.

        if os.path.exists(self.token_file):
            self.load_creds_from_file()

    def _init_secrets_from_json(self):
        with open(settings.GOOGLE_DRIVE_CREDENTIALS_JSON_FILE, 'r') as f:
            self.secrets_from_json = dict(json.load(f))['web']

    def _ensure_folder_exists(self, path):
        """ Given a path to a folder, ensure it exists"""
        if not os.path.exists(path):
            os.makedirs(path)

    def authorize(self,code=None):
        """ Update drive credentials for user """
        if self.creds and self.creds.expired and self.creds.refresh_token:
            # token expired so refresh
            self.creds.refresh(Request())
        else:
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
                    self.creds = Credentials(
                        token=response['access_token'],
                        refresh_token=response['refresh_token'],
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
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                self.creds = pickle.load(token)

    def save_creds_to_file(self):
        """ Save the current access token in pickle file for future usage """
        with open(self.token_file, 'wb') as token:
            pickle.dump(self.creds, token)

    def has_valid_creds(self):
        """ set default to invalid """
        self.load_creds_from_file()
        return self.creds is not None and self.creds.valid


    def connect_drive_service(self):
        self.service = build('drive', 'v3', credentials=self.creds)
        self.connected = True

    def get_authorization_url(self):
        if not self.connected:
            return self.flow.authorization_url()

    def get_file(self, file_id, file_path, file_name):
        #response = self.service.files().get_media(fileId=file_id)
        response = self.service.files().export(
            fileId=file_id, mimeType='application/pdf')
        print(response.to_json())
        fh = io.BytesIO()

        # Initialise a downloader object to download the file
        downloader = MediaIoBaseDownload(fh, response, chunksize=204800)
        #downloader = MediaIoBaseDownload(fh, response, mimetype='application/pdf')
        done = False

        try:
            # Download the data in chunks
            while not done:
                status, done = downloader.next_chunk()

            fh.seek(0)

            if not os.path.exists(file_path):
                os.makedirs(file_path)

            # Write the received data to the file
            with open(f'{file_path}/{file_name}', 'wb') as f:
                shutil.copyfileobj(fh, f)

            print("File Downloaded")
            # Return True if file Downloaded successfully
            return True
        except Exception as e:

            # Return False if something went wrong
            print("Something went wrong.")
            raise e

    def get_folder_list(self, folder_id):
        files_in_folder = []
        page_token = None

        while True:
            response = self.service.files().list(q=f"'{folder_id}' in parents",
                                                 pageSize=100,
                                                 fields='nextPageToken, files(id, name)',
                                                 pageToken=page_token).execute()
            for file in response.get('files', []):
                # Process change
                print('Found file: %s (%s)' %
                      (file.get('name'), file.get('id')))

                # Could likely append response.get('files', []) to list, but this allows us to also print to console in one go
                files_in_folder.append(file)

            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break

        return files_in_folder

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
