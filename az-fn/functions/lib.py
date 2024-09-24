import logging
import os
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from atproto import Client
import boto3
import markovify

S3_BUCKET = os.getenv('S3_BUCKET')
CHAIN_FILE_KEY = os.getenv('CHAIN_FILE_KEY')
KEY_VAULT_URL = os.getenv('KEY_VAULT_URL')
BLUESKY_SESSION_KEYVAULT_NAME = os.getenv('BLUESKY_SESSION_KEYVAULT_NAME')

class BlueSkySession:
    def __init__(self) -> None:
        credential = DefaultAzureCredential()
        self.secret_client = SecretClient(vault_url = KEY_VAULT_URL, credential = credential)

    def __enter__(self):
        logging.info('getting bluesky session from keyvalut...')
        self._bluesky_session = self.secret_client.get_secret(BLUESKY_SESSION_KEYVAULT_NAME).value

        logging.info('login to bluesky...')
        self.bluesky_client = Client()
        self.bluesky_client.login(session_string = self._bluesky_session)
        return self.bluesky_client

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.info('checking bluesky session is updated...')
        new_session = self.bluesky_client.export_session_string()

        if new_session != self._bluesky_session:
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
