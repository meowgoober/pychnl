#!/usr/bin/env python3
"""
Test script for PyChnl ViewerCounts functionality
"""

from pychnl.viewercounts import ViewerCounts

def test_viewer_counts():
    print("Testing PyChnl ViewerCounts...")
    print("=" * 50)
    
    # Initialize the viewer counts client
    viewer_client = ViewerCounts()
    
    try:
        # Test 1: Get all channels
        print("1. Testing get_all_channels()...")
        all_channels = viewer_client.get_all_channels()
        print(f"   ✓ Found {len(all_channels)} channels")
        
        # Test 2: Get online channels
        print("\n2. Testing get_online_channels()...")
        online_channels = viewer_client.get_online_channels()
        print(f"   ✓ Found {len(online_channels)} online channels")
        
        # Test 3: Get offline channels
        print("\n3. Testing get_offline_channels()...")
        offline_channels = viewer_client.get_offline_channels()
        print(f"   ✓ Found {len(offline_channels)} offline channels")
        
        # Test 4: Get total viewers
        print("\n4. Testing get_total_viewers()...")
        total_viewers = viewer_client.get_total_viewers()
        print(f"   ✓ Total viewers across all online channels: {total_viewers}")
        
        # Test 5: Test channel lookup by slug
        print("\n5. Testing get_channel_by_slug()...")
        if all_channels:
            test_slug = all_channels[0].slug
            found_channel = viewer_client.get_channel_by_slug(test_slug)
            if found_channel:
                print(f"   ✓ Found channel '{found_channel.name}' with slug '{test_slug}'")
            else:
                print(f"   ✗ Could not find channel with slug '{test_slug}'")
        
        # Test 6: Print full summary
        print("\n6. Full viewer summary:")
        print("-" * 50)
        viewer_client.print_viewer_summary()
        
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
        
    except Exception as e:
        print(f"   ✗ Error during testing: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_viewer_counts()
    if not success:
        exit(1)