import os
import boto3
import markovify
from atproto import Client
import logging
import azure.functions as func

S3_BUCKET = os.getenv('S3_BUCKET')
CHAIN_FILE_KEY = os.getenv('CHAIN_FILE_KEY')
BLUESKY_SESSION = os.getenv('BLUESKY_SESSION')

def load_model_data(s3, bucket: str, key: str) -> str:
    data = s3.get_object(Bucket = bucket, Key = key)['Body'].read().decode('utf-8')
    return data

bp = func.Blueprint()

@bp.schedule(schedule='0 0 */4 * * *', arg_name = 'randomPostFunc', run_on_startup = False, use_monitor = False)
def random_post(randomPostFunc: func.TimerRequest):
    logging.info('random_post start')
    s3 = boto3.client(service_name ='s3')
    bsky_client = Client()

    logging.info('login to bluesky')
    bsky_client.login(session_string = BLUESKY_SESSION)

    logging.info('loading model data')
    model_json = load_model_data(s3, S3_BUCKET, CHAIN_FILE_KEY)
    model = markovify.Text.from_json(model_json)

    random_post = model.make_short_sentence(60).replace(' ', '')

    logging.info('sending post')
    bsky_client.send_post(text = random_post, langs = ['ja'])

    logging.info('random_post end')
