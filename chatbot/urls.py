from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('policies/', views.policies_view, name='policies'),
    path('chatbot/', views.chatbot_view, name='chatbot'),
    path('api/chatbot/', views.chatbot_api, name='chatbot_api'),

    # 관리자 전용 URL
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-users/', views.admin_user_management, name='admin_user_management'),
    path('admin-users/<int:user_id>/toggle-staff/', views.admin_toggle_staff, name='admin_toggle_staff'),
    path('admin-chats/', views.admin_chat_logs, name='admin_chat_logs'),
    path('api/admin/evaluate/<int:chat_id>/', views.admin_evaluate_response, name='admin_evaluate_response'),

    # 문서 관리 URL
    path('admin-documents/', views.admin_documents, name='admin_documents'),
    path('admin-documents/upload/', views.admin_document_upload, name='admin_document_upload'),
    path('admin-documents/<int:doc_id>/delete/', views.admin_document_delete, name='admin_document_delete'),
    path('api/admin/documents/<int:doc_id>/resync/', views.admin_document_resync, name='admin_document_resync'),
]
