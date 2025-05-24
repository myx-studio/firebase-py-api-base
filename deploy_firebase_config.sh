#!/bin/bash

# deploy_firebase_config.sh - Script to deploy Firebase configuration files
# Usage: ./deploy_firebase_config.sh [project_id]

set -e  # Exit on any error

# Check if project ID was provided as argument
if [ $# -eq 1 ]; then
    PROJECT_ID="$1"
    echo "Using provided project ID: $PROJECT_ID"
else
    # Default to the project in .firebaserc if it exists
    if [ -f ".firebaserc" ]; then
        PROJECT_ID=$(grep -o '"default": "[^"]*' .firebaserc | cut -d'"' -f4)
        echo "Using project ID from .firebaserc: $PROJECT_ID"
    fi

    # If still no project ID, ask user
    if [ -z "$PROJECT_ID" ]; then
        echo "No project ID provided or found in .firebaserc"
        read -p "Enter your Firebase project ID: " PROJECT_ID
    fi
fi

# Ensure Firebase CLI is installed
if ! command -v firebase &> /dev/null; then
    echo "Firebase CLI not found. Please install it with npm:"
    echo "npm install -g firebase-tools"
    exit 1
fi

# Ensure user is logged in
firebase login --no-localhost

echo "Deploying Firebase configuration files to project: $PROJECT_ID"

# Deploy database rules
if [ -f "database.rules.json" ]; then
    echo "Deploying database rules..."
    firebase deploy --only database --project "$PROJECT_ID"
fi

# Deploy Firestore rules and indexes
if [ -f "firestore.rules" ] && [ -f "firestore.indexes.json" ]; then
    echo "Deploying Firestore rules and indexes separately..."
    
    # Deploy only Firestore rules first
    echo "Deploying Firestore rules..."
    firebase deploy --only firestore:rules --project "$PROJECT_ID"
    
    # Deploy only Firestore indexes if rules deployment succeeds
    if [ $? -eq 0 ]; then
        echo "Deploying Firestore indexes..."
        firebase deploy --only firestore:indexes --project "$PROJECT_ID"
        
        if [ $? -ne 0 ]; then
            echo "WARNING: Failed to deploy Firestore indexes."
            echo "This can happen if collections don't exist yet in your Firestore database."
            echo "You may need to create data in your collections first, then run this script again."
            
            # Ask if user wants to continue with other deployments
            read -p "Continue deploying other resources? (y/n): " continue_deploy
            if [[ "$continue_deploy" != "y" && "$continue_deploy" != "Y" ]]; then
                exit 1
            fi
        fi
    else
        echo "Failed to deploy Firestore rules. Skipping indexes deployment."
        
        # Ask if user wants to continue with other deployments
        read -p "Continue deploying other resources? (y/n): " continue_deploy
        if [[ "$continue_deploy" != "y" && "$continue_deploy" != "Y" ]]; then
            exit 1
        fi
    fi
fi

# Deploy Storage rules
if [ -f "storage.rules" ]; then
    echo "Deploying Storage rules..."
    firebase deploy --only storage --project "$PROJECT_ID"
fi

echo "Deployment of Firebase configuration files completed successfully!"