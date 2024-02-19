from datetime import datetime
from time import mktime
import feedparser

from scrappy.feeds.models import Feed, FeedItem


class FeedError(Exception):
    def __init__(self, message, status, url):
        self.message = message
        self.status = status
        self.url = url


# A set of functions to fetch feed URLs
def fetch_feed(url, feed_id):
    """
    Make the network request to fetch a feed's data and parse it using feedparser.
    We check basic error states here that feedparser resolves, raising any errors
    """
    feed_data = feedparser.parse(url)

    # "bozo" flags errors encountered
    # What was the error? If not 100% fatal, try again later
    if feed_data.bozo:

        # Feed errors, trying again later
        if feed_data.status >= 500 and feed_data.status < 600:
            raise FeedError('Server error: %s' % feed_data.status, 500, url)
        # Feed not found, no need to keep trying
        elif feed_data.status == 404:
            raise FeedError('Feed not found', 404, url)
        # Feed forbidden
        elif feed_data.status == 403:
            raise FeedError('Feed forbidden', 403, url)
        # Feed unauthorixed
        elif feed_data.status == 401:
            raise FeedError('Feed unauthorized', 401, url)
        # URL resolved but we cannot parse it
        elif feed_data.status == 200:
            raise FeedError('Feed unparsable', 200, url)
        else:
            raise FeedError('Feed error: %s' % feed_data.bozo_exception,
                            feed_data.status, url)

    # Valid feed data to process
    if not feed_data.bozo and feed_data.status == 200:
        feed = Feed.objects.get(id=feed_id)
        feed.title = feed_data.feed.title
        # Feeds, got to love'm, sometimes they have a field sometimes they don't
        feed.description = getattr(feed_data.feed, 'description', '')
        feed.last_fetched = datetime.now()
        feed.save()

        for item in feed_data.entries:
            FeedItem.objects.update_or_create(
                url=item.link, feed_id=feed.id, defaults={
                    'title': item.title,
                    'description': getattr(item, 'description', ''),
                    # TODO: can we preserve timezones? I don't like this..
                    'published': datetime.fromtimestamp(mktime(item.published_parsed)),
                    'updated': datetime.fromtimestamp(mktime(item.updated_parsed)),
                }
            )
    return feed_data
