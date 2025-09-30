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
]
