"""
간소화된 URL 패턴
"""
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'chatbot_web'

urlpatterns = [
    # Home
    path('', views.home, name='home'),

    # Authentication
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='chatbot_web/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Chat
    path('chat/', views.chat_view, name='chat'),
    path('chat/new/', views.chat_new_session, name='chat_new_session'),
    path('chat/<str:session_id>/', views.chat_session, name='chat_session'),
    path('chat/api/message/', views.chat_api_message, name='chat_api_message'),
    path('chat/session/<str:session_id>/delete/', views.chat_session_delete, name='chat_session_delete'),

    # Validation Chat (Admin Only)
    path('validation/chat/', views.validation_chat_view, name='validation_chat'),
    path('validation/chat/new/', views.validation_chat_new_session, name='validation_chat_new_session'),
    path('validation/chat/<str:session_id>/', views.validation_chat_session, name='validation_chat_session'),
    path('validation/chat/api/message/', views.validation_chat_api_message, name='validation_chat_api_message'),

    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),

    # Bookmarks
    path('bookmarks/', views.bookmark_list, name='bookmark_list'),
    path('bookmarks/save/', views.bookmark_save, name='bookmark_save'),
    path('bookmarks/<int:bookmark_id>/delete/', views.bookmark_delete, name='bookmark_delete'),

    # Policy List
    # FAQ and Quick Start
    path('faq/', views.faq_view, name='faq'),
    path('quick-start/', views.quick_start_view, name='quick_start'),

    path('policies/', views.policy_list, name='policy_list'),

    # Admin Dashboard
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('chat-logs/', views.chat_logs, name='chat_logs'),
    path('api/chat/session/<str:session_id>/', views.chat_session_detail_api, name='chat_session_detail_api'),
    path('user-management/', views.user_management, name='user_management'),
    path('user/<int:user_id>/toggle-admin/', views.user_toggle_admin, name='user_toggle_admin'),
    path('validation/chat-logs/', views.validation_chat_logs, name='validation_chat_logs'),
]
