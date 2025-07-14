import requests
import json
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class Channel:
    """Represents a webchnl channel with viewer information"""
    name: str
    slug: str
    viewers: int
    
    @property
    def is_online(self) -> bool:
        """Returns True if channel is online (viewers >= 0)"""
        return self.viewers >= 0
    
    @property
    def is_offline(self) -> bool:
        """Returns True if channel is offline (viewers == -1)"""
        return self.viewers == -1


class ViewerCounts:
    """Handle viewer count operations for webchnl API"""
    
    def __init__(self, base_url: str = "https://webchnl.live/api"):
        self.base_url = base_url
        self.viewer_counts_endpoint = f"{base_url}/viewerCounts"
    
    def get_all_channels(self) -> List[Channel]:
        """
        Fetch all channels with their viewer counts
        
        Returns:
            List[Channel]: List of Channel objects with viewer data
            
        Raises:
            requests.RequestException: If API request fails
            json.JSONDecodeError: If response is not valid JSON
        """
        try:
            response = requests.get(self.viewer_counts_endpoint)
            response.raise_for_status()
            
            data = response.json()
            channels = [Channel(name=ch["name"], slug=ch["slug"], viewers=ch["viewers"]) 
                       for ch in data]
            
            return channels
            
        except requests.RequestException as e:
            raise requests.RequestException(f"Failed to fetch viewer counts: {e}")
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON response: {e}")
    
    def get_channel_by_slug(self, slug: str) -> Optional[Channel]:
        """
        Get a specific channel by its slug
        
        Args:
            slug (str): The channel slug to search for
            
        Returns:
            Optional[Channel]: Channel object if found, None otherwise
        """
        channels = self.get_all_channels()
        for channel in channels:
            if channel.slug == slug:
                return channel
        return None
    
    def get_online_channels(self) -> List[Channel]:
        """
        Get only channels that are currently online
        
        Returns:
            List[Channel]: List of online channels
        """
        channels = self.get_all_channels()
        return [ch for ch in channels if ch.is_online]
    
    def get_offline_channels(self) -> List[Channel]:
        """
        Get only channels that are currently offline
        
        Returns:
            List[Channel]: List of offline channels
        """
        channels = self.get_all_channels()
        return [ch for ch in channels if ch.is_offline]
    
    def get_total_viewers(self) -> int:
        """
        Get total viewer count across all online channels
        
        Returns:
            int: Total number of viewers
        """
        online_channels = self.get_online_channels()
        return sum(ch.viewers for ch in online_channels)
    
    def print_viewer_summary(self):
        """Print a formatted summary of all channels and their viewer counts"""
        channels = self.get_all_channels()
        online_channels = self.get_online_channels()
        
        print("WebChnl Viewer Count Summary")
        print("=" * 40)
        print(f"Total Channels: {len(channels)}")
        print(f"Online Channels: {len(online_channels)}")
        print(f"Total Viewers: {self.get_total_viewers()}")
        print("\nChannel Details:")
        print("-" * 40)
        
        for channel in channels:
            status = "ONLINE" if channel.is_online else "OFFLINE"
            viewer_text = f"{channel.viewers} viewers" if channel.is_online else "offline"
            print(f"{channel.name:<20} | {status:<7} | {viewer_text}")


# Example usage
if __name__ == "__main__":
    # Initialize the viewer counts client
    viewer_client = ViewerCounts()
    
    try:
        # Get all channels
        all_channels = viewer_client.get_all_channels()
        print(f"Found {len(all_channels)} channels")
        
        # Get online channels only
        online_channels = viewer_client.get_online_channels()
        print(f"Online channels: {len(online_channels)}")
        
        # Print summary
        viewer_client.print_viewer_summary()
        
    except Exception as e:
        print(f"Error: {e}")