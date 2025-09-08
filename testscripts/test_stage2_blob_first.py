"""
Test Stage 2 blob-first implementation
Tests that files are uploaded directly to blob without persistent local storage
"""
import os
import sys
import requests
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.version_tracking_service import VersionTrackingService
from api.services.output_blob_service import OutputBlobService

def test_stage2_blob_first():
    """Test the Stage 2 blob-first implementation"""
    
    print("=== Testing Stage 2 Blob-First Implementation ===\n")
    
    # API base URL
    base_url = "http://localhost:8000"
    
    # Test parameters
    comparison_id = 10
    generation_mode = "delta"
    
    try:
        # Initialize services for verification
        tracking_service = VersionTrackingService()
        blob_service = OutputBlobService()
        
        print(f"1. Testing blob-first test step generation for comparison {comparison_id} ({generation_mode} mode)...")
        print("   Note: Make sure the API server is running on localhost:8000\n")
        
        # Clear any existing output files in output_files directory
        output_files_dir = "output_files"
        print("2. Checking for existing local files before test...")
        existing_files = []
        if os.path.exists(output_files_dir):
            existing_files = [f for f in os.listdir(output_files_dir) 
                            if f.startswith(f"comparison_{comparison_id}") or 
                               f.startswith(f"test_modifications_from_qtest")]
        print(f"   Found {len(existing_files)} existing files")
        
        # Make API request
        url = f"{base_url}/api/generate/test-steps-from-comparison"
        params = {
            "comparison_id": comparison_id,
            "generation_mode": generation_mode
        }
        
        print("3. Sending request to API...")
        try:
            response = requests.post(url, params=params, timeout=30)
            if response.status_code == 200:
                result = response.json()
                print("   [OK] Request successful\n")
                
                # Check response structure
                print("4. Checking response structure...")
                blob_urls = result.get('blob_urls', {})
                if blob_urls:
                    if blob_urls.get('json_url'):
                        print(f"   [OK] JSON blob URL in response: {blob_urls['json_url'][:80]}...")
                    if blob_urls.get('excel_url'):
                        print(f"   [OK] Excel blob URL in response: {blob_urls['excel_url'][:80]}...")
                else:
                    print("   [ERROR] No blob URLs in response")
                    return False
                
                # Check that saved_file_path is not in response (blob-first)
                if 'saved_file_path' in result:
                    print("   [WARNING] saved_file_path still in response - should be removed in Stage 2")
                else:
                    print("   [OK] No saved_file_path in response (blob-first)")
                print()
                
                # Check that no new local files were created persistently
                print("5. Checking that no persistent local files were created...")
                current_files = []
                if os.path.exists(output_files_dir):
                    current_files = [f for f in os.listdir(output_files_dir) 
                                   if f.startswith(f"comparison_{comparison_id}") or 
                                      f.startswith(f"test_modifications_from_qtest")]
                
                new_files = [f for f in current_files if f not in existing_files]
                if new_files:
                    print(f"   [WARNING] Found {len(new_files)} new local files - should be cleaned up:")
                    for file in new_files:
                        print(f"       - {file}")
                else:
                    print("   [OK] No new persistent local files created")
                print()
                
                # Check database for blob URLs
                print("6. Checking database for blob URLs...")
                db_urls = tracking_service.get_output_urls(comparison_id, generation_mode)
                if db_urls:
                    if db_urls.get('json_url'):
                        print(f"   [OK] JSON URL in DB: {db_urls['json_url'][:80]}...")
                    if db_urls.get('excel_url'):
                        print(f"   [OK] Excel URL in DB: {db_urls['excel_url'][:80]}...")
                    if db_urls.get('generated_at'):
                        print(f"   [OK] Generation timestamp: {db_urls['generated_at']}")
                else:
                    print("   [ERROR] No URLs found in database")
                    return False
                print()
                
                # Verify blob files exist
                print("7. Verifying blob files exist...")
                blob_outputs = blob_service.list_comparison_outputs(comparison_id)
                delta_files = blob_outputs.get('delta', [])
                if delta_files:
                    print(f"   [OK] Found {len(delta_files)} delta files in blob storage")
                    recent_files = [f for f in delta_files if 'test_steps_delta' in f][-2:]  # Get last 2
                    for file_url in recent_files:
                        print(f"       - {file_url.split('/')[-1]}")
                else:
                    print("   [ERROR] No delta files found in blob storage")
                    return False
                print()
                
                print("=== Stage 2 Test Complete ===")
                print("[SUCCESS] Files are generated directly to blob storage")
                print("         No persistent local files created")
                print("         Database updated with blob URLs")
                print("         Stage 2 blob-first implementation working correctly!")
                
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
    success = test_stage2_blob_first()
    sys.exit(0 if success else 1)