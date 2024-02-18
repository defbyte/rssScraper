from datetime import datetime
import logging

from celery import shared_task
from scrappy.feeds.models import Feed
from scrappy.feeds.fetcher import fetch_feed, FeedError

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


@shared_task(bind=True)
def update_feeds(self):
    # Get all feeds eligible for auto updates
    feeds = Feed.objects.filter(auto_update=True)
    logger.info(f'Updating {feeds.count()} feeds...')
    for feed in feeds:
        logger.info(f'  Updating {feeds.url}')
        update_feed(feed)


def update_feed(feed):
    try:
        # mark time we are attempting fetch
        feed.last_fetched = datetime.now()
        fetch_feed(feed.url, feed.id)
        # the following will only execute if there were no errors
        feed.auto_update = True
        feed.is_failed = False
        feed.retries = 0
        feed.status = 'ok'
        feed.save()
    except FeedError as e:
        logger.warning(f'FeedError {feed.url}, {e.message}')
        # capture the error, set in failed state
        feed.status = e.message
        feed.is_failed = True
        # If we have 404 or 401, stop trying
        if e.status == 404 or e.status == 401:
            feed.auto_update = False
        # Errors happened but we are elligible to retry later
        elif feed.retries < MAX_RETRIES:
            feed.retries += 1
        # No more retries left, stop auto updates
        else:
            feed.auto_update = False
        feed.save()
    return feed
