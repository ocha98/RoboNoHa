import logging
import azure.functions as func
from .lib import BlueSkySession, load_markovify_model

bp = func.Blueprint()

@bp.schedule(schedule = '0 0 */5 * * *', arg_name = 'randomPostFunc', run_on_startup = False, use_monitor = False)
def random_post(randomPostFunc: func.TimerRequest):
    logging.info('random_post start')

    with BlueSkySession() as bsky_client:
        model = load_markovify_model()
        random_post = model.make_short_sentence(60).replace(' ', '')

        logging.info('sending post...')
        bsky_client.send_post(text = random_post, langs = ['ja'])

    logging.info('random_post end')
