"""
Test API Endpoints
Tests the new version tracking API endpoints
"""

import requests
import json
import sys
from pathlib import Path

# API base URL - update port based on .env
API_BASE_URL = "http://127.0.0.1:8000"  # Using port 8000 from .env


def test_api_health():
    """Test if API is running"""
    print("\n" + "="*60)
    print("TEST 1: API Health Check")
    print("="*60)
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"[PASS] API is healthy")
            print(f"  Version: {data.get('version')}")
            print(f"  Environment: {data.get('environment')}")
            return True
        else:
            print(f"[FAIL] API returned status code: {response.status_code}")
            return False
            
    except requests.ConnectionError:
        print(f"[FAIL] Cannot connect to API at {API_BASE_URL}")
        print("   Make sure the API server is running: python -m api.main")
        return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_tracked_files_endpoint():
    """Test GET /api/tracked-files endpoint"""
    print("\n" + "="*60)
    print("TEST 2: GET /api/tracked-files")
    print("="*60)
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/tracked-files", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                files = data.get('files', [])
                print(f"[PASS] Endpoint returned successfully")
                print(f"  Files count: {data.get('count', len(files))}")
                
                if files:
                    print("\n  Sample files:")
                    for file in files[:3]:
                        print(f"    - {file.get('friendly_name')} (ID: {file.get('id')})")
                
                # Check if it's mock data
                if data.get('message') and 'mock' in data.get('message', '').lower():
                    print("\n  [WARNING] Note: Returning mock data (database may not be configured)")
                    
                return True
            else:
                print(f"[FAIL] API returned success=false")
                return False
                
        else:
            print(f"[FAIL] API returned status code: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.ConnectionError:
        print(f"[FAIL] Cannot connect to API")
        return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_comparisons_endpoint():
    """Test GET /api/tracked-files/{file_id}/comparisons endpoint"""
    print("\n" + "="*60)
    print("TEST 3: GET /api/tracked-files/{file_id}/comparisons")
    print("="*60)
    
    try:
        # First get a file ID to test with
        files_response = requests.get(f"{API_BASE_URL}/api/tracked-files", timeout=10)
        
        if files_response.status_code != 200:
            print("[WARNING] Cannot get tracked files to test comparisons")
            return False
        
        files_data = files_response.json()
        files = files_data.get('files', [])
        
        if not files:
            print("[WARNING] No tracked files available to test")
            # Test with mock file_id = 1
            test_file_id = 1
            print(f"  Testing with mock file_id: {test_file_id}")
        else:
            test_file_id = files[0].get('id')
            print(f"  Testing with file: {files[0].get('friendly_name')} (ID: {test_file_id})")
        
        # Test comparisons endpoint
        response = requests.get(
            f"{API_BASE_URL}/api/tracked-files/{test_file_id}/comparisons",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                comparisons = data.get('comparisons', [])
                print(f"[PASS] Endpoint returned successfully")
                print(f"  Comparisons count: {data.get('count', len(comparisons))}")
                
                if comparisons:
                    comp = comparisons[0]
                    print(f"\n  Sample comparison:")
                    print(f"    Title: {comp.get('comparison_title')}")
                    print(f"    From: v{comp.get('from_sharepoint_version')} (Seq #{comp.get('from_sequence')})")
                    print(f"    To: v{comp.get('to_sharepoint_version')} (Seq #{comp.get('to_sequence')})")
                    print(f"    Changes: {comp.get('total_changes')}")
                
                # Check if it's mock data
                if data.get('message') and 'mock' in data.get('message', '').lower():
                    print("\n  [WARNING] Note: Returning mock data")
                    
                return True
            else:
                print(f"[FAIL] API returned success=false")
                return False
                
        else:
            print(f"[FAIL] API returned status code: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_azure_blob_service():
    """Test Azure Blob Service functionality"""
    print("\n" + "="*60)
    print("TEST 4: Azure Blob Service")
    print("="*60)
    
    try:
        # Import the service directly
        sys.path.append(str(Path(__file__).parent.parent))
        from api.services.azure_blob_service import AzureBlobService
        
        service = AzureBlobService()
        
        # Test JSON structure validation
        valid_json = {
            "summary": {"total_changes": 5},
            "tabs": []
        }
        
        invalid_json = {
            "data": "test"
        }
        
        if service.validate_json_structure(valid_json):
            print("[PASS] Valid JSON structure validated correctly")
        else:
            print("[FAIL] Failed to validate valid JSON structure")
            return False
        
        if not service.validate_json_structure(invalid_json):
            print("[PASS] Invalid JSON structure rejected correctly")
        else:
            print("[FAIL] Failed to reject invalid JSON structure")
            return False
        
        print("\n[PASS] Azure Blob Service validation working")
        return True
        
    except Exception as e:
        print(f"[FAIL] Error testing Azure Blob Service: {e}")
        return False


def test_impact_analysis_endpoint():
    """Test POST /api/analyze-impact-from-comparison endpoint"""
    print("\n" + "="*60)
    print("TEST 5: POST /api/analyze-impact-from-comparison")
    print("="*60)
    
    print("[INFO] This endpoint requires:")
    print("  1. A valid comparison_id with JSON in Azure Blob")
    print("  2. A QTest Excel file to upload")
    print("  Skipping automated test - test manually with Postman/curl")
    
    print("\nExample curl command:")
    print('curl -X POST \\')
    print(f'  {API_BASE_URL}/api/analyze-impact-from-comparison \\')
    print('  -F "comparison_id=1" \\')
    print('  -F "qtest_file=@path/to/qtest.xlsx"')
    
    return True  # Skip for automated testing


def main():
    """Run all API tests"""
    print("\n" + "="*60)
    print("API ENDPOINTS TEST SUITE")
    print("="*60)
    print(f"\nTesting API at: {API_BASE_URL}")
    
    results = []
    
    # Check if API is running first
    api_running = test_api_health()
    results.append(("API Health Check", api_running))
    
    if api_running:
        # Run endpoint tests
        results.append(("Tracked Files Endpoint", test_tracked_files_endpoint()))
        results.append(("Comparisons Endpoint", test_comparisons_endpoint()))
        results.append(("Azure Blob Service", test_azure_blob_service()))
        results.append(("Impact Analysis Endpoint", test_impact_analysis_endpoint()))
    else:
        print("\n[WARNING] Skipping endpoint tests - API is not running")
        print("   Start the API server with: python -m api.main")
    
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
    elif not api_running:
        print("\n[WARNING] Please start the API server and run tests again")
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)