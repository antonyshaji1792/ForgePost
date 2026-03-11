# Quick Start: LinkedIn Company Page Posting

## 🚀 3-Step Setup

### 1️⃣ Get Organization URN
```bash
python test_linkedin.py
```
Choose option 2 when prompted to see your company pages.

### 2️⃣ Generate New Access Token
Go to: https://www.linkedin.com/developers/apps
- Select your app → Auth tab
- Enable scope: `w_organization_social` ✅
- Click "Generate token"

### 3️⃣ Update Settings
In your app Settings page, fill in:
- **Access Token**: [your new token]
- **Person URN**: `urn:li:person:12345`
- **Organization URN**: `urn:li:organization:67890` ← **NEW!**

## ✅ Done!
Now when you post to LinkedIn, it will post as your **company page** instead of your personal profile!

---

## 📋 Quick Checklist
- [ ] Access token has `w_organization_social` scope
- [ ] You are admin of the company page
- [ ] Organization URN is filled in Settings
- [ ] Person URN is also filled (required)
- [ ] Tested with `python test_linkedin.py`

## 🆘 Still Getting 500 Error?
1. Check if access token is expired → Generate new one
2. Verify Organization URN format: `urn:li:organization:NUMBERS`
3. Run test script: `python test_linkedin.py`
4. Check `app.log` for detailed error

## 📚 More Help
- Full guide: `LINKEDIN_COMPANY_SETUP.md`
- Troubleshooting: `LINKEDIN_TROUBLESHOOTING.md`
