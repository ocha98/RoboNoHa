import os
import boto3
import markovify
from atproto import Client
import logging
import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

S3_BUCKET = os.getenv('S3_BUCKET')
CHAIN_FILE_KEY = os.getenv('CHAIN_FILE_KEY')
KEY_VAULT_URL = os.getenv('KEY_VAULT_URL')
SESSION_KEYVAULT_NAME = os.getenv('SESSION_KEYVAULT_NAME')

def load_model_data(s3, bucket: str, key: str) -> str:
    data = s3.get_object(Bucket = bucket, Key = key)['Body'].read().decode('utf-8')
    return data

bp = func.Blueprint()

@bp.schedule(schedule='0 0 */4 * * *', arg_name = 'randomPostFunc', run_on_startup = False, use_monitor = False)
def random_post(randomPostFunc: func.TimerRequest):
    logging.info('random_post start')

    logging.info('getting bluesky session from keyvalut')
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url = KEY_VAULT_URL, credential = credential)
    bluesky_session = client.get_secret(SESSION_KEYVAULT_NAME).value

    logging.info('login to bluesky')
    bsky_client = Client()
    bsky_client.login(session_string = bluesky_session)

    logging.info('loading model data')
    s3 = boto3.client(service_name ='s3')
    model_json = load_model_data(s3, S3_BUCKET, CHAIN_FILE_KEY)
    model = markovify.Text.from_json(model_json)

    random_post = model.make_short_sentence(60).replace(' ', '')

    logging.info('sending post')
    bsky_client.send_post(text = random_post, langs = ['ja'])

    logging.info('check session is updated')
    new_session = bsky_client.export_session_string()
    if new_session != bluesky_session:
        logging.info('session is updated')
        logging.info('update bluesky session of keyvault')
        client.set_secret(SESSION_KEYVAULT_NAME, new_session)
    else:
        logging.info('session is not updated')

    logging.info('random_post end')
