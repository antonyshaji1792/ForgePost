"""
LinkedIn API Test Script
This script helps you verify your LinkedIn credentials and API access.
"""

import requests
import json

def test_linkedin_credentials(access_token):
    """Test if the LinkedIn access token is valid"""
    print("=" * 60)
    print("Testing LinkedIn Access Token...")
    print("=" * 60)
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'X-Restli-Protocol-Version': '2.0.0',
        'LinkedIn-Version': '202405'
    }
    
    # Test 1: Get user profile
    print("\n[Test 1] Getting user profile...")
    try:
        response = requests.get('https://api.linkedin.com/v2/me', headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            person_id = data.get('id', 'N/A')
            print(f"✓ Success! Your Person ID: {person_id}")
            print(f"✓ Your Person URN should be: urn:li:person:{person_id}")
            return f"urn:li:person:{person_id}"
        else:
            print(f"✗ Failed: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def test_video_upload_registration(access_token, person_urn):
    """Test the video upload registration endpoint"""
    print("\n" + "=" * 60)
    print("Testing Video Upload Registration...")
    print("=" * 60)
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'X-Restli-Protocol-Version': '2.0.0',
        'LinkedIn-Version': '202405'
    }
    
    register_url = 'https://api.linkedin.com/v2/assets?action=registerUpload'
    register_data = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-video"],
            "owner": person_urn,
            "serviceRelationships": [
                {
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent"
                }
            ]
        }
    }
    
    print(f"\nRequest URL: {register_url}")
    print(f"Person URN: {person_urn}")
    print(f"\nRequest Data:")
    print(json.dumps(register_data, indent=2))
    
    try:
        response = requests.post(register_url, headers=headers, json=register_data)
        print(f"\nResponse Status Code: {response.status_code}")
        print(f"\nResponse Body:")
        print(json.dumps(response.json() if response.text else {}, indent=2))
        
        if response.status_code == 200:
            print("\n✓ Success! Video upload registration works!")
            return True
        else:
            print(f"\n✗ Failed! Error: {response.text}")
            return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

def get_organization_urns(access_token):
    """Get list of organizations the user can post as"""
    print("\n" + "=" * 60)
    print("Getting Organizations You Can Post As...")
    print("=" * 60)
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'X-Restli-Protocol-Version': '2.0.0',
        'LinkedIn-Version': '202405'
    }
    
    try:
        # Get organizations
        response = requests.get('https://api.linkedin.com/v2/organizationalEntityAcls?q=roleAssignee', headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            orgs = []
            
            if 'elements' in data:
                for element in data['elements']:
                    org_urn = element.get('organizationalTarget')
                    role = element.get('role')
                    if org_urn and 'ADMINISTRATOR' in str(role):
                        orgs.append(org_urn)
                        print(f"✓ Found organization: {org_urn}")
            
            if orgs:
                return orgs
            else:
                print("✗ No organizations found where you have admin access")
                return []
        else:
            print(f"✗ Failed: {response.text}")
            return []
    except Exception as e:
        print(f"✗ Error: {e}")
        return []

def main():
    print("\n" + "=" * 60)
    print("LinkedIn API Credential Tester")
    print("=" * 60)
    
    # Get credentials from user
    print("\nPlease enter your LinkedIn credentials:")
    access_token = input("Access Token: ").strip()
    
    if not access_token:
        print("Error: Access token is required!")
        return
    
    # Test 1: Verify access token and get person URN
    person_urn = test_linkedin_credentials(access_token)
    
    if not person_urn:
        print("\n" + "=" * 60)
        print("RESULT: Access token is invalid or expired!")
        print("=" * 60)
        print("\nPlease generate a new access token from:")
        print("https://www.linkedin.com/developers/apps")
        return
    
    # Test 2: Get organizations
    org_urns = get_organization_urns(access_token)
    
    # Test 3: Choose which URN to test
    print("\n" + "=" * 60)
    print("Choose Posting Type")
    print("=" * 60)
    print("\n1. Post as Personal Profile")
    print(f"   URN: {person_urn}")
    
    if org_urns:
        print("\n2. Post as Organization/Company Page")
        for i, org in enumerate(org_urns):
            print(f"   {i+3}. {org}")
    
    choice = input("\nEnter choice (1 for personal, 2+ for organization): ").strip()
    
    author_urn = person_urn
    is_org = False
    
    if choice == "1":
        author_urn = person_urn
        is_org = False
    elif choice.isdigit() and int(choice) >= 2 and org_urns:
        idx = int(choice) - 3
        if 0 <= idx < len(org_urns):
            author_urn = org_urns[idx]
            is_org = True
        else:
            print("Invalid choice, using personal profile")
    
    # Allow custom URN
    custom_urn = input(f"\nPress Enter to use {author_urn}, or enter a custom URN: ").strip()
    if custom_urn:
        author_urn = custom_urn
        is_org = 'organization' in author_urn.lower()
    
    # Test video upload registration
    success = test_video_upload_registration(access_token, author_urn)
    
    # Final summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if success:
        print("✓ All tests passed!")
        print(f"\nYou can use these credentials in your app:")
        print(f"  Access Token: {access_token[:20]}...")
        if is_org:
            print(f"  Organization URN: {author_urn}")
            print(f"  Person URN: {person_urn} (keep this too)")
        else:
            print(f"  Person URN: {author_urn}")
    else:
        print("✗ Tests failed!")
        print("\nPossible issues:")
        print("1. Access token is invalid or expired")
        print("2. Access token doesn't have required scopes (w_member_social or w_organization_social)")
        print("3. URN is incorrect")
        print("4. LinkedIn app doesn't have video upload permissions")
        print("5. For organizations: You need admin access to the company page")
        print("\nPlease check the LINKEDIN_TROUBLESHOOTING.md file for more help.")

if __name__ == "__main__":
    main()
