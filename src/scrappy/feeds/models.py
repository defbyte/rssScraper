from django.db import models


class Feed(models.Model):
    url = models.URLField()
    title = models.CharField()
    description = models.CharField(blank=True)
    updated = models.DateTimeField(blank=True, null=True)
    # When this feed was added
    created = models.DateTimeField(auto_now_add=True)
    # When this feed was last fetched
    last_fetched = models.DateTimeField(blank=True, null=True)
    status = models.CharField(blank=True)
    retries = models.IntegerField(default=0)
    auto_update = models.BooleanField(default=True)
    is_failed = models.BooleanField(default=False)
    # TODO: do we make this non-nullable?
    owner = models.ForeignKey('auth.User', related_name='feeds',
                              on_delete=models.CASCADE, null=True)


class FeedItem(models.Model):
    url = models.URLField()
    title = models.CharField()
    description = models.CharField(blank=True)
    published = models.DateTimeField(blank=True, null=True)
    updated = models.DateTimeField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE)
