#!/bin/bash
# Quick seed data script - Seeds all test data in proper order
# Run this from the project root directory: bash seed_data.sh

set -e  # Exit on first error

echo "========================================="
echo "BlueOlive Data Seeding Script"
echo "========================================="
echo ""

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please activate your virtual environment."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ manage.py not found. Please run this from the project root directory."
    exit 1
fi

# Run migrations first (required for seeding)
echo "🔄 Running migrations..."
python manage.py migrate
if [ $? -ne 0 ]; then
    echo "❌ Migrations failed!"
    echo "   Make sure your database is properly configured and running."
    exit 1
fi
echo ""

# Check if admin user exists
if ! python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print('OK' if User.objects.filter(is_staff=True).exists() else exit(1))" > /dev/null 2>&1; then
    echo "⚠️  No admin user found!"
    echo "   Run: python manage.py createsuperuser"
    echo ""
    echo "   Or use the quick command:"
    echo "   python manage.py shell -c \"from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@test.com', 'admin123')\""
    exit 1
fi

# Run the master seed command with error handling
echo "🌱 Seeding all data (this may take a moment)..."
if python manage.py seed_all_data; then
    echo ""
    echo "========================================="
    echo "✅ Data seeding complete!"
    echo "========================================="
    echo ""
    echo "You can now:"
    echo "1. Run the server: python manage.py runserver"
    echo "2. Check data in Django admin: http://localhost:8000/admin"
    echo "3. Test API endpoints with the frontend"
    echo ""
else
    echo ""
    echo "========================================="
    echo "❌ Seeding failed!"
    echo "========================================="
    echo ""
    echo "Troubleshooting:"
    echo "1. Check that migrations are complete: python manage.py migrate"
    echo "2. Verify admin user exists: python manage.py createsuperuser"
    echo "3. Check database connection: python manage.py dbshell"
    echo "4. Run with verbose output: python manage.py seed_all_data --verbosity 3"
    exit 1
fi
