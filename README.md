# Scrappy, the RSS Scraper

Author: Chris Davis

Private GitHub: https://github.com/defbyte/rssScraper

## Setup

### Installation

Please note the following prerequisites:
* Python 3
* Docker
* Docker Compose

In the project root, create your virtualenv, activate it, and install requirements.txt
```
# project root is rssScraper
python venv -m .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Before proceeding, it is wise to go ahead and create a user for the application. You will need one for using the API. Use the `createsuperuser` management command and follow the prompts. Later you will use these credentials to obtain an API key.

```
# from project root and activated virtualenv
cd src/
python manage.py createsuperuser
```

### Run via Docker
To run the app and all services via `docker-compose`

```
# From project root:
docker-compose up
```

This will start up the services required:
* Postgres database
* Application server (Django app, Celery & Celery Beat)
* Redis
* Ngninx

Celery & Celery Beat are used to handle the schduled task of updating RSS feeds in the background. Redis plays the role of message broker.

If changes are made to the application code you'll need to flag to rebuild containers:

```
docker-compose up --build
```

Now visit 127.0.0.1/api/ in browser for a quick verification.

See usage section below for API

### Running in Development Mode

Note: the instruciton below assume you are running the dockerized database!

Using multiple tabs / terminal sessions:

#### Tab 1: Database
Start the database. Feel free to run it detached and save a tab!
```
From project root:
docker-compose up db
```

#### Tab 2: Celery and Celery Beat

```
# From project root
source .venv/bin/activate
cd src/
# Before you first try to start celery or runserver in development mode:
python manage.py migrate
# I keep it running to watch
celery -A scrappy worker --beat -l info
```


#### Tab 3: Django Runserver

```
From project root
source .venv/bin/activate
cd src/
# Before you first try to start celery or runserver in development mode:
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### Running Tests

This project uses `pytest`. Switch to the `src/` directory in an activate virtualenv and simply execute `pytest`:

```
From project root
source .venv/bin/activate
cd src/
pytest
```


## API Usage

This API requires user authentication as feeds are managed per user.

✨ **Swagger docs are available** for this project at `/swagger/` in your browser ✨

### 🗝 Authentication

#### POST /api/token-auth/

Expects `username` and `password`, returns a token.

You can setup a user account using the createsuperuser management command.

All requests require the authorization header to be sent:
```
Authorization: Token {YOUR_TOKEN}
```

### Feeds

#### GET /api/feeds/
Get paginated list of this user's feeds.

#### POST /api/feeds/
Create a new feed to follow.

#### DELETE /api/feeds/{feed_id}
Unfollow a feed .. by deleting it.

#### GET /api/feeds/{feed_id}/
Get feed detail.

#### GET /api/feeds/{feed_id}/refresh/
Attempts to refresh the feed and resets any auto update error statuses, regardless of response. The feed will be elligible for auto updates again and will be taken out of rotation on next failure cycle(s).

#### GET /api/feeds/{feed_id}/items/
Get paginated list of this feed's items via a convenience path that includes the feed id in parent path.

Supports filtering:
* `is_read = true|false`

Supports ordering (asc/desc):
* published: `ordering=-published | ordering=published`
* updated: `ordering=-updated | ordering=updated`

### Feed Items
#### GET /api/feed-items/
Get paginated list of all this user's feed items, across all their feeds.

Supports filtering:
* `is_read = true|false`
* `feed_id = {feed_id}`

Supports ordering (asc/desc):
* published: `ordering=-published | ordering=published`
* updated: `ordering=-updated | ordering=updated`

#### GET /api/feed-items/{item_id}/
Get detail view of a feed item.

Also available via: `GET /api/feeds/{feed_id}/items/{item_id}/`

#### GET /api/feed-items/{item_id}/read/
Marks this feed item as read and returns item.

Also available via: `GET /api/feeds/{feed_id}/items/{item_id}/read`

#### GET /api/feed-items/{item_id}/unread/
Marks this feed item as unread and returns item.

Also available via: `GET /api/feeds/{feed_id}/items/{item_id}/unread`

## Assignment Notes

Things I could do better?

* Better separation of development settings from production settings
* Cleanup tests.py
* Split up tests.py in to two files
* Optimize the mocks for the task tests to use a factory
* Remove unused API methods such as updates for feed items
