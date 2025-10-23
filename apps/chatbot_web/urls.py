"""
간소화된 URL 패턴
"""
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import feedback_views

app_name = 'chatbot_web'

urlpatterns = [
    # Home
    path('', views.home, name='home'),

    # Authentication
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='chatbot_web/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Kakao Login
    path('kakao/login/', views.kakao_login, name='kakao_login'),
    path('kakao/callback/', views.kakao_callback, name='kakao_callback'),
    path('kakao/logout/', views.kakao_logout, name='kakao_logout'),

    # Chat
    path('chat/', views.chat_view, name='chat'),
    path('chat/new/', views.chat_new_session, name='chat_new_session'),
    path('chat/<str:session_id>/', views.chat_session, name='chat_session'),
    path('chat/api/message/', views.chat_api_message, name='chat_api_message'),
    path('chat/session/<str:session_id>/delete/', views.chat_session_delete, name='chat_session_delete'),

    # Validation Chat (Admin Only)
    path('validation/chat/', views.validation_chat_view, name='validation_chat'),
    path('validation/config/', views.validation_config_select, name='validation_config_select'),
    path('validation/chat/new/', views.validation_chat_new_session, name='validation_chat_new_session'),
    path('validation/chat/<str:session_id>/', views.validation_chat_session, name='validation_chat_session'),
    path('validation/chat/api/message/', views.validation_chat_api_message, name='validation_chat_api_message'),

    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/password-change/', views.password_change, name='password_change'),

    # Policy List
    path('policies/', views.policy_list, name='policy_list'),

    # Quick Start & FAQ
    path('quick-start/', views.quick_start, name='quick_start'),
    path('quick-start/recommend/', views.quick_start_recommend, name='quick_start_recommend'),
    path('faq/', views.faq, name='faq'),

    # Bookmarks
    path('bookmarks/', views.bookmark_list, name='bookmark_list'),
    path('bookmark/save/', views.bookmark_save, name='bookmark_save'),
    path('bookmark/<int:bookmark_id>/delete/', views.bookmark_delete, name='bookmark_delete'),

    # Admin Dashboard
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('chat-logs/', views.chat_logs, name='chat_logs'),
    path('user-management/', views.user_management, name='user_management'),
    path('user/<int:user_id>/toggle-admin/', views.user_toggle_admin, name='user_toggle_admin'),
    path('validation/chat-logs/', views.validation_chat_logs, name='validation_chat_logs'),
    path('monitoring/', views.monitoring_view, name='monitoring'),

    # Feedback System
    path('feedback/submit/', feedback_views.feedback_submit, name='feedback_submit'),
    path('feedback/analytics/', feedback_views.feedback_analytics, name='feedback_analytics'),
    path('session/rating/submit/', feedback_views.session_rating_submit, name='session_rating_submit'),

    # Chatbot Optimization (AutoRAG)
    path('optimization/', views.chatbot_optimization, name='chatbot_optimization'),
    path('optimization/text-extraction/', views.optimization_text_extraction, name='optimization_text_extraction'),
    path('optimization/chunking/', views.optimization_chunking, name='optimization_chunking'),
    path('optimization/embedding/', views.optimization_embedding, name='optimization_embedding'),
    path('optimization/retriever/', views.optimization_retriever, name='optimization_retriever'),
    path('optimization/rag-system/', views.optimization_rag_system, name='optimization_rag_system'),
    path('optimization/full-pipeline/', views.optimization_full_pipeline, name='optimization_full_pipeline'),

    # AutoRAG API Endpoints
    path('api/optimization/text-extraction/', views.api_run_text_extraction, name='api_run_text_extraction'),
    path('api/optimization/chunking/', views.api_run_chunking, name='api_run_chunking'),
    path('api/optimization/embedding/', views.api_run_embedding, name='api_run_embedding'),
    path('api/optimization/full/', views.api_run_full_optimization, name='api_run_full_optimization'),
]
