from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'contacts', views.ContactViewSet)
router.register(r'tags', views.ContactTagViewSet)
router.register(r'notes', views.ContactNoteViewSet)

app_name = 'crm'

urlpatterns = [
    path('', include(router.urls)),
    
    # Custom endpoints
    path('contacts/<uuid:contact_id>/calls/', views.ContactCallsView.as_view(), name='contact-calls'),
    path('contacts/<uuid:contact_id>/assign-tags/', views.AssignTagsView.as_view(), name='assign-tags'),
    path('contacts/import/', views.ContactImportView.as_view(), name='contact-import'),
    path('contacts/export/', views.ContactExportView.as_view(), name='contact-export'),
    
    # Analytics
    path('analytics/dashboard/', views.CRMDashboardView.as_view(), name='crm-dashboard'),
    path('analytics/contact-stats/', views.ContactStatsView.as_view(), name='contact-stats'),
]
