
"""
ContentDM API Integration Module
Handles all interactions with ContentDM API endpoints
"""

import requests
import logging
from typing import Dict, List, Optional, Any, Tuple
import time
from urllib.parse import urljoin, quote
import json
from PIL import Image
import io
import base64

class ContentDMAPI:
    """ContentDM API client for fetching metadata and images"""
    
    def __init__(self, config: Dict[str, Any]):
        self.base_url = config.get('base_url', 'https://vu.contentdm.oclc.org')
        self.api_endpoint = config.get('api_endpoint', '/digital/bl/dmwebservices/index.php')
        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)
        
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        
        # Set common headers
        self.session.headers.update({
            'User-Agent': 'ContentDM-AI-Metadata-Generator/1.0',
            'Accept': 'application/json, text/plain, */*'
        })
    
    def _make_api_call(self, query: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make API call to ContentDM with retry logic"""
        url = urljoin(self.base_url, self.api_endpoint)
        
        params = {'q': query}
        if kwargs:
            for key, value in kwargs.items():
                params[key] = value
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                
                # Handle different response formats
                content_type = response.headers.get('content-type', '').lower()
                
                if 'application/json' in content_type:
                    return response.json()
                elif response.text.strip():
                    # Try to parse as JSON even if content-type is not set
                    try:
                        return json.loads(response.text)
                    except json.JSONDecodeError:
                        return {'raw_response': response.text}
                else:
                    return None
                    
            except requests.RequestException as e:
                self.logger.warning(f"API call attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    self.logger.error(f"API call failed after {self.max_retries} attempts: {e}")
                    return None
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def get_item_info(self, collection: str, item_id: str) -> Optional[Dict[str, Any]]:
        """Get item metadata using dmGetItemInfo"""
        query = f"dmGetItemInfo/{collection}/{item_id}/json"
        
        try:
            result = self._make_api_call(query)
            if result:
                self.logger.info(f"Successfully fetched item info for {collection}/{item_id}")
                return result
            else:
                self.logger.error(f"Failed to fetch item info for {collection}/{item_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching item info: {e}")
            return None
    
    def get_image_info(self, collection: str, item_id: str) -> Optional[Dict[str, Any]]:
        """Get image metadata using dmGetImageInfo"""
        query = f"dmGetImageInfo/{collection}/{item_id}/json"
        
        try:
            result = self._make_api_call(query)
            if result:
                self.logger.info(f"Successfully fetched image info for {collection}/{item_id}")
                return result
            else:
                self.logger.error(f"Failed to fetch image info for {collection}/{item_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching image info: {e}")
            return None
    
    def get_image_data(self, collection: str, item_id: str, 
                      format: str = "jpeg", size: str = "medium") -> Optional[Image.Image]:
        """Get image file using dmGetFile or dmGetStreamingFile"""
        
        # Try dmGetFile first (for images)
        query = f"dmGetFile/{collection}/{item_id}"
        
        try:
            # Get image bytes
            url = urljoin(self.base_url, self.api_endpoint)
            params = {'q': query}
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            
            if response.status_code == 200 and response.content:
                # Try to open as image
                try:
                    image = Image.open(io.BytesIO(response.content))
                    self.logger.info(f"Successfully fetched image for {collection}/{item_id}")
                    return image
                except Exception as img_error:
                    self.logger.warning(f"Failed to parse image from dmGetFile: {img_error}")
            
            # Try dmGetStreamingFile as fallback
            streaming_query = f"dmGetStreamingFile/{collection}/{item_id}.jpg/xml"
            streaming_result = self._make_api_call(streaming_query)
            
            if streaming_result and 'raw_response' in streaming_result:
                # Parse streaming file response for image URL
                streaming_url = self._parse_streaming_url(streaming_result['raw_response'])
                if streaming_url:
                    img_response = self.session.get(streaming_url, timeout=self.timeout)
                    if img_response.status_code == 200:
                        image = Image.open(io.BytesIO(img_response.content))
                        self.logger.info(f"Successfully fetched streaming image for {collection}/{item_id}")
                        return image
            
            # Try IIIF endpoint as another fallback
            iiif_url = f"{self.base_url}/digital/iiif/{collection}/{item_id}/full/!800,800/0/default.jpg"
            iiif_response = self.session.get(iiif_url, timeout=self.timeout)
            
            if iiif_response.status_code == 200:
                image = Image.open(io.BytesIO(iiif_response.content))
                self.logger.info(f"Successfully fetched IIIF image for {collection}/{item_id}")
                return image
            
            self.logger.error(f"Failed to fetch image for {collection}/{item_id}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching image data: {e}")
            return None
    
    def _parse_streaming_url(self, xml_response: str) -> Optional[str]:
        """Parse streaming file XML response to extract image URL"""
        try:
            # Simple XML parsing to extract URL
            import re
            url_match = re.search(r'<url[^>]*>([^<]+)</url>', xml_response)
            if url_match:
                return url_match.group(1)
            return None
        except Exception as e:
            self.logger.error(f"Error parsing streaming URL: {e}")
            return None
    
    def get_collection_info(self, collection: str) -> Optional[Dict[str, Any]]:
        """Get collection metadata using dmGetCollectionInfo"""
        query = f"dmGetCollectionInfo/{collection}/json"
        
        try:
            result = self._make_api_call(query)
            if result:
                self.logger.info(f"Successfully fetched collection info for {collection}")
                return result
            else:
                self.logger.error(f"Failed to fetch collection info for {collection}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching collection info: {e}")
            return None
    
    def get_collection_items(self, collection: str, 
                           max_records: int = 1000) -> List[Dict[str, Any]]:
        """Get collection items using dmQuery"""
        
        all_items = []
        start = 1
        batch_size = 100
        
        try:
            while len(all_items) < max_records:
                # Query collection items
                query = f"dmQuery/{collection}/0/title/title/title/{batch_size}/{start}/0/0/0/json"
                
                result = self._make_api_call(query)
                
                if not result or 'records' not in result:
                    break
                
                records = result['records']
                if not records:
                    break
                
                all_items.extend(records)
                
                # Check if we've reached the end
                if len(records) < batch_size:
                    break
                
                start += batch_size
                
                # Respect rate limits
                time.sleep(0.1)
            
            self.logger.info(f"Successfully fetched {len(all_items)} items from collection {collection}")
            return all_items[:max_records]
            
        except Exception as e:
            self.logger.error(f"Error fetching collection items: {e}")
            return []
    
    def search_items(self, collection: str, searchterm: str, 
                    field: str = "CISOSEARCHALL", max_records: int = 100) -> List[Dict[str, Any]]:
        """Search items in collection using dmQuery"""
        
        try:
            # URL encode search term
            encoded_searchterm = quote(searchterm)
            
            query = f"dmQuery/{collection}/{encoded_searchterm}/{field}/title/title/{max_records}/1/0/0/0/json"
            
            result = self._make_api_call(query)
            
            if result and 'records' in result:
                items = result['records']
                self.logger.info(f"Successfully found {len(items)} items matching '{searchterm}' in {collection}")
                return items
            else:
                self.logger.warning(f"No items found matching '{searchterm}' in {collection}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error searching items: {e}")
            return []
    
    def get_field_info(self, collection: str) -> Optional[Dict[str, Any]]:
        """Get collection field configuration using dmGetCollectionFieldInfo"""
        query = f"dmGetCollectionFieldInfo/{collection}/json"
        
        try:
            result = self._make_api_call(query)
            if result:
                self.logger.info(f"Successfully fetched field info for {collection}")
                return result
            else:
                self.logger.error(f"Failed to fetch field info for {collection}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching field info: {e}")
            return None
    
    def get_thumbnail(self, collection: str, item_id: str, 
                     width: int = 150, height: int = 150) -> Optional[Image.Image]:
        """Get item thumbnail using dmGetThumbnail"""
        query = f"dmGetThumbnail/{collection}/{item_id}"
        
        try:
            url = urljoin(self.base_url, self.api_endpoint)
            params = {'q': query}
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            
            if response.status_code == 200 and response.content:
                image = Image.open(io.BytesIO(response.content))
                self.logger.info(f"Successfully fetched thumbnail for {collection}/{item_id}")
                return image
            else:
                self.logger.error(f"Failed to fetch thumbnail for {collection}/{item_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching thumbnail: {e}")
            return None
    
    def validate_item(self, collection: str, item_id: str) -> bool:
        """Validate that an item exists in the collection"""
        try:
            metadata = self.get_item_info(collection, item_id)
            return metadata is not None and not metadata.get('error')
        except Exception:
            return False
    
    def get_collection_list(self) -> List[Dict[str, Any]]:
        """Get list of all available collections using dmGetCollectionList"""
        query = "dmGetCollectionList/json"
        
        try:
            result = self._make_api_call(query)
            if result:
                collections = result if isinstance(result, list) else [result]
                self.logger.info(f"Successfully fetched {len(collections)} collections")
                return collections
            else:
                self.logger.error("Failed to fetch collection list")
                return []
                
        except Exception as e:
            self.logger.error(f"Error fetching collection list: {e}")
            return []
