import logging
import os
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from atproto import Client, SessionEvent
from atproto.exceptions import BadRequestError
import boto3
import markovify

S3_BUCKET = os.getenv('S3_BUCKET')
CHAIN_FILE_KEY = os.getenv('CHAIN_FILE_KEY')
BLUESKY_SESSION_KEYVAULT_NAME = os.getenv('BLUESKY_SESSION_KEYVAULT_NAME')

BLUESKY_HANDLE = os.getenv('BLUEKSY_HANDLE')
BLUESKY_APP_PASS = os.getenv('BLUEKSY_APP_PASS')
KEY_VAULT_URL = os.getenv('KEY_VAULT_URL')

def get_secret_client() -> SecretClient:
    credential = DefaultAzureCredential()
    return SecretClient(vault_url = KEY_VAULT_URL, credential = credential)

def load_bluesky_session() -> str | None:
    try:
        secret_client = get_secret_client()
        return secret_client.get_secret(BLUESKY_SESSION_KEYVAULT_NAME).value
    except Exception as e:
        logging.error('Key vaultからBLUESKY_SESSIONを取得できませんでした。')
        return None
    

def save_bluesky_session(session: str):
    secret_client = get_secret_client()
    secret_client.set_secret(BLUESKY_SESSION_KEYVAULT_NAME, session)


def verify_bluesky_login(client: Client, login_method: str) -> None:
    logging.info("Bluesky ログイン確認を開始します: method=%s", login_method)

    try:
        me = client.me

        logging.info(
            "Bluesky ログイン確認に成功しました: method=%s handle=%s did=%s",
            login_method,
            getattr(me, "handle", None),
            getattr(me, "did", None),
        )

    except Exception:
        logging.exception(
            "Bluesky ログイン確認に失敗しました: method=%s",
            login_method,
        )
        raise

def init_bluesky_client() -> Client:
    logging.info('bluesky clientの初期化を開始します')
    client = Client()

    @client.on_session_change
    def on_session_change(event: SessionEvent, session) -> None:
        logging.info('bluesky session change eventを受信')
        if event in (SessionEvent.CREATE, SessionEvent.REFRESH):
            try:
                logging.info('Bluesky sessionを保存します。 event=%s', event)
                save_bluesky_session(session.export())
                logging.info('Bluesky sessionの保存に成功しました: event=%s', event)
            except Exception as e:
                logging.exception("Bluesky sessionの保存に失敗しました event = %s", event)
                raise

    bluesky_session = load_bluesky_session()

    if bluesky_session:
        try:
            logging.info("既存の session を利用してログインします")
            client.login(session_string=bluesky_session)

            # セッション確認
            verify_bluesky_login(client, login_method="session")

            return client

        except Exception as e:
            logging.warning(f"既存セッションが使えなかったため app password でログインします: {e}")

    if not BLUESKY_HANDLE or not BLUESKY_APP_PASS:
        raise RuntimeError(
            "BLUESKY_SESSION が無効、かつ BLUESKY_HANDLE / BLUESKY_APP_PASS が設定されていません。"
        )

    logging.info("Bluesky に app password でログインします")
    client.login(BLUESKY_HANDLE, BLUESKY_APP_PASS)

    # ログイン確認
    verify_bluesky_login(client, login_method="app pass")

    save_bluesky_session(client.export_session_string())

    return client

def load_markovify_model() -> markovify.Text:
    s3 = boto3.client(service_name = 's3')
    logging.info('fetching chain file...')
    model_json = s3.get_object(Bucket = S3_BUCKET, Key = CHAIN_FILE_KEY)['Body'].read().decode('utf-8')

    logging.info('loading model...')
    model = markovify.Text.from_json(model_json)

    return model
