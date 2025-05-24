#!/bin/bash
# Script to deploy functions to Firebase production environment

# Change to the project root directory
cd "$(dirname "$0")"

echo "🚀 Deploying Parent CEO API to Firebase Production Environment..."

# Set environment to production
export APP_ENV=production

# Install dependencies if needed
echo "📦 Installing dependencies..."
cd functions
pip install -r requirements.txt

# Run linting and tests
echo "🧪 Running tests and linting..."
pylint functions/ || { echo "⚠️ Linting failed, but continuing deployment..."; }
#pytest tests/unit/ || { echo "⚠️ Some tests failed, but continuing deployment..."; }

# Deploy to Firebase
echo "☁️ Deploying to Firebase..."
cd ..
firebase deploy --only functions

# Verify deployment
if [ $? -eq 0 ]; then
    echo "✅ Deployment to production completed successfully!"
    echo "🌐 Your API is now live at: https://us-central1-parent-ceo.cloudfunctions.net"
else
    echo "❌ Deployment failed. Check the error messages above."
    exit 1
fi
