from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Contact, ContactNote, ContactTag
from django.contrib.auth.models import User


class ContactViewSet(viewsets.ModelViewSet):
    """ViewSet for managing contacts"""
    queryset = Contact.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['contact_type', 'lead_source', 'do_not_call']
    search_fields = ['first_name', 'last_name', 'email', 'company']
    ordering_fields = ['created_at', 'last_contacted', 'first_name']
    ordering = ['-created_at']

    def get_serializer_class(self):
        # Simple serializer for now
        from rest_framework import serializers
        
        class ContactSerializer(serializers.ModelSerializer):
            class Meta:
                model = Contact
                fields = '__all__'
        
        return ContactSerializer


class ContactNoteViewSet(viewsets.ModelViewSet):
    """ViewSet for managing contact notes"""
    queryset = ContactNote.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['contact', 'note_type']
    search_fields = ['title', 'content']
    ordering = ['-created_at']

    def get_serializer_class(self):
        from rest_framework import serializers
        
        class ContactNoteSerializer(serializers.ModelSerializer):
            class Meta:
                model = ContactNote
                fields = '__all__'
        
        return ContactNoteSerializer


class ContactTagViewSet(viewsets.ModelViewSet):
    """ViewSet for managing contact tags"""
    queryset = ContactTag.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering = ['name']

    def get_serializer_class(self):
        from rest_framework import serializers
        
        class ContactTagSerializer(serializers.ModelSerializer):
            class Meta:
                model = ContactTag
                fields = '__all__'
        
        return ContactTagSerializer
