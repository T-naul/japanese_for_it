from rest_framework.routers import DefaultRouter
from .views import ShadowingVideoViewSet

router = DefaultRouter()
router.register("videos", ShadowingVideoViewSet, basename="shadowing-video")

urlpatterns = router.urls
