from rest_framework.routers import DefaultRouter
from .views import LearningMaterialViewSet

router = DefaultRouter()
router.register("", LearningMaterialViewSet, basename="material")

urlpatterns = router.urls
