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
    
    # Campaign management
    path('campaigns/<uuid:campaign_id>/contacts/', views.CampaignContactsView.as_view(), name='campaign-contacts'),
    path('campaigns/<uuid:campaign_id>/start/', views.StartCampaignView.as_view(), name='start-campaign'),
    path('campaigns/<uuid:campaign_id>/pause/', views.PauseCampaignView.as_view(), name='pause-campaign'),
    path('campaigns/<uuid:campaign_id>/stats/', views.CampaignStatsView.as_view(), name='campaign-stats'),
    
    # Bulk operations
    path('campaigns/bulk-create/', views.BulkCreateCampaignView.as_view(), name='bulk-create-campaign'),
    path('campaigns/<uuid:campaign_id>/add-contacts/', views.AddContactsToCampaignView.as_view(), name='add-contacts-to-campaign'),
    
    # Schedule management
    path('schedules/<uuid:schedule_id>/execute/', views.ExecuteScheduleView.as_view(), name='execute-schedule'),
    path('schedules/upcoming/', views.UpcomingSchedulesView.as_view(), name='upcoming-schedules'),
    
    # Time slot management
    path('time-slots/availability/', views.TimeSlotAvailabilityView.as_view(), name='time-slot-availability'),
    path('time-slots/book/', views.BookTimeSlotView.as_view(), name='book-time-slot'),
    
    # Analytics
    path('analytics/dashboard/', views.SchedulingDashboardView.as_view(), name='scheduling-dashboard'),
    path('analytics/campaign-performance/', views.CampaignPerformanceView.as_view(), name='campaign-performance'),
]
