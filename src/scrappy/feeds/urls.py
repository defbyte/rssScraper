from django.urls import include, path
from rest_framework.routers import DefaultRouter
from scrappy.feeds import views

router = DefaultRouter()
router.register(r'feeds', views.FeedViewSet, basename='feed')
router.register(r'feeds/(?P<feed_id>[^/.]+)/items',
                views.FeedItemViewSet, basename='feed-item')
# So that we can get global lists of feed items for the user
router.register(r'feed-items', views.FeedItemViewSet, basename='feed-item')

urlpatterns = [
    path('', include(router.urls)),
]
