import os
import boto3
from dotenv import load_dotenv
import markovify
from atproto import Client

import azure.functions as func

load_dotenv()

S3_BUCKET = os.getenv('S3_BUCKET')
CHAIN_FILE_KEY = os.getenv('CHAIN_FILE_KEY')

BLUESKY_HANDLE = os.getenv('BLUESKY_HANDLE')
BLUESKY_APP_PASS = os.getenv('BLUESKY_APP_PASS')

def load_model_data(s3, bucket: str, key: str) -> str:
    data = s3.get_object(Bucket = bucket, Key = key)['Body'].read().decode('utf-8')
    return data

def upload_model_data(s3, bucket: str, key: str, data: str) -> None:
    s3.put_object(Bucket = bucket, Key = key, Body = data)


bp = func.Blueprint()

@bp.schedule(schedule="0 0 */4 * * *", arg_name = "randomPostFunc", run_on_startup = True, use_monitor = False)
def random_post(randomPostFunc: func.TimerRequest):
    print("random_post start")
    s3 = boto3.client(service_name ="s3")
    bsky_client = Client()
    bsky_client.login(BLUESKY_HANDLE, BLUESKY_APP_PASS)

    model_json = load_model_data(s3, S3_BUCKET, CHAIN_FILE_KEY)

    model = markovify.Text.from_json(model_json)
    random_post = model.make_short_sentence(60).replace(' ', '')
    print("random_post send")
    bsky_client.send_post(text = random_post)
    print("random_post end")
