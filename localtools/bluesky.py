import os
from atproto import Client
from dotenv import load_dotenv
import time
from lib import cleaing_txt

load_dotenv()

BLUESKY_HANDLE = os.getenv('BLUESKY_HANDLE')
BLUESKY_APP_PASS = os.getenv('BLUESKY_APP_PASS')
BLUESKY_SESSION = os.getenv('BLUESKY_SESSION')

bsky_client = Client()
bsky_client.login(session_string = BLUESKY_SESSION)

def get_bluesky_session():
    return bsky_client.export_session_string()

def get_all_posts():
    me = bsky_client.me
    cursor = None
    posts = []
    while True:
        res = bsky_client.get_author_feed(me.did, cursor = cursor, limit = 100)
        cursor = res.cursor
        for post in res.feed:
            posts.append(post.post.record.text)
        print(len(posts))
        if cursor is None:
            break
        time.sleep(1)

    with open('all_blue_sky_posts.txt', 'w') as f:
        f.write('\n'.join(posts))
        f.write('\n')

    clean_posts = []
    for txt in posts:
        txt = cleaing_txt(txt)

        if len(txt) == 0:
            continue
        clean_posts.append(txt)

    with open('clean_bluesky_posts.txt', 'w') as f:
        f.write('\n'.join(clean_posts))
        f.write('\n')
