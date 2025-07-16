from pychnl.streamurl import StreamURL

def test_stream_url():
    print("Testing PyChnl StreamURL...")
    
    with StreamURL(headless=True) as stream_client:
        # Get available channels
        channels = stream_client.get_available_channels()
        print(f"Available channels: {channels}")
        
        # Test with spark channel
        stream_info = stream_client.get_stream_url("spark")
        if stream_info:
            print(f"\nAll URLs for spark:")
            print("=" * 40)
            
            # Display each URL type in a simple format
            if "blob_url" in stream_info and stream_info["blob_url"]:
                print(f"Blob URL: {stream_info['blob_url']}")
            
            if "m3u8_url" in stream_info and stream_info["m3u8_url"]:
                print(f"M3U8 URL: {stream_info['m3u8_url']}")
            
            if "mp4_url" in stream_info and stream_info["mp4_url"]:
                print(f"MP4 URL: {stream_info['mp4_url']}")
            
            if "poster_url" in stream_info and stream_info["poster_url"]:
                print(f"Poster URL: {stream_info['poster_url']}")
                
        else:
            print("Failed to get stream info for spark")

if __name__ == "__main__":
    test_stream_url()