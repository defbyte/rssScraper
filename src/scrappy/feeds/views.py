from rest_framework.decorators import action
from rest_framework import filters, permissions, viewsets
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend

from scrappy.feeds.fetcher import fetch_feed
from scrappy.feeds.models import Feed, FeedItem
from scrappy.feeds.serializers import FeedSerializer, FeedItemSerializer


class FeedViewSet(viewsets.ModelViewSet):
    queryset = Feed.objects.all()
    lookup_url_kwarg = 'feed_id'
    serializer_class = FeedSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['updated', 'last_fetched']
    ordering = '-updated'

    def get_queryset(self):
        # Return only feeds for the authenticated user
        return self.queryset.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True)
    def refresh(self, request, *args, **kwargs):
        feed = self.get_object()
        # Reset any feed failure states for this refresh
        feed.auto_update = True
        feed.is_failed = False
        feed.retries = 0
        feed.status = ''
        feed.save()
        # Trigger the fetch
        fetch_feed(feed.url, feed.id)
        feed.refresh_from_db()
        serializer = self.get_serializer(feed)
        return Response(serializer.data)


class FeedItemViewSet(viewsets.ModelViewSet):
    queryset = FeedItem.objects.all()
    lookup_url_kwarg = 'item_id'
    serializer_class = FeedItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_read', 'feed_id']
    ordering_fields = ['published', 'updated']
    ordering = '-published'

    def get_queryset(self):
        if 'feed_id' in self.kwargs:
            return self.queryset.filter(
                feed_id=self.kwargs['feed_id'],
                feed__owner=self.request.user)
        return self.queryset.filter(feed__owner=self.request.user)

    @action(detail=True)
    def read(self, request, feed_id=None, item_id=None):
        item = self.get_object()
        item.is_read = True
        item.save()
        serializer = self.get_serializer(item)
        return Response(serializer.data)

    @action(detail=True)
    def unread(self, request, feed_id=None, item_id=None):
        item = self.get_object()
        item.is_read = False
        item.save()
        serializer = self.get_serializer(item)
        return Response(serializer.data)
