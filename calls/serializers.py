from rest_framework import serializers
from .models import Call, CallConversation, CallTemplate, CallQueue

class CallSerializer(serializers.ModelSerializer):
    contact_name = serializers.CharField(source='contact.full_name', read_only=True)
    contact_phone = serializers.CharField(source='contact.phone_number', read_only=True)
    
    class Meta:
        model = Call
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'twilio_call_sid']

class CallConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallConversation
        fields = '__all__'
        read_only_fields = ['id', 'timestamp']

class CallTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallTemplate
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'usage_count']

class CallQueueSerializer(serializers.ModelSerializer):
    contact_name = serializers.CharField(source='contact.full_name', read_only=True)
    contact_phone = serializers.CharField(source='contact.phone_number', read_only=True)
    template_name = serializers.CharField(source='call_template.name', read_only=True)
    
    class Meta:
        model = CallQueue
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'attempt_count']
