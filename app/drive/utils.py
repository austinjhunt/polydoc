import os.path
import pickle
import shutil
import io

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from googleapiclient.errors import HttpError

class DriveAPI:

    connected = False

    def __init__(self):
        self.scopes = ['https://www.googleapis.com/auth/drive']

        # Variable self.creds will
        # store the user access token.
        # If no valid token found
        # we will create one.
        self.creds = None

        # The file token.pickle stores the
        # user's access and refresh tokens. It is
        # created automatically when the authorization
        # flow completes for the first time.

        # Check if file token.pickle exists
        if os.path.exists('token.pickle'):

            # Read the token from the file and
            # store it in the variable self.creds
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)

        # If no valid credentials are available,
        # request the user to log in.
        if not self.creds or not self.creds.valid:

            # If token is expired, it will be refreshed,
            # else, we will request a new one.
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                self.flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.scopes,
                #     redirect_uri="https://poly-doc.herokuapp.com/profile")
                #    redirect_uri="http://localhost:8000/authenticate")
                    redirect_uri="https://poly-doc.herokuapp.com:50005/authenticate")

                #self.creds = flow.credentials.to_json()
                return
                '''print(self.flow.authorization_url())
                self.creds = self.flow.run_local_server(port=50005)
                #flow.fetch_token()
                #self.creds = flow.credentials()
                print("Done authenticating")
                '''

            # Save the access token in token.pickle
            # file for future usage
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)

        # Connect to the API service
        self.service = build('drive', 'v3', credentials=self.creds)
        self.connected = True

    def authenticate(self, code):
        if not self.creds or not self.creds.valid:
            # If token is expired, it will be refreshed,
            # else, we will request a new one.
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                self.flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.scopes,
                #     redirect_uri="https://poly-doc.herokuapp.com/profile")
                    redirect_uri="http://localhost:8000/authenticate")
    
                authorization_response = "https://localhost:8000/profile"

                print(f"authorization_response: {authorization_response}\ncode: {code}")
                token = self.flow.fetch_token(authorization_response=authorization_response, code=code)
                print(f"token: {token}")

                session = self.flow.authorized_session()
                print(f"session: {session.credentials}")

                #self.creds = self.flow.run_local_server(port=50005)
                self.creds = session.credentials
                #flow.fetch_token()
                #self.creds = flow.credentials()
                print("Done authenticating")

            # Save the access token in token.pickle
            # file for future usage
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)

        print(f"Creds: {self.creds}")
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
        if self.service = None:
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
