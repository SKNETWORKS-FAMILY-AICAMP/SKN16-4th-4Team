from django.contrib import admin
from .models import UserProfile, ChatHistory, Policy


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
