#!/usr/bin/env python
"""
Script to demonstrate the Uniware API error for support team
Run this and record the screen to show the error clearly
"""

import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

def main():
    print("🎥 RECORDING API ERROR FOR SUPPORT TEAM")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    username = os.getenv("UNIWARE_USERNAME")
    password = os.getenv("UNIWARE_PASSWORD")
    
    print(f"🔐 Step 1: Authentication")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")
    
    # Step 1: Get Access Token
    print("\n📡 Making authentication request...")
    tenant = 'priyankdesigns'
    auth_url = f"https://{tenant}.unicommerce.com/oauth/token"
    auth_params = {
        'grant_type': 'password',
        'client_id': 'my-trusted-client',
        'username': username,
        'password': password
    }
    
    try:
        auth_response = requests.get(auth_url, params=auth_params)
        print(f"✅ Authentication Status: {auth_response.status_code}")
        
        if auth_response.status_code == 200:
            token = auth_response.json()['access_token']
            print(f"✅ Token received: {token[:20]}...")
        else:
            print(f"❌ Authentication failed: {auth_response.text}")
            return
            
    except Exception as e:
        print(f"❌ Authentication error: {str(e)}")
        return
    
    # Step 2: Create Export Job
    print("\n📋 Step 2: Creating Export Job")
    print("📡 Making export job request...")
    
    export_url = f"https://{tenant}.unicommerce.com/services/rest/v1/export/job/create"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'bearer {token}',
        'facility': 'priyankdesigns'
    }
    
    # Calculate date range
    yesterday = datetime.now() - timedelta(days=1)
    month_start = yesterday.replace(day=1)
    start_date = month_start.strftime('%Y-%m-%d')
    end_date = yesterday.strftime('%Y-%m-%d')
    
    payload = {
        "exportJobTypeName": "Sale Orders",
        "exportColums": [
            "saleOrderCode", "totalPrice", "created", "channel", "status", 
            "subtotal", "tax", "discount", "currency"
        ],
        "frequency": "ONETIME",
        "exportFilters": [
            {
                "id": 1,
                "dateRange": {
                    "start": start_date,
                    "end": end_date
                }
            }
        ]
    }
    
    print(f"📅 Date Range: {start_date} to {end_date}")
    print(f"📤 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        export_response = requests.post(export_url, headers=headers, data=json.dumps(payload))
        print(f"\n📊 RESPONSE DETAILS:")
        print(f"Status Code: {export_response.status_code}")
        print(f"Response Headers: {dict(export_response.headers)}")
        print(f"Response Body: {export_response.text}")
        
        if export_response.status_code == 500:
            print("\n❌ ERROR CONFIRMED:")
            print("✅ This is the 500 Internal Server Error we're reporting")
            print("✅ The error occurs consistently with this payload")
            print("✅ Manual exports work, but API calls fail")
            
    except Exception as e:
        print(f"❌ Request error: {str(e)}")
    
    print("\n🎬 RECORDING COMPLETE")
    print("Please send this recording to support team")

if __name__ == "__main__":
    main() 