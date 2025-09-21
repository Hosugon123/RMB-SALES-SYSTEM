#!/usr/bin/env python3
"""
Simple GCS Test Script (English version for PowerShell compatibility)
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime

def main():
    print("=== GCS Local Test ===")
    print("Checking environment...")
    
    # Check for credentials
    gcs_credentials = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    gcs_bucket = os.getenv('GCS_BUCKET_NAME', 'dealsys')
    
    print(f"Credentials path: {gcs_credentials}")
    print(f"Bucket name: {gcs_bucket}")
    
    # Check for local credential file
    local_files = ['gcs-key.json', 'service-account-key.json']
    found_creds = None
    
    for file in local_files:
        if os.path.exists(file):
            print(f"Found local credential file: {file}")
            found_creds = file
            break
    
    if not gcs_credentials and not found_creds:
        print("ERROR: No GCS credentials found!")
        print("Please:")
        print("1. Set GOOGLE_APPLICATION_CREDENTIALS environment variable")
        print("2. Or place your service account key as 'gcs-key.json' in this directory")
        return False
    
    # Use found credentials
    creds_file = gcs_credentials or found_creds
    
    if not os.path.exists(creds_file):
        print(f"ERROR: Credential file does not exist: {creds_file}")
        return False
    
    print(f"Using credential file: {creds_file}")
    
    # Test JSON format
    try:
        with open(creds_file, 'r') as f:
            creds_data = json.load(f)
            print("JSON format: OK")
            print(f"Project ID: {creds_data.get('project_id', 'N/A')}")
    except Exception as e:
        print(f"ERROR: Invalid JSON format: {e}")
        return False
    
    # Test GCS connection
    try:
        print("Testing GCS connection...")
        from google.cloud import storage
        
        client = storage.Client.from_service_account_json(creds_file)
        bucket = client.bucket(gcs_bucket)
        
        if bucket.exists():
            print(f"SUCCESS: Bucket '{gcs_bucket}' exists and accessible")
            
            # List files
            blobs = list(bucket.list_blobs(max_results=5))
            print(f"Files in bucket: {len(blobs)}")
            
            # Test upload
            print("Testing file upload...")
            test_data = pd.DataFrame({
                'timestamp': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                'status': ['Local test success']
            })
            
            test_file = f"local_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            test_data.to_excel(test_file, index=False, engine='openpyxl')
            
            blob = bucket.blob(f"test/{test_file}")
            blob.upload_from_filename(test_file)
            
            print(f"SUCCESS: File uploaded to gs://{gcs_bucket}/test/{test_file}")
            
            # Cleanup
            os.remove(test_file)
            print("Local file cleaned up")
            
        else:
            print(f"ERROR: Bucket '{gcs_bucket}' not found or no access")
            return False
            
    except Exception as e:
        print(f"ERROR: GCS test failed: {e}")
        return False
    
    print("=== ALL TESTS PASSED ===")
    print("Your GCS setup is working correctly!")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\nNext steps:")
        print("1. Get your Google Cloud Service Account JSON key")
        print("2. Place it as 'gcs-key.json' in this directory")
        print("3. Make sure the service account has Storage Admin role")
        print("4. Create a GCS bucket named 'dealsys'")
        sys.exit(1)
    else:
        print("\nReady for Render deployment!")
        sys.exit(0)
