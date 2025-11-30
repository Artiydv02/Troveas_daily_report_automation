#!/usr/bin/env python
"""
Debug encoding issues
"""

import os
from dotenv import load_dotenv

def debug_encoding():
    load_dotenv()
    
    sender_email = os.getenv("EMAIL_ADDRESS")
    sender_password = os.getenv("EMAIL_PASSWORD")
    filename = "Troveas_Report_2025-08-06.xlsx"
    
    print("=== DEBUGGING ENCODING ISSUES ===")
    
    # Check email address
    print(f"Email address: '{sender_email}'")
    print(f"Email address bytes: {sender_email.encode('utf-8') if sender_email else 'None'}")
    print(f"Email address repr: {repr(sender_email) if sender_email else 'None'}")
    
    # Check password 
    if sender_password:
        print(f"Password length: {len(sender_password)}")
        print(f"Password repr (first 10 chars): {repr(sender_password[:10])}")
        
        # Check for problematic characters
        for i, char in enumerate(sender_password):
            if ord(char) > 127:
                print(f"Non-ASCII character at position {i}: {repr(char)} (ord: {ord(char)})")
    
    # Check filename
    print(f"Filename: '{filename}'")
    print(f"Filename bytes: {filename.encode('utf-8')}")
    print(f"Filename repr: {repr(filename)}")
    
    # Check current directory path
    current_dir = os.getcwd()
    print(f"Current directory: {current_dir}")
    print(f"Directory repr: {repr(current_dir)}")
    
    # Check if file exists and its properties
    if os.path.exists(filename):
        print(f"File exists: ✅")
        print(f"File size: {os.path.getsize(filename)} bytes")
        
        # Get absolute path
        abs_path = os.path.abspath(filename)
        print(f"Absolute path: {abs_path}")
        print(f"Absolute path repr: {repr(abs_path)}")
        
        # Check for non-ASCII characters in path
        for i, char in enumerate(abs_path):
            if ord(char) > 127:
                print(f"Non-ASCII character in path at position {i}: {repr(char)} (ord: {ord(char)})")
    else:
        print(f"File exists: ❌")

if __name__ == "__main__":
    debug_encoding()