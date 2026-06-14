import os
from atproto import Client, SessionEvent, Session
from dotenv import load_dotenv, set_key
import time
from lib import cleaing_txt
import pathlib

load_dotenv()

ENV_PATH = pathlib.Path('.env')
BLUESKY_SESSION = os.getenv('BLUESKY_SESSION')
BLUESKY_HANDLE = os.getenv('BLUESKY_HANDLE')
BLUESKY_APP_PASS = os.getenv('BLUESKY_APP_PASS')

def save_bluesky_session(session: str) -> None:
    # .envのBLUESKY_SESSIONの更新
    set_key(str(ENV_PATH), "BLUESKY_SESSION", session)
    os.environ["BLUESKY_SESSION"] = session

def init_bluesky_clinet() -> Client:
    client = Client()

    @client.on_session_change
    def on_session_changee(event: SessionEvent, session: Session):
        if event in (SessionEvent.CREATE,SessionEvent.REFRESH):
            save_bluesky_session(session.export())

    if BLUESKY_SESSION:
        try:
            print('既存のsessionを利用しログインします')
            client.login(session_string = BLUESKY_SESSION)

            # 確認
            _ = client.me

            return client
        except Exception as e:
            print("既存セッションが使えなかったためapp passwordでログインします")

    if not BLUESKY_HANDLE or not BLUESKY_APP_PASS:
        raise RuntimeError(
            "BLUESKY_SESSION が無効、かつ BLUESKY_HANDLE / BLUESKY_APP_PASS が設定されていません。"
        )
    
    print("Bluesky に app password でログインします")
    client.login(BLUESKY_HANDLE, BLUESKY_APP_PASS)

    # 確認
    _ = client.me
    save_bluesky_session(client.export_session_string())

    return client


bluesky_client = init_bluesky_clinet()

def get_all_posts():
    me = bluesky_client.me
    cursor = None
    posts = []

    while True:
        res = bluesky_client.get_author_feed(me.did, cursor = cursor, limit = 100)
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

if __name__ == "__main__":
    get_all_posts()
