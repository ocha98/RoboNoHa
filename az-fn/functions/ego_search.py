import logging
import atproto
from atproto import models
import azure.functions as func
import datetime
from .lib import BlueSkySession, load_markovify_model

bp = func.Blueprint()

def ego_search_impl(bsky_client: atproto.Client) -> None:
    logging.info('searching post...')
    now = bsky_client.get_current_time()
    since = now - datetime.timedelta(minutes = 5)
    since_iso = since.isoformat()

    query = f'"ロボの葉" since:{since_iso}'
    res = bsky_client.app.bsky.feed.search_posts(models.AppBskyFeedSearchPosts.Params(q = query))

    posts = res.posts

    need_to_reply_refs = []
    for post in posts:
        if 'ロボの葉' not in post.record.text:
            continue
        if post.record.reply is not None: # replyには返信しない
            continue
        if post.viewer.like is not None: # 既にいいねで返信済み
            continue
        if post.author.handle == 'robo.ochappa.net': # 自分の投稿には返信しない
            continue
        ref = models.create_strong_ref(post)
        need_to_reply_refs.append(ref)

    if len(need_to_reply_refs) == 0:
        logging.info('no need to reply')
        return

    logging.info('loading model data....')
    model = load_markovify_model()

    n = len(need_to_reply_refs)
    logging.info(f'need to reply len: {n}')
    for i in range(n):
        parent_ref = need_to_reply_refs[i]
        logging.info(f'{i+1}/{n}: liking {parent_ref}')
        bsky_client.like(uri = parent_ref.uri, cid = parent_ref.cid)

        reply_ref = models.AppBskyFeedPost.ReplyRef(parent = parent_ref, root = parent_ref)
        logging.info(f'{i+1}/{n}: replying to {parent_ref}')
        random_post = model.make_short_sentence(60).replace(' ', '')
        bsky_client.send_post(text = random_post, reply_to = reply_ref, langs = ['ja'])

@bp.schedule(schedule='0 * * * * *', arg_name = 'egoSearchFunc', run_on_startup = False, use_monitor = False)
def ego_search(egoSearchFunc: func.TimerRequest):
    logging.info('ego_search start')

    with BlueSkySession() as bsky_client:
        ego_search_impl(bsky_client)

    logging.info('ego_search end')
