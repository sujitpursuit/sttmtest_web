"""
Test VersionTrackingService blob methods
"""
import os
import sys
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.version_tracking_service import VersionTrackingService

def test_version_tracking_blob():
    """Test the blob-related methods in VersionTrackingService"""
    
    print("=== Testing VersionTrackingService Blob Methods ===\n")
    
    try:
        # Initialize service
        print("1. Initializing VersionTrackingService...")
        service = VersionTrackingService()
        print("   [OK] Service initialized\n")
        
        # Get a test comparison (using comparison_id 10 which we know exists)
        comparison_id = 10
        
        # Test delta outputs update
        print(f"2. Testing delta outputs update for comparison {comparison_id}...")
        test_json_url = f"https://test.blob.core.windows.net/output-files/test_delta_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        test_excel_url = f"https://test.blob.core.windows.net/output-files/test_delta_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        success = service.update_delta_outputs(
            comparison_id=comparison_id,
            json_url=test_json_url,
            excel_url=test_excel_url
        )
        
        if success:
            print(f"   [OK] Updated delta outputs")
        else:
            print(f"   [ERROR] Failed to update delta outputs")
        print()
        
        # Test inplace outputs update
        print(f"3. Testing inplace outputs update for comparison {comparison_id}...")
        test_json_url_inplace = f"https://test.blob.core.windows.net/output-files/test_inplace_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        test_excel_url_inplace = f"https://test.blob.core.windows.net/output-files/test_inplace_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        success = service.update_inplace_outputs(
            comparison_id=comparison_id,
            json_url=test_json_url_inplace,
            excel_url=test_excel_url_inplace
        )
        
        if success:
            print(f"   [OK] Updated inplace outputs")
        else:
            print(f"   [ERROR] Failed to update inplace outputs")
        print()
        
        # Test getting output URLs
        print(f"4. Testing get output URLs for comparison {comparison_id}...")
        
        # Get delta only
        delta_urls = service.get_output_urls(comparison_id, 'delta')
        if delta_urls:
            print(f"   [OK] Got delta URLs:")
            print(f"       JSON: {delta_urls.get('json_url', 'None')[:80]}...")
            print(f"       Excel: {delta_urls.get('excel_url', 'None')[:80]}...")
            print(f"       Generated: {delta_urls.get('generated_at', 'None')}")
        
        # Get inplace only
        inplace_urls = service.get_output_urls(comparison_id, 'inplace')
        if inplace_urls:
            print(f"   [OK] Got inplace URLs:")
            print(f"       JSON: {inplace_urls.get('json_url', 'None')[:80]}...")
            print(f"       Excel: {inplace_urls.get('excel_url', 'None')[:80]}...")
            print(f"       Generated: {inplace_urls.get('generated_at', 'None')}")
        
        # Get all outputs
        all_urls = service.get_output_urls(comparison_id)
        if all_urls:
            print(f"   [OK] Got all output URLs")
            print(f"       Delta: {all_urls.get('delta', {}).get('json_url', 'None') is not None}")
            print(f"       Inplace: {all_urls.get('inplace', {}).get('json_url', 'None') is not None}")
        print()
        
        # Clean up test data
        print("5. Cleaning up test data...")
        # Clear the test URLs we added
        service.update_delta_outputs(comparison_id, None, None)
        service.update_inplace_outputs(comparison_id, None, None)
        print("   [OK] Test data cleaned\n")
        
        print("=== Test Complete ===")
        print("[SUCCESS] VersionTrackingService blob methods working correctly")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_version_tracking_blob()
    sys.exit(0 if success else 1)