import os
import google.auth
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from flask import Flask, redirect, url_for, session, request, jsonify
from flask_session import Session

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key')
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']
REDIRECT_URI = os.environ.get('REDIRECT_URI')

@app.route('/')
def index():
    return 'Welcome to the Google Drive API Flask app!'

@app.route('/authorize')
def authorize():
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES)
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        redirect_uri=REDIRECT_URI)  # Adicione redirect_uri aqui
    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    state = session['state']
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES, state=state)
    flow.fetch_token(authorization_response=request.url, redirect_uri=REDIRECT_URI)  # Adicione redirect_uri aqui

    creds = flow.credentials
    session['credentials'] = creds_to_dict(creds)
    return redirect(url_for('list_files'))

@app.route('/list_files')
def list_files():
    if 'credentials' not in session:
        return redirect('authorize')

    creds = Credentials(**session['credentials'])
    service = build('drive', 'v3', credentials=creds)

    results = service.files().list(
        pageSize=10, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        return 'No files found.'
    else:
        files_list = [{'name': item['name'], 'id': item['id']} for item in items]
        return jsonify(files_list)

def creds_to_dict(creds):
    return {'token': creds.token, 'refresh_token': creds.refresh_token, 'token_uri': creds.token_uri, 'client_id': creds.client_id, 'client_secret': creds.client_secret, 'scopes': creds.scopes}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
