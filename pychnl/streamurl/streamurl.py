import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from typing import Optional, Dict, List
import re


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
    
    def _extract_stream_urls(self) -> Optional[Dict[str, any]]:
        """
        Extract all stream URLs and information from the video player
        
        Returns:
            Optional[Dict[str, any]]: Dictionary containing all stream information
        """
        try:
            # Wait for video container to load
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, "video-js"))
            )
            
            stream_info = {
                'urls': {},
                'poster': None,
                'blob_url': None,
                'sources': [],
                'metadata': {}
            }
            
            # Find the video container
            video_container = self.driver.find_element(By.CLASS_NAME, "video-js")
            
            # Extract poster URL from container
            poster_url = video_container.get_attribute("poster")
            if poster_url:
                stream_info['poster'] = poster_url
            
            # Find the actual video element
            video_element = self.driver.find_element(By.TAG_NAME, "video")
            
            # Get the blob URL from video src
            blob_src = video_element.get_attribute("src")
            if blob_src:
                stream_info['blob_url'] = blob_src
            
            # Extract poster from video element as well (fallback)
            if not stream_info['poster']:
                video_poster = video_element.get_attribute("poster")
                if video_poster:
                    stream_info['poster'] = video_poster
            
            # Find all source elements - this is the key part that needs fixing
            source_elements = video_element.find_elements(By.TAG_NAME, "source")
            
            print(f"Found {len(source_elements)} source elements")
            
            for i, source in enumerate(source_elements):
                src = source.get_attribute("src")
                source_type = source.get_attribute("type")
                
                print(f"Source {i+1}: src='{src}', type='{source_type}'")
                
                if src:
                    source_info = {
                        'url': src,
                        'type': source_type
                    }
                    
                    stream_info['sources'].append(source_info)
                    
                    # Improved M3U8 detection
                    is_m3u8 = False
                    
                    # Check by MIME type
                    if source_type:
                        if ("application/x-mpegurl" in source_type.lower() or 
                            "application/vnd.apple.mpegurl" in source_type.lower() or
                            "m3u8" in source_type.lower()):
                            is_m3u8 = True
                    
                    # Check by file extension
                    if src.endswith('.m3u8'):
                        is_m3u8 = True
                    
                    # Check by URL pattern (delta.webchnl.live with .m3u8)
                    if 'delta.webchnl.live' in src and '.m3u8' in src:
                        is_m3u8 = True
                    
                    if is_m3u8:
                        stream_info['urls']['m3u8'] = src
                        print(f"✅ Found M3U8 URL: {src}")
                    elif source_type and "mp4" in source_type:
                        stream_info['urls']['mp4'] = src
                        print(f"✅ Found MP4 URL: {src}")
                    elif source_type and "webm" in source_type:
                        stream_info['urls']['webm'] = src
                        print(f"✅ Found WebM URL: {src}")
                    elif src.endswith('.mp4'):
                        stream_info['urls']['mp4'] = src
                        print(f"✅ Found MP4 URL (by extension): {src}")
                    elif src.endswith('.webm'):
                        stream_info['urls']['webm'] = src
                        print(f"✅ Found WebM URL (by extension): {src}")
            
            # Additional fallback: Try to extract M3U8 URL from page source if not found
            if 'm3u8' not in stream_info['urls']:
                print("M3U8 not found in source elements, trying page source extraction...")
                m3u8_url = self._extract_m3u8_from_page()
                if m3u8_url:
                    stream_info['urls']['m3u8'] = m3u8_url
                    print(f"✅ Found M3U8 URL from page source: {m3u8_url}")
            
            # Try another approach: look for source elements more broadly
            if 'm3u8' not in stream_info['urls']:
                print("Trying broader source element search...")
                all_sources = self.driver.find_elements(By.CSS_SELECTOR, "source")
                for source in all_sources:
                    src = source.get_attribute("src")
                    if src and ('.m3u8' in src or 'delta.webchnl.live' in src):
                        stream_info['urls']['m3u8'] = src
                        print(f"✅ Found M3U8 URL from broader search: {src}")
                        break
            
            # Extract additional metadata from video element
            video_attrs = ['preload', 'autoplay', 'controls', 'loop', 'muted']
            for attr in video_attrs:
                value = video_element.get_attribute(attr)
                if value is not None:
                    stream_info['metadata'][attr] = value
            
            # Get video dimensions if available
            try:
                video_width = video_element.get_attribute("videoWidth")
                video_height = video_element.get_attribute("videoHeight")
                if video_width and video_height:
                    stream_info['metadata']['dimensions'] = {
                        'width': video_width,
                        'height': video_height
                    }
            except:
                pass
            
            # Check if we found any useful URLs
            if stream_info['urls'] or stream_info['blob_url'] or stream_info['sources']:
                return stream_info
            else:
                return None
                
        except TimeoutException:
            print("Timeout waiting for video player to load")
            return None
        except NoSuchElementException:
            print("Video player element not found")
            return None
        except Exception as e:
            print(f"Error extracting stream URLs: {e}")
            return None
    
    def _extract_m3u8_from_page(self) -> Optional[str]:
        """
        Try to extract M3U8 URL from page source or JavaScript
        
        Returns:
            Optional[str]: M3U8 URL if found
        """
        try:
            # Get page source
            page_source = self.driver.page_source
            
            # Enhanced M3U8 pattern matching
            patterns = [
                r'https://delta\.webchnl\.live/memfs/[^"\'<>\s]+\.m3u8',
                r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*',
                r'"(https://delta\.webchnl\.live/[^"]+\.m3u8)"',
                r"'(https://delta\.webchnl\.live/[^']+\.m3u8)'"
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_source)
                if matches:
                    # Return the first match
                    url = matches[0]
                    if isinstance(url, tuple):
                        url = url[0]
                    print(f"Found M3U8 URL with pattern '{pattern}': {url}")
                    return url
            
            # Also try to execute JavaScript to find M3U8 URLs
            try:
                js_result = self.driver.execute_script("""
                    var sources = document.querySelectorAll('source');
                    for (var i = 0; i < sources.length; i++) {
                        var src = sources[i].getAttribute('src');
                        if (src && (src.includes('.m3u8') || src.includes('delta.webchnl.live'))) {
                            console.log('Found source:', src);
                            return src;
                        }
                    }
                    
                    // Also check for any elements with src containing m3u8
                    var allElements = document.querySelectorAll('[src*="m3u8"]');
                    for (var j = 0; j < allElements.length; j++) {
                        var src = allElements[j].getAttribute('src');
                        if (src) {
                            console.log('Found m3u8 element:', src);
                            return src;
                        }
                    }
                    
                    return null;
                """)
                
                if js_result:
                    print(f"Found M3U8 URL via JavaScript: {js_result}")
                    return js_result
                    
            except Exception as e:
                print(f"JavaScript execution failed: {e}")
                
            return None
            
        except Exception as e:
            print(f"Error extracting M3U8 from page: {e}")
            return None
    
    def get_stream_info(self, channel_name: str) -> Optional[Dict[str, any]]:
        """
        Get comprehensive stream information for a specific channel
        
        Args:
            channel_name (str): Name of the channel to get stream info for
            
        Returns:
            Optional[Dict[str, any]]: Dictionary containing all stream information
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
            time.sleep(3)
            
            # Extract all stream information
            print("Extracting stream information...")
            stream_info = self._extract_stream_urls()
            
            if stream_info:
                print(f"Successfully extracted stream info for '{channel_name}'")
                
                # Add channel name to the info
                stream_info['channel_name'] = channel_name
                stream_info['extraction_time'] = time.time()
                
                return stream_info
            else:
                print(f"Failed to extract stream info for '{channel_name}'")
                return None
                
        except Exception as e:
            print(f"Error getting stream info: {e}")
            return None
    
    def get_stream_url(self, channel_name: str) -> Optional[Dict[str, str]]:
        """
        Get stream URL for a specific channel (legacy method for backward compatibility)
        
        Args:
            channel_name (str): Name of the channel to get stream URL for
            
        Returns:
            Optional[Dict[str, str]]: Dictionary containing stream URLs
        """
        stream_info = self.get_stream_info(channel_name)
        
        if stream_info:
            # Return simplified format for backward compatibility
            result = {}
            
            if stream_info.get('urls'):
                result.update(stream_info['urls'])
            
            if stream_info.get('blob_url'):
                result['blob_url'] = stream_info['blob_url']
            
            if stream_info.get('poster'):
                result['poster_url'] = stream_info['poster']
            
            return result if result else None
        
        return None
    
    def get_available_channels(self) -> List[str]:
        """
        Get list of available channels from the main page
        
        Returns:
            List[str]: List of channel names
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
    # Test the comprehensive stream info extraction
    with StreamURL(headless=True) as stream_client:
        # Get available channels
        channels = stream_client.get_available_channels()
        print(f"Available channels: {channels}")
        
        # Test with a specific channel
        if channels:
            test_channel = channels[0]  # Use first available channel
            print(f"\nTesting with channel: {test_channel}")
            
            # Get comprehensive stream info
            stream_info = stream_client.get_stream_info(test_channel)
            
            if stream_info:
                print(f"\nComprehensive stream info for '{test_channel}':")
                print(f"Channel: {stream_info.get('channel_name', 'N/A')}")
                print(f"Poster: {stream_info.get('poster', 'N/A')}")
                print(f"Blob URL: {stream_info.get('blob_url', 'N/A')}")
                
                print("\nStream URLs:")
                for url_type, url in stream_info.get('urls', {}).items():
                    print(f"  {url_type}: {url}")
                
                print("\nAll Sources:")
                for i, source in enumerate(stream_info.get('sources', [])):
                    print(f"  Source {i+1}: {source['url']} (type: {source['type']})")
                
                print("\nMetadata:")
                for key, value in stream_info.get('metadata', {}).items():
                    print(f"  {key}: {value}")
                
                # Test legacy method
                print("\n--- Legacy method test ---")
                legacy_result = stream_client.get_stream_url(test_channel)
                if legacy_result:
                    print("Legacy format result:")
                    for key, value in legacy_result.items():
                        print(f"  {key}: {value}")
                        
            else:
                print(f"Failed to get stream info for '{test_channel}'")