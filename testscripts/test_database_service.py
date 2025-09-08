"""
Test Database Service
Tests the connection and functionality of the VersionTrackingService
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from api.services.version_tracking_service import VersionTrackingService


def test_database_connection():
    """Test database connection"""
    print("\n" + "="*60)
    print("TEST 1: Database Connection")
    print("="*60)
    
    try:
        service = VersionTrackingService()
        
        if not service.connection_string:
            print("[FAIL] No connection string found in environment")
            return False
            
        print("+ Connection string loaded from environment")
        
        # Test connection
        connected = service.test_connection()
        
        if connected:
            print("[PASS] Successfully connected to Azure SQL Database")
            return True
        else:
            print("[FAIL] Failed to connect to database")
            return False
            
    except Exception as e:
        print(f"[FAIL] Connection test failed with error: {e}")
        return False


def test_get_tracked_files():
    """Test fetching tracked files"""
    print("\n" + "="*60)
    print("TEST 2: Fetch Tracked Files")
    print("="*60)
    
    try:
        service = VersionTrackingService()
        
        if not service.connection_string:
            print("[SKIP] Skipping - No database connection")
            return False
        
        files = service.get_tracked_files()
        
        print(f"+ Retrieved {len(files)} tracked files")
        
        if files:
            print("\nSample tracked files:")
            for i, file in enumerate(files[:3], 1):  # Show first 3
                print(f"\n  File {i}:")
                print(f"    ID: {file.get('id')}")
                print(f"    Name: {file.get('file_name')}")
                print(f"    Friendly Name: {file.get('friendly_name')}")
                print(f"    Created: {file.get('created_at')}")
                
        print(f"\n[PASS] Successfully fetched tracked files")
        return True
        
    except Exception as e:
        print(f"[FAIL] Failed to fetch tracked files: {e}")
        return False


def test_get_file_comparisons():
    """Test fetching comparisons for a file"""
    print("\n" + "="*60)
    print("TEST 3: Fetch File Comparisons")
    print("="*60)
    
    try:
        service = VersionTrackingService()
        
        if not service.connection_string:
            print("[SKIP] Skipping - No database connection")
            return False
        
        # First get tracked files to find a valid file_id
        files = service.get_tracked_files()
        
        if not files:
            print("[WARNING] No tracked files found to test comparisons")
            return False
        
        # Use the first file
        test_file = files[0]
        file_id = test_file.get('id')
        
        print(f"Testing with file: {test_file.get('friendly_name')} (ID: {file_id})")
        
        comparisons = service.get_file_comparisons(file_id)
        
        print(f"\n+ Retrieved {len(comparisons)} comparisons")
        
        if comparisons:
            print("\nSample comparison:")
            comp = comparisons[0]
            print(f"  Comparison ID: {comp.get('comparison_id')}")
            print(f"  Title: {comp.get('comparison_title')}")
            print(f"  From Version: {comp.get('from_sharepoint_version')} (Seq #{comp.get('from_sequence')})")
            print(f"  To Version: {comp.get('to_sharepoint_version')} (Seq #{comp.get('to_sequence')})")
            print(f"  Total Changes: {comp.get('total_changes')}")
            print(f"    - Added: {comp.get('added_mappings')}")
            print(f"    - Modified: {comp.get('modified_mappings')}")
            print(f"    - Deleted: {comp.get('deleted_mappings')}")
            print(f"  JSON URL: {comp.get('json_report_url')[:50]}..." if comp.get('json_report_url') else "  JSON URL: None")
            
        print(f"\n[PASS] Successfully fetched comparisons")
        return True
        
    except Exception as e:
        print(f"[FAIL] Failed to fetch comparisons: {e}")
        return False


def test_get_comparison_details():
    """Test fetching specific comparison details"""
    print("\n" + "="*60)
    print("TEST 4: Fetch Comparison Details")
    print("="*60)
    
    try:
        service = VersionTrackingService()
        
        if not service.connection_string:
            print("[SKIP] Skipping - No database connection")
            return False
        
        # Get a comparison to test with
        files = service.get_tracked_files()
        if not files:
            print("[WARNING] No tracked files found")
            return False
            
        file_id = files[0].get('id')
        comparisons = service.get_file_comparisons(file_id)
        
        if not comparisons:
            print("[WARNING] No comparisons found to test")
            return False
        
        # Test with first comparison
        comparison_id = comparisons[0].get('comparison_id')
        
        print(f"Testing with comparison ID: {comparison_id}")
        
        details = service.get_comparison_details(comparison_id)
        
        if details:
            print("\n+ Retrieved comparison details:")
            print(f"  ID: {details.get('id')}")
            print(f"  Title: {details.get('comparison_title')}")
            print(f"  Status: {details.get('comparison_status')}")
            print(f"  JSON URL exists: {'Yes' if details.get('json_report_url') else 'No'}")
            print(f"  HTML URL exists: {'Yes' if details.get('html_report_url') else 'No'}")
            print(f"  Total Changes: {details.get('total_changes')}")
            
            print(f"\n[PASS] Successfully fetched comparison details")
            return True
        else:
            print(f"[FAIL] No details found for comparison {comparison_id}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Failed to fetch comparison details: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("DATABASE SERVICE TEST SUITE")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Database Connection", test_database_connection()))
    results.append(("Get Tracked Files", test_get_tracked_files()))
    results.append(("Get File Comparisons", test_get_file_comparisons()))
    results.append(("Get Comparison Details", test_get_comparison_details()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{test_name:.<40} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n*** All tests passed successfully! ***")
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)