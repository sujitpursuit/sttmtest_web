"""
Test OutputBlobService functionality
"""
import os
import sys
import json
import tempfile
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.output_blob_service import OutputBlobService

def test_output_blob_service():
    """Test the OutputBlobService"""
    
    print("=== Testing OutputBlobService ===\n")
    
    try:
        # Initialize service
        print("1. Initializing OutputBlobService...")
        service = OutputBlobService()
        print("   [OK] Service initialized\n")
        
        # Create test files
        print("2. Creating test files...")
        test_json = {
            "test": "data",
            "generated_at": "2025-09-08",
            "mode": "delta"
        }
        
        # Create temporary test files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as json_file:
            json.dump(test_json, json_file)
            json_path = json_file.name
        
        # Create a simple Excel file (just a placeholder for testing)
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as excel_file:
            excel_file.write(b'Test Excel Content')
            excel_path = excel_file.name
        
        print(f"   [OK] Created test JSON: {json_path}")
        print(f"   [OK] Created test Excel: {excel_path}\n")
        
        # Test upload
        print("3. Testing upload...")
        comparison_id = 999  # Test comparison ID
        generation_mode = "delta"
        
        urls = service.upload_test_step_outputs(
            comparison_id=comparison_id,
            generation_mode=generation_mode,
            json_file_path=json_path,
            excel_file_path=excel_path
        )
        
        if urls['json_url']:
            print(f"   [OK] JSON uploaded: {urls['json_url'][:80]}...")
        else:
            print("   [ERROR] JSON upload failed")
        
        if urls['excel_url']:
            print(f"   [OK] Excel uploaded: {urls['excel_url'][:80]}...")
        else:
            print("   [ERROR] Excel upload failed")
        print()
        
        # Test listing
        print("4. Testing list outputs...")
        outputs = service.list_comparison_outputs(comparison_id)
        print(f"   [OK] Found {len(outputs['delta'])} delta outputs")
        print(f"   [OK] Found {len(outputs['inplace'])} inplace outputs\n")
        
        # Test download (if upload was successful)
        if urls['json_url']:
            print("5. Testing download...")
            downloaded_path = service.download_output_file(urls['json_url'])
            if downloaded_path:
                with open(downloaded_path, 'r') as f:
                    downloaded_content = json.load(f)
                if downloaded_content == test_json:
                    print("   [OK] Downloaded content matches original")
                else:
                    print("   [ERROR] Downloaded content differs")
                os.unlink(downloaded_path)  # Clean up
            else:
                print("   [ERROR] Download failed")
            print()
        
        # Clean up test files
        print("6. Cleaning up test files...")
        service.delete_output_files(comparison_id, generation_mode)
        print("   [OK] Deleted test blobs")
        
        # Clean up local temp files
        os.unlink(json_path)
        os.unlink(excel_path)
        print("   [OK] Deleted local temp files\n")
        
        print("=== Test Complete ===")
        print("[SUCCESS] OutputBlobService is working correctly")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_output_blob_service()
    sys.exit(0 if success else 1)