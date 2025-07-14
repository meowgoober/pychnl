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
            print(f"Stream info for spark:")
            for key, value in stream_info.items():
                print(f"  {key}: {value}")

if __name__ == "__main__":
    test_stream_url()