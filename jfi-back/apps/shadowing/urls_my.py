from rest_framework.routers import DefaultRouter
from .views import MyShadowingViewSet

router = DefaultRouter()
router.register("", MyShadowingViewSet, basename="my-shadowing")

urlpatterns = router.urls
