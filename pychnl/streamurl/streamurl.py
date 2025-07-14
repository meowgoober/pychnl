import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from typing import Optional, Dict


class StreamURL:
    """Handle stream URL extraction from webchnl.live"""
    
    def __init__(self, headless: bool = True, timeout: int = 30):
        """
        Initialize the StreamURL client
        
        Args:
            headless (bool): Run browser in headless mode
            timeout (int): Timeout in seconds for page loads and element waits
        """
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        self.base_url = "https://webchnl.live"
        
    def _setup_driver(self):
        """Set up the Chrome driver with appropriate options"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Additional options for better performance and compatibility
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Automatically download and setup ChromeDriver
        service = Service(ChromeDriverManager().install())
        
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def _find_channel_button(self, channel_name: str) -> Optional[object]:
        """
        Find the channel button by name
        
        Args:
            channel_name (str): Name of the channel to find
            
        Returns:
            Optional[WebElement]: The channel button element if found
        """
        try:
            # Wait for channel items to load
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, "item"))
            )
            
            # Find all channel items
            channel_items = self.driver.find_elements(By.CLASS_NAME, "item")
            
            for item in channel_items:
                try:
                    # Look for the channel name in the h1 tag
                    channel_name_element = item.find_element(By.CSS_SELECTOR, "h1[channel-name]")
                    if channel_name_element.text.strip().lower() == channel_name.lower():
                        return item
                except NoSuchElementException:
                    continue
                    
            return None
            
        except TimeoutException:
            print(f"Timeout waiting for channel items to load")
            return None
    
    def _extract_stream_url(self) -> Optional[Dict[str, str]]:
        """
        Extract stream URL from the video element
        
        Returns:
            Optional[Dict[str, str]]: Dictionary containing stream URLs if found
        """
        try:
            # Wait for video element to load
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "video"))
            )
            
            # Find the video element
            video_element = self.driver.find_element(By.TAG_NAME, "video")
            
            # Extract different types of URLs
            stream_info = {}
            
            # Get the main src attribute (blob URL)
            main_src = video_element.get_attribute("src")
            if main_src:
                stream_info["blob_url"] = main_src
            
            # Get source elements for direct stream URLs
            source_elements = video_element.find_elements(By.TAG_NAME, "source")
            
            for source in source_elements:
                src = source.get_attribute("src")
                source_type = source.get_attribute("type")
                
                if src and source_type:
                    if "m3u8" in source_type:
                        stream_info["m3u8_url"] = src
                    elif "mp4" in source_type:
                        stream_info["mp4_url"] = src
            
            # Get poster image if available
            poster = video_element.get_attribute("poster")
            if poster:
                stream_info["poster_url"] = poster
                
            return stream_info if stream_info else None
            
        except TimeoutException:
            print("Timeout waiting for video element to load")
            return None
        except NoSuchElementException:
            print("Video element not found")
            return None
    
    def get_stream_url(self, channel_name: str) -> Optional[Dict[str, str]]:
        """
        Get stream URL for a specific channel
        
        Args:
            channel_name (str): Name of the channel to get stream URL for
            
        Returns:
            Optional[Dict[str, str]]: Dictionary containing stream URLs and info
        """
        try:
            # Setup driver if not already done
            if not self.driver:
                self._setup_driver()
            
            # Navigate to webchnl.live
            print(f"Navigating to {self.base_url}...")
            self.driver.get(self.base_url)
            
            # Find and click the channel button
            print(f"Looking for channel: {channel_name}")
            channel_button = self._find_channel_button(channel_name)
            
            if not channel_button:
                print(f"Channel '{channel_name}' not found")
                return None
            
            print(f"Found channel '{channel_name}', clicking...")
            channel_button.click()
            
            # Wait a bit for the page to load
            time.sleep(2)
            
            # Extract stream URL from video element
            print("Extracting stream URL...")
            stream_info = self._extract_stream_url()
            
            if stream_info:
                print(f"Successfully extracted stream info for '{channel_name}'")
                return stream_info
            else:
                print(f"Failed to extract stream info for '{channel_name}'")
                return None
                
        except Exception as e:
            print(f"Error getting stream URL: {e}")
            return None
    
    def get_available_channels(self) -> list:
        """
        Get list of available channels from the main page
        
        Returns:
            list: List of channel names
        """
        try:
            # Setup driver if not already done
            if not self.driver:
                self._setup_driver()
            
            # Navigate to webchnl.live
            self.driver.get(self.base_url)
            
            # Wait for channel items to load
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, "item"))
            )
            
            # Find all channel items
            channel_items = self.driver.find_elements(By.CLASS_NAME, "item")
            channels = []
            
            for item in channel_items:
                try:
                    channel_name_element = item.find_element(By.CSS_SELECTOR, "h1[channel-name]")
                    channels.append(channel_name_element.text.strip())
                except NoSuchElementException:
                    continue
            
            return channels
            
        except Exception as e:
            print(f"Error getting available channels: {e}")
            return []
    
    def close(self):
        """Close the browser driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Example usage
if __name__ == "__main__":
    # Test the stream URL extraction
    with StreamURL(headless=True) as stream_client:
        # Get available channels
        channels = stream_client.get_available_channels()
        print(f"Available channels: {channels}")
        
        # Test with a specific channel
        if channels:
            test_channel = channels[0]  # Use first available channel
            stream_info = stream_client.get_stream_url(test_channel)
            
            if stream_info:
                print(f"\nStream info for '{test_channel}':")
                for key, value in stream_info.items():
                    print(f"  {key}: {value}")
            else:
                print(f"Failed to get stream info for '{test_channel}'")