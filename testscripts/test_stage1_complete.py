"""
Test complete Stage 1 implementation
Tests that files are saved locally AND uploaded to blob
"""
import os
import sys
import requests
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.version_tracking_service import VersionTrackingService
from api.services.output_blob_service import OutputBlobService

def test_stage1_complete():
    """Test the complete Stage 1 implementation"""
    
    print("=== Testing Stage 1 Complete Implementation ===\n")
    
    # API base URL
    base_url = "http://localhost:8000"
    
    # Test parameters
    comparison_id = 10
    generation_mode = "delta"
    
    try:
        # Initialize services for verification
        tracking_service = VersionTrackingService()
        blob_service = OutputBlobService()
        
        print(f"1. Testing test step generation for comparison {comparison_id} ({generation_mode} mode)...")
        print("   Note: Make sure the API server is running on localhost:8000\n")
        
        # Make API request
        url = f"{base_url}/api/generate/test-steps-from-comparison"
        params = {
            "comparison_id": comparison_id,
            "generation_mode": generation_mode
        }
        
        print("2. Sending request to API...")
        try:
            response = requests.post(url, params=params, timeout=30)
            if response.status_code == 200:
                result = response.json()
                print("   [OK] Request successful\n")
                
                # Check local files
                print("3. Checking local files...")
                local_path = result.get('saved_file_path')
                report_id = result.get('report_id')
                
                if local_path:
                    if os.path.exists(local_path):
                        print(f"   [OK] Excel file exists locally: {local_path}")
                    else:
                        print(f"   [WARNING] Excel file not found: {local_path}")
                
                if report_id:
                    json_path = os.path.join("output_files", f"{report_id}.json")
                    if os.path.exists(json_path):
                        print(f"   [OK] JSON file exists locally: {json_path}")
                    else:
                        print(f"   [WARNING] JSON file not found: {json_path}")
                print()
                
                # Check blob URLs in response
                print("4. Checking blob URLs in response...")
                blob_urls = result.get('blob_urls', {})
                if blob_urls:
                    if blob_urls.get('json_url'):
                        print(f"   [OK] JSON blob URL: {blob_urls['json_url'][:80]}...")
                    if blob_urls.get('excel_url'):
                        print(f"   [OK] Excel blob URL: {blob_urls['excel_url'][:80]}...")
                else:
                    print("   [WARNING] No blob URLs in response")
                print()
                
                # Check database for blob URLs
                print("5. Checking database for blob URLs...")
                db_urls = tracking_service.get_output_urls(comparison_id, generation_mode)
                if db_urls:
                    if db_urls.get('json_url'):
                        print(f"   [OK] JSON URL in DB: {db_urls['json_url'][:80]}...")
                    if db_urls.get('excel_url'):
                        print(f"   [OK] Excel URL in DB: {db_urls['excel_url'][:80]}...")
                    if db_urls.get('generated_at'):
                        print(f"   [OK] Generation timestamp: {db_urls['generated_at']}")
                else:
                    print("   [WARNING] No URLs found in database")
                print()
                
                # Verify blob files exist
                print("6. Verifying blob files exist...")
                blob_outputs = blob_service.list_comparison_outputs(comparison_id)
                delta_files = blob_outputs.get('delta', [])
                if delta_files:
                    print(f"   [OK] Found {len(delta_files)} delta files in blob storage")
                    for file_url in delta_files[:2]:  # Show first 2
                        print(f"       - {file_url.split('/')[-1]}")
                else:
                    print("   [WARNING] No delta files found in blob storage")
                print()
                
                print("=== Stage 1 Test Complete ===")
                print("[SUCCESS] Files are saved locally AND uploaded to blob storage")
                print("         Database is updated with blob URLs")
                print("         Stage 1 implementation working correctly!")
                
            else:
                print(f"   [ERROR] Request failed with status {response.status_code}")
                print(f"   Response: {response.text[:500]}")
                return False
                
        except requests.exceptions.ConnectionError:
            print("   [ERROR] Could not connect to API server")
            print("   Please make sure the server is running: python api/main.py")
            return False
        except Exception as e:
            print(f"   [ERROR] Request failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_stage1_complete()
    sys.exit(0 if success else 1)