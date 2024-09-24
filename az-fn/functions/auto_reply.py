import os
import boto3
from atproto import Client, models
import markovify
import logging

import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

S3_BUCKET = os.getenv('S3_BUCKET')
CHAIN_FILE_KEY = os.getenv('CHAIN_FILE_KEY')
KEY_VAULT_URL = os.getenv('KEY_VAULT_URL')
BLUESKY_SESSION_KEYVAULT_NAME = os.getenv('BLUESKY_SESSION_KEYVAULT_NAME')

def load_model_data(s3, bucket: str, key: str) -> str:
    data = s3.get_object(Bucket = bucket, Key = key)['Body'].read().decode('utf-8')
    return data

bp = func.Blueprint()

@bp.schedule(schedule='0 * * * * *', arg_name = 'autoReplyFunc', run_on_startup = False, use_monitor = False)
def auto_reply(autoReplyFunc: func.TimerRequest):
    logging.info('auto_reply start')

    logging.info('getting bluesky session from keyvalut')
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url = KEY_VAULT_URL, credential = credential)
    bluesky_session = client.get_secret(BLUESKY_SESSION_KEYVAULT_NAME).value

    logging.info('login to bluesky')
    bsky_client = Client()
    bsky_client.login(session_string = bluesky_session)

    logging.info('getting notifications')
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

        need_to_reply.append((parent, root))

    if len(need_to_reply) == 0:
        logging.info('no need to reply')
        logging.info('check session is updated')
        new_session = bsky_client.export_session_string()
        if new_session != bluesky_session:
            logging.info('session is updated')
            logging.info('update bluesky session of keyvault')
            client.set_secret(BLUESKY_SESSION_KEYVAULT_NAME, bsky_client.export_session_string())
        else:
            logging.info('session is not updated')
        return

    logging.info(f'need to reply len: {len(need_to_reply)}')
    logging.info('update seen')
    bsky_client.app.bsky.notification.update_seen({'seen_at': bsky_client.get_current_time_iso()})

    logging.info('loading model data')
    s3 = boto3.client(service_name ='s3')
    model_json = load_model_data(s3, S3_BUCKET, CHAIN_FILE_KEY)
    model = markovify.Text.from_json(model_json)

    logging.info('sending posts')
    for parent, root in need_to_reply:
        random_post = model.make_short_sentence(60).replace(' ', '')
        reply_to = models.AppBskyFeedPost.ReplyRef(parent = parent, root = root)
        logging.info(f'replying to {reply_to}')
        bsky_client.send_post(text = random_post, reply_to = reply_to, langs = ['ja'])

    logging.info('check session is updated')
    new_session = bsky_client.export_session_string()
    if new_session != bluesky_session:
        logging.info('session is updated')
        logging.info('update bluesky session of keyvault')
        client.set_secret(BLUESKY_SESSION_KEYVAULT_NAME, bsky_client.export_session_string())
    else:
        logging.info('session is not updated')
    logging.info('auto_reply end')
