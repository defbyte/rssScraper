from datetime import datetime
import pytest
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from scrappy.feeds.models import Feed, FeedItem
from scrappy.feeds.tasks import update_feed


@pytest.fixture
def api_client():
    """
    Fixture to provide an API client
    :return: APIClient
    """
    yield APIClient()


@pytest.fixture
def api_user(django_user_model):
    user = django_user_model.objects.create_user(username='apiuser', password='bluerose')
    Token.objects.create(user=user)
    return user


@pytest.fixture
def api_user_feed(api_user):
    feed = Feed.objects.create(
        url='https://scryfall.com/blog/feed',
        title='Scryfall Blog',
        owner=api_user)
    # create some feed items
    count = 0
    while count < 3:
        count += 1
        FeedItem.objects.create(
            url=f'https://scryfall.com/blog/item-{count}',
            title=f'Feed Item {count}',
            description=f'Feed desc {count}',
            published=datetime.now(),
            updated=datetime.now(),
            feed_id=feed.id
        )
    return feed


@pytest.fixture
def other_user_feeds(django_user_model):
    john = django_user_model.objects.create_user(username='john', password='foobar')
    Token.objects.create(user=john)
    jane = django_user_model.objects.create_user(username='jane', password='foobar')
    Token.objects.create(user=jane)

    Feed.objects.create(
        url='https://foobar.com/rss',
        title='Foo Blog',
        owner=john)

    Feed.objects.create(
        url='https://barfoo.com/rss',
        title='Bar Blog',
        owner=jane)


@pytest.mark.django_db
def test_create_feed(api_client, api_user, other_user_feeds):
    """
    Creates one feed for api_user and tests that only that one is accessible
    """
    payload = {
        'url': 'https://scryfall.com/blog/feed',
        'title': 'Scryfall Blog',
    }
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {api_user.auth_token.key}')
    response = api_client.post('/api/feeds/', data=payload, format='json')
    assert response.status_code == 201
    assert response.data['url'] == payload['url']
    # assert user only has one feed
    response = api_client.get('/api/feeds/', format='json')
    assert response.status_code == 200
    assert response.data['count'] == 1


@pytest.mark.django_db
def test_delete_feed(api_client, api_user, api_user_feed, other_user_feeds):
    """
    Delete api_user's feed, tests user has zero, but other users have feeds
    """
    api_client.credentials(HTTP_AUTHORIZATION='Token ' + api_user.auth_token.key)

    response = api_client.delete(f'/api/feeds/{api_user_feed.id}/', format='json')
    assert response.status_code == 204
    # assert user now has zero feeds
    response = api_client.get('/api/feeds/', format='json')
    assert response.status_code == 200
    assert response.data['count'] == 0
    # assert other users still have their feeds
    assert Feed.objects.count() == 2


@pytest.mark.django_db
def test_mark_read_and_unread(api_client, api_user, api_user_feed, other_user_feeds):
    api_client.credentials(HTTP_AUTHORIZATION='Token ' + api_user.auth_token.key)

    response = api_client.get(f'/api/feeds/{api_user_feed.id}/items/', format='json')
    feed_item = response.data['results'][0]
    assert feed_item['is_read'] is False

    response = api_client.get(
        f'/api/feeds/{api_user_feed.id}/items/{feed_item["id"]}/read/', format='json')
    assert response.data['is_read'] is True

    response = api_client.get(
        f'/api/feeds/{api_user_feed.id}/items/{feed_item["id"]}/unread/', format='json')
    assert response.data['is_read'] is False


@pytest.mark.django_db
def test_update_feed_success(mocker, api_user_feed):
    """
    A 200 ok hooray, business as usual, no retries
    """
    from feedparser.util import FeedParserDict
    # bozo is an error state bit the feedparser package sets
    mocker.patch('scrappy.feeds.fetcher.feedparser.parse', return_value=FeedParserDict(
        bozo=0,
        status=200,
        feed=FeedParserDict(
            title='mock title',
            description='mock description',
        ),
        entries=[],
    ))
    feed = update_feed(api_user_feed)
    assert feed.auto_update is True
    assert feed.is_failed is False
    assert feed.retries == 0
    assert feed.status == 'ok'


@pytest.mark.django_db
def test_update_feed_unparseable(mocker, api_user_feed):
    """
    A 200 ok but .. unparseable . eligible for retries
    """
    from feedparser.util import FeedParserDict
    # bozo is an error state bit the feedparser package sets
    mocker.patch('scrappy.feeds.fetcher.feedparser.parse', return_value=FeedParserDict(
        bozo=1,
        status=200,
        feed=FeedParserDict(
            title='unparseable',
            description='mock description',
        ),
        entries=[],
    ))
    feed = update_feed(api_user_feed)
    assert feed.auto_update is True
    assert feed.is_failed is True
    assert feed.retries == 1
    assert feed.status == 'Feed unparsable'


@pytest.mark.django_db
def test_update_feed_404(mocker, api_user_feed):
    """
    A 404 error should take the feed out of auto updates
    """
    from feedparser.util import FeedParserDict
    # bozo is an error state bit the feedparser package sets
    mocker.patch('scrappy.feeds.fetcher.feedparser.parse', return_value=FeedParserDict(
        bozo=1,
        status=404,
        feed=FeedParserDict(
            title='404',
            description='mock description',
        ),
        entries=[],
    ))
    feed = update_feed(api_user_feed)
    assert feed.auto_update is False
    assert feed.is_failed is True
    assert feed.retries == 0
    assert feed.status == 'Feed not found'


@pytest.mark.django_db
def test_update_feed_403(mocker, api_user_feed):
    """
    A 403 forbidden will allow for retries, check for at least 1
    """
    from feedparser.util import FeedParserDict
    # bozo is an error state bit the feedparser package sets
    mocker.patch('scrappy.feeds.fetcher.feedparser.parse', return_value=FeedParserDict(
        bozo=1,
        status=403,
        feed=FeedParserDict(
            title='403',
            description='mock description',
        ),
        entries=[],
    ))
    feed = update_feed(api_user_feed)
    assert feed.auto_update is True
    assert feed.is_failed is True
    assert feed.retries == 1
    assert feed.status == 'Feed forbidden'


@pytest.mark.django_db
def test_update_feed_500(mocker, api_user_feed):
    """
    We will retry 3 times if there is a server error.
    After 3 attempts, the feed is set to not auto update
    """
    from feedparser.util import FeedParserDict
    # bozo is an error state bit the feedparser package sets
    mocker.patch('scrappy.feeds.fetcher.feedparser.parse', return_value=FeedParserDict(
        bozo=1,
        status=500,
        feed=FeedParserDict(
            title='500',
            description='mock description',
        ),
        entries=[],
    ))
    feed = update_feed(api_user_feed)
    assert feed.auto_update is True
    assert feed.is_failed is True
    assert feed.retries == 1

    feed = update_feed(api_user_feed)
    assert feed.auto_update is True
    assert feed.is_failed is True
    assert feed.retries == 2

    feed = update_feed(api_user_feed)
    assert feed.auto_update is True
    assert feed.is_failed is True
    assert feed.retries == 3

    # No more auto udpates (update_feeds task will exclude it)
    feed = update_feed(api_user_feed)
    assert feed.auto_update is False
    assert feed.is_failed is True
    assert feed.retries == 3
