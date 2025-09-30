from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from oauth2_provider import urls as oauth2_urls
from . import auth_views

urlpatterns = [
    # JWT Authentication
    path('jwt/login/', auth_views.CustomTokenObtainPairView.as_view(), name='jwt_login'),
    path('jwt/refresh/', TokenRefreshView.as_view(), name='jwt_refresh'),
    path('jwt/logout/', auth_views.logout_user, name='jwt_logout'),
    
    # OAuth2 Authentication
    path('oauth/', include(oauth2_urls)),
    
    # User Management
    path('register/', auth_views.register_user, name='register'),
    path('profile/', auth_views.user_profile, name='user_profile'),
    path('profile/update/', auth_views.update_profile, name='update_profile'),
    path('password/change/', auth_views.change_password, name='change_password'),
    path('permissions/', auth_views.user_permissions, name='user_permissions'),
]
