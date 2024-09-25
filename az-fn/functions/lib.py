import logging
import os
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from atproto import Client
from atproto.exceptions import BadRequestError
import boto3
import markovify

S3_BUCKET = os.getenv('S3_BUCKET')
CHAIN_FILE_KEY = os.getenv('CHAIN_FILE_KEY')
KEY_VAULT_URL = os.getenv('KEY_VAULT_URL')
BLUESKY_SESSION_KEYVAULT_NAME = os.getenv('BLUESKY_SESSION_KEYVAULT_NAME')

class BlueSkySession:
    _bluesky_session: str = None

    def __init__(self) -> None:
        credential = DefaultAzureCredential()
        self.secret_client = SecretClient(vault_url = KEY_VAULT_URL, credential = credential)

    def __enter__(self):
        if BlueSkySession._bluesky_session is None:
            logging.info('getting bluesky session from keyvalut...')
            BlueSkySession._bluesky_session = self.secret_client.get_secret(BLUESKY_SESSION_KEYVAULT_NAME).value
        else:
            logging.info('using cached bluesky session')

        logging.info('login to bluesky...')
        self.bluesky_client = Client()

        try:
            self.bluesky_client.login(session_string = BlueSkySession._bluesky_session)
        except BadRequestError as e:
            if e.response.status_code == 400 and e.response.content.error == 'ExpiredToken':
                logging.info('session is expired')
                logging.info('taking new session from keyvault...')
                BlueSkySession._bluesky_session = self.secret_client.get_secret(BLUESKY_SESSION_KEYVAULT_NAME).value

                logging.info('retry login to bluesky...')
                self.bluesky_client.login(session_string = BlueSkySession._bluesky_session)
            else:
                raise e

        return self.bluesky_client

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.info('checking bluesky session is updated...')
        new_session = self.bluesky_client.export_session_string()

        if new_session != BlueSkySession._bluesky_session:
            BlueSkySession._bluesky_session = new_session
            logging.info('session is updated !')
            logging.info('updating bluesky session of keyvault...')
            self.secret_client.set_secret(BLUESKY_SESSION_KEYVAULT_NAME, new_session)
        else:
            logging.info('session is not updated')

        return False

def load_markovify_model() -> markovify.Text:
    s3 = boto3.client(service_name = 's3')
    logging.info('fetching chain file...')
    model_json = s3.get_object(Bucket = S3_BUCKET, Key = CHAIN_FILE_KEY)['Body'].read().decode('utf-8')

    logging.info('loading model...')
    model = markovify.Text.from_json(model_json)

    return model
