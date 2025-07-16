from pychnl.streamurl import StreamURL

def test_stream_url():
    print("Testing PyChnl StreamURL...")
    
    with StreamURL(headless=True) as stream_client:
        # Get stream info for spark channel
        stream_info = stream_client.get_stream_url("spark")
        
        if stream_info:
            # Only get and display the M3U8 URL
            if "m3u8_url" in stream_info and stream_info["m3u8_url"]:
                print(f"Spark M3U8 URL: {stream_info['m3u8_url']}")
            else:
                print("No M3U8 URL available for spark")
        else:
            print("Failed to get stream info for spark")

if __name__ == "__main__":
    test_stream_url()