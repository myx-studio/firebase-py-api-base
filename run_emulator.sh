#!/bin/bash
# Script to run Firebase emulator with development environment settings

# Change to the project root directory
cd "$(dirname "$0")"

echo "🔥 Starting Firebase Emulator for Parent CEO API (Development Environment)..."

# Set environment to development
export APP_ENV=development

# Install dependencies if needed
echo "📦 Checking dependencies..."
cd functions
pip install -r requirements.txt

# Load environment variables from .env file
if [ -f .env ]; then
    echo "🔐 Loading environment variables from .env file..."
    set -a
    source .env
    set +a
else
    echo "⚠️ No .env file found. Using default configuration."
fi

# Return to root directory
cd ..

# Export emulator host for testing
export FIREBASE_AUTH_EMULATOR_HOST=localhost:9099
export FIRESTORE_EMULATOR_HOST=localhost:8080
export FIREBASE_DATABASE_EMULATOR_HOST=localhost:9000
export FIREBASE_STORAGE_EMULATOR_HOST=localhost:9199

# Start Firebase emulator
echo "🚀 Starting Firebase emulators..."
firebase emulators:start --only functions,firestore,database,auth,storage

# Check if emulator started successfully
if [ $? -ne 0 ]; then
    echo "❌ Failed to start Firebase emulators. Check the error messages above."
    exit 1
fi