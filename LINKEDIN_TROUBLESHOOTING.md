# LinkedIn Upload Troubleshooting Guide

## Issue Summary
The LinkedIn video upload is failing at Step 1 (Registration) with a 500 Internal Server Error.

## Recent Changes Made
I've updated the `linkedin_manager.py` file with the following improvements:

1. **Added Required Headers**:
   - `X-Restli-Protocol-Version: 2.0.0` (required by LinkedIn API)
   - `LinkedIn-Version: 202405` (latest API version)

2. **Enhanced Logging**:
   - Now logs full request details (URL, data, person URN)
   - Logs full response details (status code, headers, body)
   - This will help identify the exact cause of the error

3. **Person URN Auto-Formatting**:
   - Automatically formats person URN if it's just a number
   - Validates that URN starts with `urn:li:`

## Common Causes of 500 Error

### 1. Invalid or Expired Access Token
**Solution**: Generate a new LinkedIn access token
- Go to: https://www.linkedin.com/developers/apps
- Select your app
- Go to "Auth" tab
- Generate a new access token with these scopes:
  - `w_member_social` (for posting)
  - `r_liteprofile` (for reading profile)
  - `w_organization_social` (if posting to company page)

### 2. Incorrect Person/Organization URN Format
**Valid formats**:
- Personal profile: `urn:li:person:XXXXXXXXX`
- Organization/Company: `urn:li:organization:XXXXXXXXX`

**How to find your Person URN**:
```bash
curl -X GET 'https://api.linkedin.com/v2/me' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```
Look for the `id` field in the response.

**How to find your Organization URN** (for company page posting):
```bash
curl -X GET 'https://api.linkedin.com/v2/organizationalEntityAcls?q=roleAssignee' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -H 'X-Restli-Protocol-Version: 2.0.0'
```
Look for `organizationalTarget` fields where you have ADMINISTRATOR role.

**Important**: To post as a company page:
- Fill in the **Organization URN** field in Settings (leave Person URN filled too)
- You must have admin access to the company page
- Your access token needs `w_organization_social` scope (not just `w_member_social`)


### 3. Missing API Permissions
Ensure your LinkedIn app has:
- Video upload permissions enabled
- Proper OAuth scopes configured
- App is not in development mode restrictions

### 4. Access Token Scope Issues
The access token must have `w_member_social` scope for video uploads.

## Testing Steps

### Step 1: Verify Access Token
Run this command to test your access token:
```bash
curl -X GET 'https://api.linkedin.com/v2/me' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -H 'X-Restli-Protocol-Version: 2.0.0'
```

If this fails, your token is invalid/expired.

### Step 2: Check the Logs
After attempting an upload, check `app.log` for detailed error information:
- Request URL
- Request data (including person URN)
- Response status code
- Response body (will show specific LinkedIn error)

### Step 3: Verify Person URN
Make sure your Person URN in Settings is formatted correctly:
- Should start with `urn:li:person:` or `urn:li:organization:`
- Should not have any extra spaces or characters

## How to Fix

### Option 1: Regenerate Access Token (Most Common Fix)
1. Go to LinkedIn Developer Portal
2. Navigate to your app
3. Go to "Auth" tab
4. Click "Generate token"
5. Copy the new token
6. Update it in your app's Settings page

### Option 2: Update Person URN
1. Use the curl command above to get your person ID
2. Format it as: `urn:li:person:YOUR_ID`
3. Update in Settings page

### Option 3: Check API Version Compatibility
LinkedIn may have updated their API. If the above doesn't work:
1. Check LinkedIn's developer documentation: https://docs.microsoft.com/en-us/linkedin/
2. Verify the API endpoints are still correct
3. Check if there are new required fields

## Next Steps

1. **Try uploading again** - The enhanced logging will now show exactly what LinkedIn is returning
2. **Check the logs** - Look at `app.log` for the detailed error message
3. **Verify credentials** - Make sure your access token and person URN are correct
4. **Test with curl** - Use the curl commands above to test your credentials directly

## Additional Resources
- LinkedIn API Documentation: https://docs.microsoft.com/en-us/linkedin/marketing/integrations/community-management/shares/ugc-post-api
- LinkedIn Video Upload Guide: https://docs.microsoft.com/en-us/linkedin/marketing/integrations/community-management/shares/video-posts
- OAuth 2.0 Guide: https://docs.microsoft.com/en-us/linkedin/shared/authentication/authentication

## Contact Support
If the issue persists after trying all the above:
1. Share the relevant logs from `app.log`
2. Verify your LinkedIn app is approved for video uploads
3. Contact LinkedIn Developer Support
