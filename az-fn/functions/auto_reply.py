import os
import boto3
from atproto import Client, models
import markovify

import azure.functions as func


S3_BUCKET = os.getenv('S3_BUCKET')
CHAIN_FILE_KEY = os.getenv('CHAIN_FILE_KEY')

BLUESKY_HANDLE = os.getenv('BLUESKY_HANDLE')
BLUESKY_APP_PASS = os.getenv('BLUESKY_APP_PASS')

def load_model_data(s3, bucket: str, key: str) -> str:
    data = s3.get_object(Bucket = bucket, Key = key)['Body'].read().decode('utf-8')
    return data

bp = func.Blueprint()

@bp.schedule(schedule="0 * * * * *", arg_name = "autoReplyFunc", run_on_startup = True, use_monitor = False)
def auto_reply(autoReplyFunc: func.TimerRequest):
    print("auto_reply start")
    bsky_client = Client()
    bsky_client.login(BLUESKY_HANDLE, BLUESKY_APP_PASS)

    res = bsky_client.app.bsky.notification.list_notifications()
    need_to_reply = []
    for notification in res.notifications:
        if notification.is_read:
            continue
        if notification.reason != 'mention' and notification.reason != 'reply':
            continue

        parent = models.create_strong_ref(notification)
        root = models.create_strong_ref(notification)
        if notification.record.reply is not None:
            root = models.create_strong_ref(notification.record.reply.root)

        #bsky_client.app.bsky.notification.update_seen({'seen_at': bsky_client.get_current_time_iso()})
        need_to_reply.append((parent, root))

    s3 = boto3.client(service_name ="s3")
    bsky_client = Client()
    bsky_client.login(BLUESKY_HANDLE, BLUESKY_APP_PASS)

    model_json = load_model_data(s3, S3_BUCKET, CHAIN_FILE_KEY)

    model = markovify.Text.from_json(model_json)
    for parent, root in need_to_reply:
        random_post = model.make_short_sentence(60).replace(' ', '')
        reply_to = models.AppBskyFeedPost.ReplyRef(parent = parent, root = root)
        bsky_client.send_post(text = random_post, reply_to = reply_to)

    print("auto_reply end")