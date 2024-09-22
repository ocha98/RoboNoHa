import os
from atproto import Client
from dotenv import load_dotenv

load_dotenv()

BLUESKY_HANDLE = os.getenv('BLUESKY_HANDLE')
BLUESKY_APP_PASS = os.getenv('BLUESKY_APP_PASS')

def get_bluesky_session():
    bsky_client = Client()
    bsky_client.login(BLUESKY_HANDLE, BLUESKY_APP_PASS)
    return bsky_client.export_session_string()


