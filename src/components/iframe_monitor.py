
"""
IFrame Monitor Component
Handles ContentDM website embedding and URL monitoring
"""

try:
    import streamlit as st
    import streamlit.components.v1 as components
    from streamlit_autorefresh import st_autorefresh
except Exception:
    st = None  # type: ignore
    components = None  # type: ignore
    def st_autorefresh(*args, **kwargs):  # type: ignore
        return None
from typing import Optional
import re
import time

class IFrameMonitor:
    """Monitor iframe URL changes and display ContentDM website"""
    
    def __init__(self, base_url: str, height: int = 600):
        self.base_url = base_url
        self.height = height
        self.last_url = ""
    
    def render(self) -> str:
        """Render iframe and monitor URL changes"""
        
        # Create iframe HTML with URL monitoring
        iframe_html = self._create_iframe_html()
        
        # Display iframe with custom component
        current_url = components.html(
            iframe_html,
            height=self.height,
            scrolling=True
        )
        
        # Auto-refresh to check for URL changes
        # Refresh every 2 seconds to monitor URL changes
        st_autorefresh(interval=2000, limit=None, key="iframe_monitor")
        
        # Try to detect URL from session state or other methods
        detected_url = self._detect_current_url()
        
        return detected_url or self.base_url
    
    def _create_iframe_html(self) -> str:
        """Create HTML for iframe with URL monitoring"""
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    font-family: 'Arial', sans-serif;
                }}
                .iframe-container {{
                    position: relative;
                    width: 100%;
                    height: {self.height}px;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    overflow: hidden;
                    background: #f8f9fa;
                }}
                .iframe-header {{
                    background: #343a40;
                    color: white;
                    padding: 8px 16px;
                    font-size: 14px;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }}
                .url-display {{
                    flex: 1;
                    background: #495057;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-family: monospace;
                    font-size: 12px;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }}
                .status-indicator {{
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    background: #28a745;
                    animation: pulse 2s infinite;
                }}
                @keyframes pulse {{
                    0% {{ opacity: 1; }}
                    50% {{ opacity: 0.5; }}
                    100% {{ opacity: 1; }}
                }}
                iframe {{
                    width: 100%;
                    height: calc(100% - 40px);
                    border: none;
                    background: white;
                }}
                .loading-overlay {{
                    position: absolute;
                    top: 40px;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(255, 255, 255, 0.9);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 16px;
                    color: #666;
                }}
                .spinner {{
                    border: 3px solid #f3f3f3;
                    border-top: 3px solid #007bff;
                    border-radius: 50%;
                    width: 30px;
                    height: 30px;
                    animation: spin 1s linear infinite;
                    margin-right: 10px;
                }}
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
            </style>
        </head>
        <body>
            <div class="iframe-container">
                <div class="iframe-header">
                    <div class="status-indicator"></div>
                    <span>ContentDM Browser:</span>
                    <div class="url-display" id="urlDisplay">{self.base_url}</div>
                </div>
                <div class="loading-overlay" id="loadingOverlay">
                    <div class="spinner"></div>
                    Loading ContentDM...
                </div>
                <iframe 
                    src="{self.base_url}" 
                    id="contentdm-iframe"
                    onload="hideLoading()"
                    allow="fullscreen"
                    sandbox="allow-same-origin allow-scripts allow-forms allow-navigation allow-top-navigation">
                </iframe>
            </div>
            
            <script>
                let currentUrl = "{self.base_url}";
                let urlChangeCount = 0;
                
                function hideLoading() {{
                    document.getElementById('loadingOverlay').style.display = 'none';
                }}
                
                function updateUrlDisplay(url) {{
                    document.getElementById('urlDisplay').textContent = url;
                    currentUrl = url;
                    
                    // Store URL in session storage for Streamlit to access
                    if (typeof(Storage) !== "undefined") {{
                        sessionStorage.setItem('contentdm_current_url', url);
                        sessionStorage.setItem('contentdm_url_change_count', ++urlChangeCount);
                    }}
                }}
                
                // Monitor iframe URL changes (limited by same-origin policy)
                setInterval(function() {{
                    try {{
                        const iframe = document.getElementById('contentdm-iframe');
                        if (iframe.contentWindow.location.href !== currentUrl) {{
                            updateUrlDisplay(iframe.contentWindow.location.href);
                        }}
                    }} catch (e) {{
                        // Cross-origin access blocked - this is expected
                        // URL monitoring will be handled by other means
                    }}
                }}, 1000);
                
                // Initial URL set
                updateUrlDisplay(currentUrl);
            </script>
        </body>
        </html>
        """
        
        return html
    
    def _detect_current_url(self) -> Optional[str]:
        """Try to detect current URL from various sources"""
        
        # Method 1: Check session state for manually entered URLs
        if 'manual_contentdm_url' in st.session_state:
            return st.session_state.manual_contentdm_url
        
        # Method 2: Pattern matching from any text inputs
        # This would be populated by user navigation or input
        if hasattr(st.session_state, 'current_url') and st.session_state.current_url:
            return st.session_state.current_url
        
        # Method 3: Default to base URL
        return self.base_url
    
    def create_url_input(self) -> str:
        """Create URL input widget for manual navigation"""
        
        st.markdown("##### 🔗 Navigate to ContentDM Item")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            manual_url = st.text_input(
                "Enter ContentDM URL:",
                value=st.session_state.get('manual_contentdm_url', self.base_url),
                placeholder="https://vu.contentdm.oclc.org/digital/collection/alias/id/123",
                help="Enter the full URL of a ContentDM item detail page",
                key="manual_url_input"
            )
        
        with col2:
            if st.button("🔄 Navigate", type="primary"):
                if manual_url and manual_url != self.base_url:
                    st.session_state.manual_contentdm_url = manual_url
                    st.session_state.current_url = manual_url
                    st.rerun()
        
        # Quick navigation options
        st.markdown("**Quick Navigation:**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📚 Browse Collections"):
                browse_url = f"{self.base_url}/digital/collections"
                st.session_state.manual_contentdm_url = browse_url
                st.session_state.current_url = browse_url
                st.rerun()
        
        with col2:
            if st.button("🔍 Search"):
                search_url = f"{self.base_url}/digital/search"
                st.session_state.manual_contentdm_url = search_url
                st.session_state.current_url = search_url
                st.rerun()
        
        with col3:
            if st.button("🏠 Home"):
                st.session_state.manual_contentdm_url = self.base_url
                st.session_state.current_url = self.base_url
                st.rerun()
        
        return st.session_state.get('manual_contentdm_url', self.base_url)
    
    def extract_item_info_from_url(self, url: str) -> tuple[Optional[str], Optional[str]]:
        """Extract collection and item ID from ContentDM URL"""
        
        try:
            # Common ContentDM URL patterns:
            # https://site.contentdm.oclc.org/digital/collection/alias/id/123
            # https://site.contentdm.oclc.org/digital/collection/alias/id/123/rec/1
            
            patterns = [
                r'/collection/([^/]+)/id/(\d+)',  # Standard pattern
                r'/([^/]+)/id/(\d+)',            # Short pattern
                r'collection=([^&]+).*id=(\d+)', # Query parameter pattern
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    collection = match.group(1)
                    item_id = match.group(2)
                    return collection, item_id
            
            return None, None
            
        except Exception:
            return None, None
    
    def is_item_detail_page(self, url: str) -> bool:
        """Check if URL is an item detail page"""
        return '/id/' in url and any(pattern in url for pattern in ['/collection/', 'id='])
    
    def create_navigation_history(self):
        """Create navigation history widget"""
        
        if 'navigation_history' not in st.session_state:
            st.session_state.navigation_history = []
        
        # Add current URL to history
        current_url = st.session_state.get('current_url', self.base_url)
        if current_url not in st.session_state.navigation_history:
            st.session_state.navigation_history.append(current_url)
            
            # Keep only last 10 URLs
            if len(st.session_state.navigation_history) > 10:
                st.session_state.navigation_history = st.session_state.navigation_history[-10:]
        
        if len(st.session_state.navigation_history) > 1:
            st.markdown("**Recent Navigation:**")
            
            for i, hist_url in enumerate(reversed(st.session_state.navigation_history[-5:])):
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    # Extract display name
                    display_name = hist_url
                    collection, item_id = self.extract_item_info_from_url(hist_url)
                    if collection and item_id:
                        display_name = f"{collection}/{item_id}"
                    elif len(hist_url) > 50:
                        display_name = hist_url[:47] + "..."
                    
                    st.text(f"{i+1}. {display_name}")
                
                with col2:
                    if st.button("↩", key=f"nav_history_{i}", help="Go back to this URL"):
                        st.session_state.manual_contentdm_url = hist_url
                        st.session_state.current_url = hist_url
                        st.rerun()
