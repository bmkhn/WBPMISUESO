from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
# Register the ViewSet to the 'client-requests' endpoint
router.register(r'client-requests', api_views.ClientRequestViewSet, basename='client-request')

urlpatterns = router.urls