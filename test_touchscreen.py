#!/usr/bin/env python
"""
Simple test script to demonstrate the touchscreen interface.
Run this to test the code entry screen with the touchscreen buttons.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utilities.screen import run_code_screen, show_success_screen, show_error_screen

if __name__ == "__main__":
    print("Testing Touchscreen Code Entry Interface")
    print("=" * 50)
    print("The touchscreen interface will open in a new window.")
    print("Click on the number buttons to enter a code.")
    print("Use BackSpaceKey button to delete digits.")
    print("Use EnterKey button to submit.")
    print("=" * 50)
    
    # Test the code entry screen
    code = run_code_screen(email="customer@example.com")
    
    if code:
        print(f"\nCode entered: {code}")
        print("Showing success screen...")
        show_success_screen("Test successful!")
    else:
        print("\nNo code entered or window closed.")
