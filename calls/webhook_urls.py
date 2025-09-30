from django.urls import path
from . import webhook_views

app_name = 'call_webhooks'

urlpatterns = [
    # Twilio webhooks
    path('call-status/', webhook_views.TwilioCallStatusWebhook.as_view(), name='call-status'),
    path('voice/', webhook_views.TwilioVoiceWebhook.as_view(), name='voice'),
    path('recording/', webhook_views.TwilioRecordingWebhook.as_view(), name='recording'),
    path('transcription/', webhook_views.TwilioTranscriptionWebhook.as_view(), name='transcription'),
    
    # AI Integration webhooks
    path('ai-response/', webhook_views.AIResponseWebhook.as_view(), name='ai-response'),
]
