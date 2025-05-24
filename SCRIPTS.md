# Parent CEO API Scripts

This document explains the utility scripts available for running and deploying the Parent CEO API.

## Development Scripts

### Run Emulator (`run_emulator.sh`)

This script starts the Firebase emulators with the development environment configuration.

```bash
./run_emulator.sh
```

**What it does:**

1. Sets the environment to `development` mode
2. Installs dependencies if needed
3. Loads environment variables from the `.env` file
4. Sets up emulator host environment variables
5. Starts the Firebase emulators for:
   - Functions
   - Firestore
   - Realtime Database
   - Authentication
   - Storage

**Accessing the emulator:**

- Functions: http://localhost:5001
- Firestore: http://localhost:8080
- Database: http://localhost:9000
- Auth: http://localhost:9099
- Storage: http://localhost:9199
- Emulator UI: http://localhost:4000

## Production Scripts

### Deploy to Production (`deploy_prod.sh`)

This script deploys the Firebase functions to the production environment.

```bash
./deploy_prod.sh
```

**What it does:**

1. Sets the environment to `production` mode
2. Installs dependencies if needed
3. Runs linting and unit tests
4. Deploys the functions to Firebase
5. Verifies the deployment was successful

**Production URLs:**

- Functions: https://us-central1-parent-ceo.cloudfunctions.net
- Cloud Run: https://parent-ceo-ojvc7r2mua-uc.a.run.app

## Environment Configuration

Both scripts use the appropriate environment configuration:

- `run_emulator.sh` uses the settings in `functions/config/dev.py`
- `deploy_prod.sh` uses the settings in `functions/config/prod.py`

You can customize the environment variables by editing the `.env` file for local development.

## Troubleshooting

### Common Issues with Emulators

1. **Port conflicts**: If you see errors about ports being in use, make sure you don't have other Firebase emulators running.
   
   ```bash
   # Find and kill processes using the ports
   lsof -i :8080 -i :9000 -i :9099 -i :9199 -i :5001
   kill -9 [PID]
   ```

2. **Authentication problems**: If you're having authentication issues in the emulator, try:
   
   ```bash
   firebase emulators:start --only auth
   # Then in another terminal
   firebase auth:export auth_export.json
   firebase auth:import auth_export.json
   ```

### Deployment Issues

1. **Permission errors**: Make sure you're logged in with the correct Firebase account:
   
   ```bash
   firebase logout
   firebase login
   ```

2. **Project selection**: Verify you're using the correct project:
   
   ```bash
   firebase use parent-ceo
   ```

3. **Artifact Registry permissions**: If you get errors about Artifact Registry access:
   
   ```bash
   gcloud projects add-iam-policy-binding parent-ceo --member=serviceAccount:[your-service-account] --role=roles/artifactregistry.reader
   ```

## Testing and Debugging

### Test Email Service (`functions/test_email.py`)

This script allows you to test the email service configuration by sending a test email.

```bash
cd functions
./test_email.py recipient@example.com
```

**Options:**
- `--subject`: Custom subject for the test email
- `--message`: Custom message to include in the email

Example:
```bash
./test_email.py recipient@example.com --subject "Test Subject" --message "<p>This is a test message.</p>"
```

This is useful for:
- Verifying Mailgun configuration is correct
- Testing email deliverability
- Checking email template rendering

## Additional Commands

- **View deployed functions:**
  ```bash
  firebase functions:list
  ```

- **Delete a deployed function:**
  ```bash
  firebase functions:delete functionName
  ```

- **View function logs:**
  ```bash
  firebase functions:log
  ```