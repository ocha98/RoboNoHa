import logging
import atproto
from atproto import models
import azure.functions as func
from .lib import BlueSkySession, load_markovify_model

bp = func.Blueprint()

def auto_reply_impl(bsky_client: atproto.Client) -> None:
    logging.info('getting notifications...')
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
        return

    logging.info(f'need to reply len: {len(need_to_reply)}')
    logging.info('update seen....')
    bsky_client.app.bsky.notification.update_seen({'seen_at': bsky_client.get_current_time_iso()})

    logging.info('loading model data....')
    model = load_markovify_model()

    logging.info('sending posts....')
    num_need_to_reply = len(need_to_reply)
    for i in range(num_need_to_reply):
        parent, root = need_to_reply[i]

        random_post = model.make_short_sentence(60).replace(' ', '')

        logging.info(f'{i+1}/{num_need_to_reply}: liking {parent}')
        bsky_client.like(uri = parent.uri, cid = parent.cid)

        reply_to = models.AppBskyFeedPost.ReplyRef(parent = parent, root = root)
        logging.info(f'{i+1}/{num_need_to_reply}: replying to {reply_to}')
        bsky_client.send_post(text = random_post, reply_to = reply_to, langs = ['ja'])

@bp.schedule(schedule='0 * * * * *', arg_name = 'autoReplyFunc', run_on_startup = False, use_monitor = False)
def auto_reply(autoReplyFunc: func.TimerRequest):
    logging.info('auto_reply start')

    with BlueSkySession() as bsky_client:
        auto_reply_impl(bsky_client)

    logging.info('auto_reply end')
