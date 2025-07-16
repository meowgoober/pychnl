import requests
import re
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class StreamChannel:
    """Represents a webchnl stream channel with metadata"""
    tvg_id: str
    name: str
    logo: str
    stream_url: str


class StreamURL:
    """Handle stream URL operations for webchnl M3U playlist"""
    
    def __init__(self, base_url: str = "https://webchnl.live/api"):
        self.base_url = base_url
        self.m3u_endpoint = f"{base_url}/master.m3u"
    
    def get_stream_channels(self) -> Dict[str, StreamChannel]:
        """
        Fetch all channels with their stream URLs and metadata from M3U playlist
        
        Returns:
            Dict[str, StreamChannel]: Dictionary with channel names as keys and StreamChannel objects as values
            
        Raises:
            requests.RequestException: If API request fails
            ValueError: If M3U parsing fails
        """
        try:
            response = requests.get(self.m3u_endpoint)
            response.raise_for_status()
            
            m3u_content = response.text
            channels = self._parse_m3u(m3u_content)
            
            return channels
            
        except requests.RequestException as e:
            raise requests.RequestException(f"Failed to fetch M3U playlist: {e}")
    
    def _parse_m3u(self, m3u_content: str) -> Dict[str, StreamChannel]:
        """
        Parse M3U content and extract channel information
        
        Args:
            m3u_content (str): Raw M3U playlist content
            
        Returns:
            Dict[str, StreamChannel]: Dictionary of parsed channels
        """
        channels = {}
        lines = m3u_content.strip().split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for EXTINF lines
            if line.startswith('#EXTINF:'):
                # Extract metadata from EXTINF line
                extinf_match = re.search(
                    r'#EXTINF:-1 tvg-id="([^"]*)" tvg-name="([^"]*)" tvg-logo="([^"]*)",(.+)',
                    line
                )
                
                if extinf_match and i + 1 < len(lines):
                    tvg_id = extinf_match.group(1)
                    tvg_name = extinf_match.group(2)
                    tvg_logo = extinf_match.group(3)
                    display_name = extinf_match.group(4)
                    
                    # Next line should be the stream URL
                    stream_url = lines[i + 1].strip()
                    
                    if stream_url and not stream_url.startswith('#'):
                        channel = StreamChannel(
                            tvg_id=tvg_id,
                            name=tvg_name,
                            logo=tvg_logo,
                            stream_url=stream_url
                        )
                        channels[tvg_name] = channel
                        
                    i += 2  # Skip the stream URL line
                else:
                    i += 1
            else:
                i += 1
        
        return channels
    
    def get_channel_by_name(self, channel_name: str) -> Optional[StreamChannel]:
        """
        Get a specific channel by its name
        
        Args:
            channel_name (str): The channel name to search for
            
        Returns:
            Optional[StreamChannel]: StreamChannel object if found, None otherwise
        """
        channels = self.get_stream_channels()
        return channels.get(channel_name)
    
    def get_channel_by_id(self, tvg_id: str) -> Optional[StreamChannel]:
        """
        Get a specific channel by its TVG ID
        
        Args:
            tvg_id (str): The TVG ID to search for
            
        Returns:
            Optional[StreamChannel]: StreamChannel object if found, None otherwise
        """
        channels = self.get_stream_channels()
        for channel in channels.values():
            if channel.tvg_id == tvg_id:
                return channel
        return None
    
    def get_all_channel_names(self) -> list:
        """
        Get list of all available channel names
        
        Returns:
            list: List of channel names
        """
        channels = self.get_stream_channels()
        return list(channels.keys())
    
    def get_all_stream_urls(self) -> Dict[str, str]:
        """
        Get dictionary of all channel names and their stream URLs
        
        Returns:
            Dict[str, str]: Dictionary with channel names as keys and stream URLs as values
        """
        channels = self.get_stream_channels()
        return {name: channel.stream_url for name, channel in channels.items()}
    
    def get_all_logos(self) -> Dict[str, str]:
        """
        Get dictionary of all channel names and their logo URLs
        
        Returns:
            Dict[str, str]: Dictionary with channel names as keys and logo URLs as values
        """
        channels = self.get_stream_channels()
        return {name: channel.logo for name, channel in channels.items()}
    
    def print_channels_summary(self):
        """Print a formatted summary of all channels"""
        channels = self.get_stream_channels()
        
        print("WebChnl Stream Channels Summary")
        print("=" * 50)
        print(f"Total Channels: {len(channels)}")
        print("\nChannel Details:")
        print("-" * 50)
        
        for name, channel in channels.items():
            print(f"Name: {name}")
            print(f"  TVG ID: {channel.tvg_id}")
            print(f"  Logo: {channel.logo}")
            print(f"  Stream: {channel.stream_url}")
            print()


# Example usage
if __name__ == "__main__":
    # Initialize the stream URL client
    stream_client = StreamURL()
    
    try:
        # Get all channels
        all_channels = stream_client.get_stream_channels()
        print(f"Found {len(all_channels)} channels")
        
        # Get specific channel
        channel = stream_client.get_channel_by_name("2x2_English")
        if channel:
            print(f"2x2_English stream URL: {channel.stream_url}")
        
        # Get all stream URLs
        stream_urls = stream_client.get_all_stream_urls()
        print(f"Stream URLs: {len(stream_urls)}")
        
        # Print summary
        stream_client.print_channels_summary()
        
    except Exception as e:
        print(f"Error: {e}")