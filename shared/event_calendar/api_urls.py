from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'meeting-events', views.MeetingEventViewSet, basename='meeting-event')

urlpatterns = router.urls