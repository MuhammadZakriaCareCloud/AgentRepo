from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class TwilioService:
    """
    Service class for Twilio integration
    """
    
    def __init__(self):
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.from_number = settings.TWILIO_PHONE_NUMBER
    
    def initiate_call(self, to_number, webhook_url, call_data=None):
        """
        Initiate an outbound call
        """
        try:
            call = self.client.calls.create(
                to=to_number,
                from_=self.from_number,
                url=webhook_url,
                method='POST',
                status_callback=f"{webhook_url}/status",
                status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
                status_callback_method='POST',
                record=settings.ENABLE_CALL_RECORDING,
                recording_status_callback=f"{webhook_url}/recording" if settings.ENABLE_CALL_RECORDING else None,
                timeout=30
            )
            
            logger.info(f"Call initiated: {call.sid} to {to_number}")
            return {
                'success': True,
                'call_sid': call.sid,
                'status': call.status
            }
            
        except Exception as e:
            logger.error(f"Failed to initiate call to {to_number}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_call_details(self, call_sid):
        """
        Get details of a specific call
        """
        try:
            call = self.client.calls(call_sid).fetch()
            return {
                'sid': call.sid,
                'from': call.from_,
                'to': call.to,
                'status': call.status,
                'duration': call.duration,
                'start_time': call.start_time,
                'end_time': call.end_time,
                'price': call.price,
                'price_unit': call.price_unit
            }
        except Exception as e:
            logger.error(f"Failed to get call details for {call_sid}: {str(e)}")
            return None
    
    def end_call(self, call_sid):
        """
        End an active call
        """
        try:
            call = self.client.calls(call_sid).update(status='completed')
            logger.info(f"Call ended: {call_sid}")
            return True
        except Exception as e:
            logger.error(f"Failed to end call {call_sid}: {str(e)}")
            return False
    
    def generate_twiml_response(self, message, voice='alice', language='en-US'):
        """
        Generate TwiML response for voice calls
        """
        response = VoiceResponse()
        response.say(message, voice=voice, language=language)
        return str(response)
    
    def generate_ai_twiml_response(self, ai_response, voice='alice', gather_input=False, webhook_url=None):
        """
        Generate TwiML response with AI integration
        """
        response = VoiceResponse()
        
        # Speak the AI response
        response.say(ai_response, voice=voice, language='en-US')
        
        # If we need to gather input from the caller
        if gather_input and webhook_url:
            gather = response.gather(
                input='speech',
                timeout=3,
                speech_timeout='auto',
                action=webhook_url,
                method='POST'
            )
            
            # Add a fallback message if no input is received
            response.say("I didn't hear anything. Please try again.", voice=voice)
            response.redirect(webhook_url)
        
        return str(response)
    
    def create_conference(self, conference_name, participant_numbers, webhook_url):
        """
        Create a conference call with multiple participants
        """
        try:
            conference_calls = []
            
            for number in participant_numbers:
                call = self.client.calls.create(
                    to=number,
                    from_=self.from_number,
                    url=f"{webhook_url}/conference/{conference_name}",
                    method='POST'
                )
                conference_calls.append(call.sid)
            
            return {
                'success': True,
                'conference_name': conference_name,
                'participant_calls': conference_calls
            }
            
        except Exception as e:
            logger.error(f"Failed to create conference {conference_name}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_recordings(self, call_sid):
        """
        Get recordings for a specific call
        """
        try:
            recordings = self.client.recordings.list(call_sid=call_sid)
            return [
                {
                    'sid': recording.sid,
                    'duration': recording.duration,
                    'date_created': recording.date_created,
                    'uri': recording.uri,
                    'media_url': f"https://api.twilio.com{recording.uri.replace('.json', '.mp3')}"
                }
                for recording in recordings
            ]
        except Exception as e:
            logger.error(f"Failed to get recordings for call {call_sid}: {str(e)}")
            return []
    
    def send_sms(self, to_number, message):
        """
        Send SMS message
        """
        try:
            message = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            
            logger.info(f"SMS sent: {message.sid} to {to_number}")
            return {
                'success': True,
                'message_sid': message.sid,
                'status': message.status
            }
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {to_number}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_call_logs(self, limit=50, date_created_after=None):
        """
        Get call logs from Twilio
        """
        try:
            calls = self.client.calls.list(
                limit=limit,
                date_created_after=date_created_after
            )
            
            return [
                {
                    'sid': call.sid,
                    'from': call.from_,
                    'to': call.to,
                    'status': call.status,
                    'duration': call.duration,
                    'start_time': call.start_time,
                    'end_time': call.end_time,
                    'direction': call.direction,
                    'price': call.price
                }
                for call in calls
            ]
            
        except Exception as e:
            logger.error(f"Failed to get call logs: {str(e)}")
            return []

# Singleton instance
twilio_service = TwilioService()
