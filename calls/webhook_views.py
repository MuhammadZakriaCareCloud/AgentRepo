from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone
from twilio.twiml.voice_response import VoiceResponse
from twilio.request_validator import RequestValidator
from django.conf import settings
import json
import logging

from calls.models import Call, CallConversation
from calls.services.twilio_service import twilio_service
from calls.tasks import process_ai_conversation, generate_call_summary

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class TwilioWebhookView(View):
    """Base class for Twilio webhook views"""
    
    def validate_twilio_request(self, request):
        """Validate that the request is from Twilio"""
        if not settings.DEBUG:  # Skip validation in debug mode
            validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
            url = request.build_absolute_uri()
            signature = request.META.get('HTTP_X_TWILIO_SIGNATURE', '')
            
            if not validator.validate(url, request.POST, signature):
                logger.warning(f"Invalid Twilio signature for URL: {url}")
                return False
        return True

@method_decorator(csrf_exempt, name='dispatch')
class TwilioVoiceWebhook(TwilioWebhookView):
    """Handle Twilio voice webhooks for AI-powered calls"""
    
    def post(self, request):
        if not self.validate_twilio_request(request):
            return HttpResponse('Forbidden', status=403)
        
        # Get call information
        call_sid = request.POST.get('CallSid')
        call_id = request.GET.get('call_id')
        from_number = request.POST.get('From')
        to_number = request.POST.get('To')
        speech_result = request.POST.get('SpeechResult', '').strip()
        
        logger.info(f"Voice webhook - Call SID: {call_sid}, Speech: {speech_result}")
        
        try:
            # Get or create call record
            if call_id:
                call = Call.objects.get(id=call_id)
            else:
                # This is an inbound call
                from crm.models import Contact
                try:
                    contact = Contact.objects.get(phone_number=from_number)
                except Contact.DoesNotExist:
                    # Create a new contact for inbound calls
                    contact = Contact.objects.create(
                        first_name='Unknown',
                        last_name='Caller',
                        phone_number=from_number,
                        contact_type='lead'
                    )
                
                call = Call.objects.create(
                    call_type='inbound',
                    contact=contact,
                    from_number=from_number,
                    to_number=to_number,
                    twilio_call_sid=call_sid,
                    status='in_progress',
                    started_at=timezone.now(),
                    ai_enabled=True
                )
            
            # Generate TwiML response
            response = VoiceResponse()
            
            if not speech_result:
                # First interaction or no speech detected
                if call.call_type == 'outbound':
                    greeting = self._get_outbound_greeting(call)
                else:
                    greeting = self._get_inbound_greeting(call)
                
                response.say(greeting, voice='alice')
                
                # Set up speech recognition for next input
                gather = response.gather(
                    input='speech',
                    timeout=5,
                    speech_timeout='auto',
                    action=request.build_absolute_uri(),
                    method='POST'
                )
                
                # Fallback if no speech detected
                response.say("I didn't hear anything. Let me try again.")
                response.redirect(request.build_absolute_uri())
                
            else:
                # Process AI conversation in background
                task_result = process_ai_conversation.delay(
                    str(call.id), 
                    speech_result, 
                    call.ai_conversation_id
                )
                
                # For now, provide a simple response
                # In production, you might want to wait for the AI response or use a different approach
                response.say(
                    "Thank you for that information. Let me process what you've said.",
                    voice='alice'
                )
                
                # Continue the conversation
                gather = response.gather(
                    input='speech',
                    timeout=5,
                    speech_timeout='auto',
                    action=request.build_absolute_uri(),
                    method='POST'
                )
                
                # End call option
                response.say("Thank you for calling. Have a great day!")
                response.hangup()
            
            return HttpResponse(str(response), content_type='text/xml')
            
        except Exception as e:
            logger.error(f"Error in voice webhook: {str(e)}")
            response = VoiceResponse()
            response.say("I'm sorry, there was a technical issue. Please try calling back later.")
            response.hangup()
            return HttpResponse(str(response), content_type='text/xml')
    
    def _get_outbound_greeting(self, call):
        """Generate greeting for outbound calls"""
        if call.call_template:
            return call.call_template.initial_greeting
        
        return f"Hello {call.contact.first_name}, this is an automated call from our company. How can I help you today?"
    
    def _get_inbound_greeting(self, call):
        """Generate greeting for inbound calls"""
        return "Hello! Thank you for calling. I'm an AI assistant here to help you. How can I assist you today?"

