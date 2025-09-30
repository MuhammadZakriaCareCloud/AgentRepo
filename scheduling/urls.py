from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'campaigns', views.CampaignViewSet)
router.register(r'schedules', views.ScheduleViewSet)
router.register(r'time-slots', views.CallTimeSlotViewSet)
router.register(r'executions', views.ScheduleExecutionViewSet)

app_name = 'scheduling'

urlpatterns = [
    path('', include(router.urls)),
]
