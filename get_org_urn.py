"""
Quick script to get your LinkedIn Organization URN
"""
import requests

def get_organization_urn():
    print("=" * 60)
    print("LinkedIn Organization URN Finder")
    print("=" * 60)
    
    access_token = input("\nEnter your LinkedIn Access Token: ").strip()
    
    if not access_token:
        print("Error: Access token required!")
        return
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'X-Restli-Protocol-Version': '2.0.0',
        'LinkedIn-Version': '202405'
    }
    
    print("\nFetching your organizations...")
    
    try:
        # Get organizations
        response = requests.get(
            'https://api.linkedin.com/v2/organizationalEntityAcls?q=roleAssignee',
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}\n")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'elements' in data and len(data['elements']) > 0:
                print("[SUCCESS] Found your organizations:\n")
                
                for i, element in enumerate(data['elements'], 1):
                    org_urn = element.get('organizationalTarget', 'N/A')
                    role = element.get('role', 'N/A')
                    state = element.get('state', 'N/A')
                    
                    print(f"{i}. Organization URN: {org_urn}")
                    print(f"   Role: {role}")
                    print(f"   State: {state}")
                    print()
                
                print("=" * 60)
                print("COPY THIS TO YOUR SETTINGS:")
                print("=" * 60)
                
                # Show the first admin org
                for element in data['elements']:
                    org_urn = element.get('organizationalTarget')
                    role = element.get('role')
                    if org_urn and 'ADMINISTRATOR' in str(role):
                        print(f"\nOrganization URN: {org_urn}")
                        print("\n[NEXT STEPS]")
                        print("1. Go to Settings -> LinkedIn Configuration")
                        print("2. Paste this in the 'Organization URN' field")
                        print("3. Save settings and try posting again!")
                        break
            else:
                print("[ERROR] No organizations found.")
                print("\nPossible reasons:")
                print("1. You don't have admin access to any LinkedIn company pages")
                print("2. Your access token doesn't have 'w_organization_social' scope")
                print("\nTo post as a company:")
                print("- You must be an admin of a LinkedIn company page")
                print("- Generate a new token with 'w_organization_social' scope")
        else:
            print(f"[ERROR] {response.text}")
            print("\nMake sure your access token has these scopes:")
            print("- r_liteprofile")
            print("- w_member_social")
            print("- w_organization_social")
            
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    get_organization_urn()
