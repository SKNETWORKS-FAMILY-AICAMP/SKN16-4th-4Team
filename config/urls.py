"""
URL configuration for elderly_rag_chatbot project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    """Health check endpoint for monitoring"""
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return JsonResponse({
        "status": "ok",
        "database": db_status,
        "service": "elderly_rag_chatbot"
    })

urlpatterns = [
    path('health/', health_check, name='health'),
    path('health', health_check, name='health_no_slash'),  # Support both with and without trailing slash
    path('admin/', admin.site.urls),
    path('', include('apps.chatbot_web.urls')),
]

# Static/media files serving in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
