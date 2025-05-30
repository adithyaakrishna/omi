from flask import Flask, request, jsonify, redirect, session, url_for, render_template
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# OMI API Configuration
APP_ID = os.getenv('OMI_APP_ID')
API_KEY = os.getenv('OMI_API_KEY')
API_URL = f"https://api.omi.me/v2/integrations/{APP_ID}/user/facts"

# Google Calendar API Configuration
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
CLIENT_SECRETS_FILE = "config/client_secrets.json"

@app.route('/')
def index():
    # Get user_id from query parameter to pass to template
    user_id = request.args.get('uid')
    if user_id:
        # If user_id is provided, store it in session
        session['user_id'] = user_id
        return render_template('index.html')
    else:
        return jsonify({"error": "No user ID provided. Please include 'uid' in your URL parameters."}), 400

@app.route('/authorize')
def authorize():
    # Get user_id from session
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "No user ID found in session. Please start from the homepage."}), 400
    
    # Create flow instance to manage OAuth 2.0 Authorization Grant Flow
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    
    # Generate URL for request to Google's OAuth 2.0 server
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    
    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    state = session['state']
    user_id = session.get('user_id')
    
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=state,
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    
    # Use the authorization server's response to fetch the OAuth 2.0 tokens
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials
    
    # Store credentials in session
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    
    return redirect(url_for('import_events'))

@app.route('/import-events')
def import_events():
    if 'credentials' not in session:
        return redirect(url_for('authorize'))
    
    # Get credentials from session
    credentials = Credentials(**session['credentials'])
    
    # Build the Google Calendar API service
    service = build('calendar', 'v3', credentials=credentials)
    
    # Get events from the last 30 days
    now = datetime.utcnow()
    start_time = (now - timedelta(days=30)).isoformat() + 'Z'
    end_time = now.isoformat() + 'Z'
    
    events_result = service.events().list(
        calendarId='primary',
        timeMin=start_time,
        timeMax=end_time,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])
    
    if not events:
        return render_template('success.html', 
                             total_events=0,
                             memories_created=0,
                             success_rate=0)
    
    # Process events and create memories
    memories = []
    success_count = 0
    
    # Submit memories to OMI
    user_id = session.get('user_id')
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    for event in events:
        # Extract relevant information
        start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date'))
        end = event.get('end', {}).get('dateTime', event.get('end', {}).get('date'))
        summary = event.get('summary', 'Untitled Event')
        description = event.get('description', '')
        location = event.get('location', '')
        
        # Create memory text
        memory_text = f"Calendar Event: {summary}"
        if description:
            memory_text += f". Notes: {description}"
        if location:
            memory_text += f". Location: {location}"
        memory_text += f". Time: {start} to {end}"
        
        memory_data = {
            "text": memory_text,
            "text_source": "google_calendar",
            "text_source_spec": "event"
        }
        
        response = requests.post(
            f"{API_URL}?uid={user_id}",
            headers=headers,
            json=memory_data
        )
        
        if response.status_code == 200:
            success_count += 1
        
        memories.append({
            "text": memory_text,
            "success": response.status_code == 200
        })
    
    # Calculate statistics
    total_events = len(events)
    memories_created = success_count
    success_rate = round((success_count / total_events) * 100) if total_events > 0 else 0
    
    # Render the success template with the results
    return render_template('success.html',
                         total_events=total_events,
                         memories_created=memories_created,
                         success_rate=success_rate)

@app.errorhandler(Exception)
def handle_error(error):
    app.logger.error(f"An error occurred: {str(error)}")
    return jsonify({
        "error": "An unexpected error occurred. Please try again later.",
        "details": str(error)
    }), 500

if __name__ == '__main__':
    # When running locally, disable OAuthlib's HTTPs verification
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run('localhost', 5002, debug=True)
