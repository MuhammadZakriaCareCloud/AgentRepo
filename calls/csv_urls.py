"""
CSV Upload URLs for Outbound Calling
"""
from django.urls import path
from . import csv_upload_views

app_name = 'csv_upload'

urlpatterns = [
    # CSV Upload endpoints
    path('upload-contacts/', csv_upload_views.upload_csv_contacts, name='upload_csv_contacts'),
    path('upload-knowledge/', csv_upload_views.create_knowledge_base_from_csv, name='upload_knowledge_base'),
    
    # Campaign management
    path('campaign/<uuid:campaign_id>/queue-calls/', csv_upload_views.queue_calls_from_campaign, name='queue_campaign_calls'),
    path('campaign/<uuid:campaign_id>/status/', csv_upload_views.get_campaign_status, name='campaign_status'),
]
