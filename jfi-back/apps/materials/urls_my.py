from rest_framework.routers import DefaultRouter
from .views import MyMaterialViewSet

router = DefaultRouter()
router.register("", MyMaterialViewSet, basename="my-material")

urlpatterns = router.urls
