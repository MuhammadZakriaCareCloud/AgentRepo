from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated  
from .models import Campaign, CampaignContact, Schedule, ScheduleExecution, CallTimeSlot


class CampaignViewSet(viewsets.ModelViewSet):
    """ViewSet for managing campaigns"""
    queryset = Campaign.objects.all()
    permission_classes = [IsAuthenticated]
    ordering = ['-created_at']

    def get_serializer_class(self):
        from rest_framework import serializers
        
        class CampaignSerializer(serializers.ModelSerializer):
            class Meta:
                model = Campaign
                fields = '__all__'
        
        return CampaignSerializer


class CampaignContactViewSet(viewsets.ModelViewSet):
    """ViewSet for managing campaign contacts"""
    queryset = CampaignContact.objects.all()
    permission_classes = [IsAuthenticated]
    ordering = ['-created_at']

    def get_serializer_class(self):
        from rest_framework import serializers
        
        class CampaignContactSerializer(serializers.ModelSerializer):
            class Meta:
                model = CampaignContact
                fields = '__all__'
        
        return CampaignContactSerializer


class ScheduleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing schedules"""
    queryset = Schedule.objects.all()
    permission_classes = [IsAuthenticated]
    ordering = ['-created_at']

    def get_serializer_class(self):
        from rest_framework import serializers
        
        class ScheduleSerializer(serializers.ModelSerializer):
            class Meta:
                model = Schedule
                fields = '__all__'
        
        return ScheduleSerializer


class CallTimeSlotViewSet(viewsets.ModelViewSet):
    """ViewSet for managing call time slots"""
    queryset = CallTimeSlot.objects.all()
    permission_classes = [IsAuthenticated]
    ordering = ['date', 'time_slot']

    def get_serializer_class(self):
        from rest_framework import serializers
        
        class CallTimeSlotSerializer(serializers.ModelSerializer):
            class Meta:
                model = CallTimeSlot
                fields = '__all__'
        
        return CallTimeSlotSerializer


class ScheduleExecutionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing schedule executions"""
    queryset = ScheduleExecution.objects.all()
    permission_classes = [IsAuthenticated]
    ordering = ['-executed_at']

    def get_serializer_class(self):
        from rest_framework import serializers
        
        class ScheduleExecutionSerializer(serializers.ModelSerializer):
            class Meta:
                model = ScheduleExecution
                fields = '__all__'
        
        return ScheduleExecutionSerializer
