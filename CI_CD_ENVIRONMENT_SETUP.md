# CI/CD Environment Setup Guide

This guide explains how to configure environment variables and secrets for the CI/CD pipeline.

## Setting Up GitHub Secrets

### Required Secrets

The CI/CD pipeline requires the following secret to be configured in your GitHub repository:

1. **WEATHER_API_KEY**: Your WeatherAPI.com API key

### How to Add GitHub Secrets

1. Go to your GitHub repository
2. Click on **Settings** tab
3. In the left sidebar, click **Secrets and variables** > **Actions**
4. Click **New repository secret**
5. Add the following secret:
   - **Name**: `WEATHER_API_KEY`
   - **Secret**: Your actual WeatherAPI.com API key

### Getting a WeatherAPI.com API Key

1. Visit [WeatherAPI.com](https://www.weatherapi.com/)
2. Sign up for a free account
3. Go to your dashboard and copy your API key
4. Add this key as the `WEATHER_API_KEY` secret in GitHub

## Environment Variables in CI

The following environment variables are automatically set in the CI pipeline:

### Development CI (ci-dev.yml)
- `WEATHER_API_KEY`: From GitHub secrets
- Test database is set up automatically using SQLite in memory

### Production CI (ci-prod.yml)
- `WEATHER_API_KEY`: From GitHub secrets
- `DATABASE_URL`: Set up for PostgreSQL integration tests
- Coverage reporting is enabled

## Local Development

For local development, create a `.env` file in the project root with:

```bash
WEATHER_API_KEY=your_actual_api_key_here
```

## Troubleshooting API Key Issues

### Common Issues:

1. **"Weather API key not found" error in CI**:
   - Ensure `WEATHER_API_KEY` is set as a GitHub secret
   - Check that the secret name matches exactly (case-sensitive)

2. **Tests failing with API initialization errors**:
   - Most tests should be mocked and not require a real API key
   - Check that test mocks are properly configured

3. **Local development issues**:
   - Ensure `.env` file exists and contains the API key
   - Make sure `.env` is in `.gitignore` (never commit API keys)

### Debug Steps:

1. Check if the secret is properly set in GitHub repository settings
2. Verify the secret name matches `WEATHER_API_KEY` exactly
3. Ensure the API key is valid by testing it locally
4. Check CI logs for specific error messages

## Security Notes

- Never commit API keys to version control
- Use GitHub secrets for sensitive data in CI/CD
- Regularly rotate API keys for security
- Use different API keys for different environments if possible

## Additional Configuration

### For Multiple Environments

If you need different API keys for staging/production:

1. Create environment-specific secrets:
   - `WEATHER_API_KEY_STAGING`
   - `WEATHER_API_KEY_PRODUCTION`

2. Update the workflow files to use the appropriate secret based on the environment

### For Self-Hosted Runners

If using self-hosted GitHub runners, ensure:
- The runner has access to the secrets
- Network connectivity to WeatherAPI.com is available
- Proper firewall rules are configured
