from django.contrib import admin
from .models import UserProfile, ChatHistory, Policy, Document


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'age', 'gender', 'region', 'created_at']
    list_filter = ['gender', 'region', 'disability', 'veteran', 'low_income']
    search_fields = ['user__username', 'region']


@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'question_preview', 'overall_score', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['user__username', 'question', 'answer']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']

    fieldsets = (
        ('대화 정보', {
            'fields': ('user', 'question', 'answer', 'created_at')
        }),
        ('평가 점수', {
            'fields': ('relevance_score', 'accuracy_score', 'completeness_score', 'overall_score'),
            'classes': ('collapse',)
        }),
    )

    def question_preview(self, obj):
        return obj.question[:50] + '...' if len(obj.question) > 50 else obj.question
    question_preview.short_description = '질문'

    def save_model(self, request, obj, form, change):
        obj.calculate_overall_score()
        super().save_model(request, obj, form, change)


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'target', 'created_at']
    list_filter = ['category']
    search_fields = ['title', 'description', 'target']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'file_type', 'category', 'is_synced', 'chunk_count', 'uploaded_by', 'created_at']
    list_filter = ['file_type', 'category', 'is_synced', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['is_synced', 'chunk_count', 'extracted_text', 'created_at', 'updated_at']

    fieldsets = (
        ('기본 정보', {
            'fields': ('title', 'file', 'file_type', 'category', 'description')
        }),
        ('동기화 상태', {
            'fields': ('is_synced', 'chunk_count', 'extracted_text'),
            'classes': ('collapse',)
        }),
        ('메타데이터', {
            'fields': ('uploaded_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