@method_decorator(csrf_exempt, name='dispatch')
class TwilioCallStatusWebhook(TwilioWebhookView):
    """Handle call status updates from Twilio"""
    
    def post(self, request):
        if not self.validate_twilio_request(request):
            return HttpResponse('Forbidden', status=403)
        
        call_sid = request.POST.get('CallSid')
        call_status = request.POST.get('CallStatus')
        call_duration = request.POST.get('CallDuration')
        
        logger.info(f"Call status update - SID: {call_sid}, Status: {call_status}")
        
        try:
            call = Call.objects.get(twilio_call_sid=call_sid)
            call.status = call_status.lower()
            
            if call_status == 'completed':
                call.ended_at = timezone.now()
                if call_duration:
                    call.duration = timezone.timedelta(seconds=int(call_duration))
                
                # Generate call summary in background
                generate_call_summary.delay(str(call.id))
            
            elif call_status == 'in-progress':
                if not call.started_at:
                    call.started_at = timezone.now()
            
            call.save()
            
            return HttpResponse('OK')
            
        except Call.DoesNotExist:
            logger.warning(f"Call not found for SID: {call_sid}")
            return HttpResponse('Call not found', status=404)
        except Exception as e:
            logger.error(f"Error updating call status: {str(e)}")
            return HttpResponse('Error', status=500)

@method_decorator(csrf_exempt, name='dispatch')
class TwilioRecordingWebhook(TwilioWebhookView):
    """Handle recording notifications from Twilio"""
    
    def post(self, request):
        if not self.validate_twilio_request(request):
            return HttpResponse('Forbidden', status=403)
        
        call_sid = request.POST.get('CallSid')
        recording_sid = request.POST.get('RecordingSid')
        recording_url = request.POST.get('RecordingUrl')
        recording_duration = request.POST.get('RecordingDuration')
        
        logger.info(f"Recording webhook - Call SID: {call_sid}, Recording SID: {recording_sid}")
        
        try:
            call = Call.objects.get(twilio_call_sid=call_sid)
            call.recording_sid = recording_sid
            call.recording_url = recording_url
            call.save()
            
            return HttpResponse('OK')
            
        except Call.DoesNotExist:
            logger.warning(f"Call not found for recording SID: {recording_sid}")
            return HttpResponse('Call not found', status=404)
        except Exception as e:
            logger.error(f"Error processing recording webhook: {str(e)}")
            return HttpResponse('Error', status=500)

@method_decorator(csrf_exempt, name='dispatch')
class TwilioTranscriptionWebhook(TwilioWebhookView):
    """Handle transcription notifications from Twilio"""
    
    def post(self, request):
        if not self.validate_twilio_request(request):
            return HttpResponse('Forbidden', status=403)
        
        call_sid = request.POST.get('CallSid')
        transcription_text = request.POST.get('TranscriptionText')
        transcription_status = request.POST.get('TranscriptionStatus')
        
        logger.info(f"Transcription webhook - Call SID: {call_sid}, Status: {transcription_status}")
        
        try:
            call = Call.objects.get(twilio_call_sid=call_sid)
            
            if transcription_status == 'completed' and transcription_text:
                # Store transcription in call metadata
                if not call.call_metadata:
                    call.call_metadata = {}
                call.call_metadata['transcription'] = transcription_text
                call.save()
                
                # Create conversation entry
                CallConversation.objects.create(
                    call=call,
                    speaker_type='system',
                    message=f"Call transcription: {transcription_text}"
                )
            
            return HttpResponse('OK')
            
        except Call.DoesNotExist:
            logger.warning(f"Call not found for transcription SID: {call_sid}")
            return HttpResponse('Call not found', status=404)
        except Exception as e:
            logger.error(f"Error processing transcription webhook: {str(e)}")
            return HttpResponse('Error', status=500)

@method_decorator(csrf_exempt, name='dispatch')
class AIResponseWebhook(View):
    """Handle AI response processing"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            call_id = data.get('call_id')
            ai_response = data.get('response')
            
            if not call_id or not ai_response:
                return HttpResponse('Missing required data', status=400)
            
            call = Call.objects.get(id=call_id)
            
            # Generate TwiML with AI response
            twiml = twilio_service.generate_ai_twiml_response(
                ai_response,
                voice='alice',
                gather_input=True,
                webhook_url=f"/webhooks/twilio/voice/?call_id={call_id}"
            )
            
            return HttpResponse(twiml, content_type='text/xml')
            
        except Exception as e:
            logger.error(f"Error in AI response webhook: {str(e)}")
            return HttpResponse('Error', status=500)
