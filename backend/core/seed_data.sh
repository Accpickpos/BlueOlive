#!/bin/bash
# Quick seed data script
# Run this from the project root directory: bash seed_data.sh

echo "========================================="
echo "BlueOlive Data Seeding Script"
echo "========================================="
echo ""

# Check if Django is available
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please activate your virtual environment."
    exit 1
fi

# Run migrations first
echo "🔄 Running migrations..."
python manage.py migrate
echo ""

# Run the master seed command
echo "🌱 Seeding all data..."
python manage.py seed_all_data
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
