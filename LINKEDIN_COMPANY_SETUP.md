# LinkedIn Company Page Posting - Setup Guide

## Overview
Your application now supports posting to LinkedIn as a **Company/Organization Page** instead of just personal profiles!

## What Changed

### 1. Code Updates
- **linkedin_manager.py**: Now accepts both `person_urn` and `organization_urn` parameters
- **social_media_manager.py**: Passes organization URN to LinkedIn upload function
- **app.py**: Added organization_urn field to settings
- **settings.html**: Added Organization URN input field with helpful description

### 2. New Features
- ✅ Post as personal profile (existing functionality)
- ✅ Post as company/organization page (NEW!)
- ✅ Automatic URN format validation
- ✅ Enhanced logging for debugging
- ✅ Test script supports both personal and organization testing

## How to Set Up Company Page Posting

### Step 1: Get Your Organization URN

**Option A: Use the Test Script**
```bash
python test_linkedin.py
```
The script will automatically detect organizations you can post as.

**Option B: Manual API Call**
```bash
curl -X GET 'https://api.linkedin.com/v2/organizationalEntityAcls?q=roleAssignee' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -H 'X-Restli-Protocol-Version: 2.0.0'
```

Look for entries where you have `ADMINISTRATOR` role. The `organizationalTarget` field contains your Organization URN.

Example response:
```json
{
  "elements": [
    {
      "organizationalTarget": "urn:li:organization:12345678",
      "role": "ADMINISTRATOR"
    }
  ]
}
```

### Step 2: Update Your Access Token Scopes

Your LinkedIn access token needs the `w_organization_social` scope to post as a company page.

**To generate a new token with correct scopes:**
1. Go to https://www.linkedin.com/developers/apps
2. Select your app
3. Go to "Auth" tab
4. Under "OAuth 2.0 scopes", ensure these are checked:
   - ✅ `r_liteprofile` (Read profile)
   - ✅ `w_member_social` (Post as personal)
   - ✅ `w_organization_social` (Post as company - REQUIRED!)
5. Click "Generate token"
6. Copy the new token

### Step 3: Configure Settings in Your App

1. Open your app and go to **Settings**
2. Scroll to **LinkedIn Configuration**
3. Fill in:
   - **Access Token**: Your new token with organization scope
   - **Person URN**: Your personal URN (e.g., `urn:li:person:12345`)
   - **Organization URN**: Your company URN (e.g., `urn:li:organization:67890`)
4. Click **Save All Settings**

### Step 4: Test It!

1. Go to **Social** page
2. Schedule a post
3. Select **LinkedIn** as platform
4. The post will be made as your **company page** (if Organization URN is filled)

## How It Works

The system uses this logic:
```
IF organization_urn is provided:
    Post as company page using organization_urn
ELSE:
    Post as personal profile using person_urn
```

## Important Notes

### ✅ Requirements for Company Posting
- You must be an **ADMINISTRATOR** of the company page
- Access token must have `w_organization_social` scope
- Both Person URN and Organization URN should be filled in Settings

### ⚠️ Common Issues

**Issue**: "Invalid access token" error
**Solution**: Generate new token with `w_organization_social` scope

**Issue**: "Permission denied" error
**Solution**: Verify you have admin access to the company page

**Issue**: Posts still going to personal profile
**Solution**: Make sure Organization URN field is filled in Settings

## Testing Your Setup

Run the test script to verify everything works:
```bash
python test_linkedin.py
```

The script will:
1. ✅ Verify your access token
2. ✅ Show your Person URN
3. ✅ List all organizations you can post as
4. ✅ Let you choose which to test
5. ✅ Test the video upload registration

## Example Settings Configuration

### For Personal Posting Only:
```
Access Token: AQV...xyz
Person URN: urn:li:person:abc123
Organization URN: [leave blank]
```

### For Company Page Posting:
```
Access Token: AQV...xyz
Person URN: urn:li:person:abc123
Organization URN: urn:li:organization:456789
```

## Troubleshooting

If you encounter issues, check:
1. ✅ Access token has `w_organization_social` scope
2. ✅ Organization URN is correctly formatted
3. ✅ You have admin access to the company page
4. ✅ Both URNs are filled in Settings
5. ✅ Check `app.log` for detailed error messages

For more help, see `LINKEDIN_TROUBLESHOOTING.md`

## Next Steps

1. **Generate new access token** with organization scope
2. **Find your organization URN** using test script or API
3. **Update Settings** with both URNs
4. **Test posting** to verify it works!

---

**Need Help?**
- Run `python test_linkedin.py` to diagnose issues
- Check `app.log` for detailed error messages
- Review `LINKEDIN_TROUBLESHOOTING.md` for common solutions
