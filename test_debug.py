#!/usr/bin/env python3
import os
import sys

print("=== Debug Test ===")
print("Current directory:", os.getcwd())
print("Python version:", sys.version)

# Check if GCS credentials exist
gcs_files = ['gcs-key.json', 'service-account-key.json']
print("\nLooking for credential files...")
for file in gcs_files:
    if os.path.exists(file):
        print(f"FOUND: {file}")
    else:
        print(f"NOT FOUND: {file}")

# Check environment variables
print("\nEnvironment variables:")
print("GOOGLE_APPLICATION_CREDENTIALS:", os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
print("GCS_BUCKET_NAME:", os.getenv('GCS_BUCKET_NAME'))

# Write to file for verification
with open('debug_output.txt', 'w') as f:
    f.write("Debug test completed successfully\n")
    f.write(f"Current directory: {os.getcwd()}\n")
    f.write(f"Python version: {sys.version}\n")

print("Debug output written to debug_output.txt")
print("=== Debug Test Complete ===")
