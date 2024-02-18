from django.contrib.auth.models import User
from rest_framework import serializers

from scrappy.feeds.models import Feed, FeedItem


class UserSerializer(serializers.ModelSerializer):
    feeds = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Feed.objects.all())

    class Meta:
        model = User
        fields = ['id', 'username', 'feeds']


class FeedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feed
        fields = ['id', 'url', 'title', 'description',
                  'updated', 'created', 'last_fetched',
                  'auto_update', 'is_failed', 'status', 'retries']


class FeedItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedItem
        fields = ['id', 'feed_id', 'url', 'title', 'description',
                  'published', 'updated', 'is_read']
