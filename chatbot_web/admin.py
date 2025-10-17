from django.contrib import admin
from .models import (
    UserProfile,
    RAGConfiguration,
    ChatSession,
    ChatMessage,
    UserFeedback,
    ElderlyPolicy,
    Bookmark
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'age', 'region']
    list_filter = ['region']
    search_fields = ['user__username']


@admin.register(RAGConfiguration)
class RAGConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'is_validation', 'build_status', 'created_by', 'created_at']
    list_filter = ['is_active', 'is_validation', 'build_status']
    search_fields = ['name', 'description']


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'rag_config', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'title']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['session', 'role', 'content_preview', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['content']

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = '내용'


@admin.register(UserFeedback)
class UserFeedbackAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__username', 'comment']


@admin.register(ElderlyPolicy)
class ElderlyPolicyAdmin(admin.ModelAdmin):
    list_display = ['title', 'provider', 'region', 'created_at']
    list_filter = ['region', 'provider']
    search_fields = ['title', 'description', 'provider']
    ordering = ['region', 'title']


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ['user', 'question_preview', 'chatbot_type', 'created_at']
    list_filter = ['chatbot_type', 'created_at']
    search_fields = ['user__username', 'question', 'answer']
    ordering = ['-created_at']

    def question_preview(self, obj):
        return obj.question[:50] + '...' if len(obj.question) > 50 else obj.question
    question_preview.short_description = '질문'
