#!/bin/bash
# ================================================================================================
# Docker Entrypoint Script for Django Application
# ================================================================================================

set -e

echo "🚀 Starting Django application..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
while ! pg_isready -h ${POSTGRES_HOST:-postgres} -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER:-elderly_rag_user} > /dev/null 2>&1; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
done
echo "✅ PostgreSQL is ready!"

# Run database migrations
echo "📊 Running database migrations..."
python manage.py migrate --noinput

# Create superuser if it doesn't exist
echo "👤 Creating superuser if needed..."
python manage.py shell << EOF
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('✅ Superuser created: admin/admin123')
else:
    print('ℹ️ Superuser already exists')
EOF

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Load welfare documents into ChromaDB (only if needed)
if [ "${LOAD_DOCUMENTS:-true}" = "true" ]; then
    echo "📚 Loading welfare documents into ChromaDB..."
    python manage.py load_welfare_documents || echo "⚠️ Document loading failed or not implemented yet"
fi

# Setup chatbot database with initial data
echo "🤖 Setting up chatbot database..."
python manage.py setup_chatbot_database || echo "⚠️ Chatbot database setup skipped"

echo "✅ Django initialization complete!"
echo "🎯 Starting application server..."

# Execute the main command (Gunicorn)
exec "$@"
