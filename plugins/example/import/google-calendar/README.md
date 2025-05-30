# Google Calendar to OMI Import Plugin

This plugin allows importing Google Calendar events into OMI as memories.

## Setup

1. Create a project in Google Cloud Console
2. Enable Google Calendar API
3. Create OAuth 2.0 credentials
4. Download client_secrets.json and place in config/
5. Copy .env.example to .env and fill in your values

## Installation

```bash
pip install -r requirements.txt
```

## Running

```bash
python app.py
```

Access at: http://localhost:5002/?uid=YOUR_OMI_USER_ID
