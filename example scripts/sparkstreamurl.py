#!/usr/bin/env python3
"""
Simple script to get Spark M3U8 URL using pychnl library
"""
from pychnl import ViewerCounts, StreamURL

def get_spark_m3u8():
    """
    Get the Spark M3U8 URL and print it out
    """
    # First, check if Spark is online
    viewer_client = ViewerCounts()
    
    print("Checking if Spark is online...")
    spark_channel = viewer_client.get_channel_by_slug("spark")
    
    if spark_channel:
        if spark_channel.is_online:
            print(f"✓ Spark is online with {spark_channel.viewers} viewers")
        else:
            print("✗ Spark is currently offline")
            return None
    else:
        print("✗ Spark channel not found")
        return None
    
    # Get the stream URL from M3U playlist
    print("\nFetching Spark M3U8 URL...")
    
    stream_client = StreamURL()
    
    # Try to find spark channel in M3U playlist
    spark_stream = stream_client.get_channel_by_name("spark")
    
    if spark_stream:
        m3u8_url = spark_stream.stream_url
        print(f"✓ Successfully retrieved M3U8 URL:")
        print(f"   {m3u8_url}")
        return m3u8_url
    else:
        print("✗ Spark channel not found in M3U playlist")
        return None

def main():
    """
    Main function
    """
    try:
        print("=== Spark M3U8 URL Fetcher ===")
        m3u8_url = get_spark_m3u8()
        
        if m3u8_url:
            print(f"\n🎉 Spark M3U8 URL: {m3u8_url}")
        else:
            print("\n❌ Could not retrieve Spark M3U8 URL")
            
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()