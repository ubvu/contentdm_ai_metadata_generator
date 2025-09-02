
"""
Processing Log Component
Displays expandable log of AI processing steps and status updates
"""

try:
    import streamlit as st
except Exception:  # Allow import without Streamlit for tests
    class _Stub:
        session_state = {}
    st = _Stub()  # type: ignore
from datetime import datetime
from typing import List, Dict, Any, Optional

class ProcessingLog:
    """Interactive processing log for Streamlit"""
    
    def __init__(self, max_entries: int = 100):
        self.max_entries = max_entries
        
        # Initialize session state
        if 'processing_log_entries' not in st.session_state:
            st.session_state.processing_log_entries = []
        
        if 'log_auto_scroll' not in st.session_state:
            st.session_state.log_auto_scroll = True
        
        if 'log_expanded' not in st.session_state:
            st.session_state.log_expanded = False
    
    def add_entry(self, level: str, message: str, details: Optional[Dict[str, Any]] = None):
        """Add new log entry"""
        
        entry = {
            'timestamp': datetime.now(),
            'level': level.upper(),
            'message': message,
            'details': details or {}
        }
        
        # Add to session state
        st.session_state.processing_log_entries.append(entry)
        
        # Maintain max entries limit
        if len(st.session_state.processing_log_entries) > self.max_entries:
            st.session_state.processing_log_entries = st.session_state.processing_log_entries[-self.max_entries:]
        
        # Auto-expand log for important messages
        if level.upper() in ['ERROR', 'SUCCESS']:
            st.session_state.log_expanded = True
    
    def render(self):
        """Render the processing log component"""
        
        # Header with controls
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown("### 📋 Processing Log")
        
        with col2:
            if st.button("🗑️ Clear", key="clear_log", help="Clear all log entries"):
                self.clear_log()
                st.rerun()
        
        with col3:
            st.session_state.log_auto_scroll = st.checkbox(
                "Auto-scroll", 
                value=st.session_state.log_auto_scroll,
                help="Automatically scroll to latest entries"
            )
        
        # Log entries count and filters
        entries = st.session_state.processing_log_entries
        
        if entries:
            # Quick stats
            stats = self._get_log_stats(entries)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total", len(entries))
            with col2:
                st.metric("Errors", stats.get('ERROR', 0))
            with col3:
                st.metric("Success", stats.get('SUCCESS', 0))
            with col4:
                st.metric("Info", stats.get('INFO', 0))
            
            # Filter options
            with st.expander("🔍 Filter Options"):
                col1, col2 = st.columns(2)
                
                with col1:
                    level_filter = st.multiselect(
                        "Filter by Level:",
                        options=['INFO', 'SUCCESS', 'WARNING', 'ERROR'],
                        default=['INFO', 'SUCCESS', 'WARNING', 'ERROR'],
                        key="log_level_filter"
                    )
                
                with col2:
                    max_display = st.slider(
                        "Max entries to show:",
                        min_value=10,
                        max_value=100,
                        value=20,
                        key="log_max_display"
                    )
            
            # Filter entries
            filtered_entries = [
                entry for entry in entries[-max_display:]
                if entry['level'] in level_filter
            ]
            
            # Display log entries
            if filtered_entries:
                # Create expandable log viewer
                with st.expander(
                    f"📝 Log Entries ({len(filtered_entries)} shown)", 
                    expanded=st.session_state.log_expanded
                ):
                    self._render_log_entries(filtered_entries)
                    
                    # Download log button
                    if st.button("📥 Download Log", key="download_log"):
                        self._create_download_log(entries)
            
            else:
                st.info("No log entries match current filters")
        
        else:
            st.info("No log entries yet. Processing activities will appear here.")
    
    def _render_log_entries(self, entries: List[Dict[str, Any]]):
        """Render individual log entries"""
        
        # Create container for log entries
        log_container = st.container()
        
        with log_container:
            # Reverse entries to show latest first
            if st.session_state.log_auto_scroll:
                display_entries = entries
            else:
                display_entries = list(reversed(entries))
            
            for i, entry in enumerate(display_entries):
                self._render_single_entry(entry, i)
    
    def _render_single_entry(self, entry: Dict[str, Any], index: int):
        """Render a single log entry"""
        
        timestamp = entry['timestamp']
        level = entry['level']
        message = entry['message']
        details = entry.get('details', {})
        
        # Choose styling based on level
        if level == 'ERROR':
            icon = "🔴"
            border_color = "#dc3545"
        elif level == 'SUCCESS':
            icon = "🟢"
            border_color = "#28a745"
        elif level == 'WARNING':
            icon = "🟡"
            border_color = "#ffc107"
        else:  # INFO
            icon = "🔵"
            border_color = "#17a2b8"
        
        # Create entry container with styling
        with st.container():
            st.markdown(f"""
            <div style="
                border-left: 3px solid {border_color};
                padding: 8px 12px;
                margin: 4px 0;
                background: rgba(128, 128, 128, 0.05);
                border-radius: 0 4px 4px 0;
            ">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span>{icon}</span>
                    <strong>{level}</strong>
                    <span style="color: #666; font-size: 0.85em;">
                        {timestamp.strftime('%H:%M:%S')}
                    </span>
                </div>
                <div style="margin-top: 4px; margin-left: 24px;">
                    {message}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Show details if available
            if details:
                with st.expander(f"Details for entry {index + 1}", expanded=False):
                    st.json(details)
    
    def _get_log_stats(self, entries: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get statistics about log entries"""
        stats = {}
        
        for entry in entries:
            level = entry['level']
            stats[level] = stats.get(level, 0) + 1
        
        return stats
    
    def _create_download_log(self, entries: List[Dict[str, Any]]):
        """Create downloadable log file"""
        # Prepare data rows
        rows = []
        for entry in entries:
            rows.append({
                'Timestamp': entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                'Level': entry['level'],
                'Message': entry['message'],
                'Details': str(entry.get('details', ''))
            })

        # Try pandas first for convenience; fall back to csv
        csv_data: str
        try:
            import pandas as pd  # type: ignore
            df = pd.DataFrame(rows)
            csv_data = df.to_csv(index=False)
        except Exception:
            import io, csv as _csv
            buf = io.StringIO()
            if rows:
                writer = _csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)
            csv_data = buf.getvalue()
        
        # Create download button
        filename = f"processing_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        st.download_button(
            label="📥 Download as CSV",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            help="Download the processing log as a CSV file"
        )
    
    def clear_log(self):
        """Clear all log entries"""
        st.session_state.processing_log_entries = []
        st.session_state.log_expanded = False
    
    def get_recent_entries(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent log entries"""
        entries = st.session_state.processing_log_entries
        return entries[-count:] if entries else []
    
    def get_error_count(self) -> int:
        """Get count of error entries"""
        entries = st.session_state.processing_log_entries
        return len([e for e in entries if e['level'] == 'ERROR'])
    
    def has_errors(self) -> bool:
        """Check if there are any error entries"""
        return self.get_error_count() > 0
    
    def create_status_summary(self):
        """Create compact status summary widget"""
        
        entries = st.session_state.processing_log_entries
        
        if not entries:
            return
        
        recent_entries = entries[-5:]  # Last 5 entries
        
        # Show status indicators
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if self.has_errors():
                st.error(f"❌ {self.get_error_count()} errors")
            else:
                st.success("✅ No errors")
        
        with col2:
            if recent_entries:
                latest = recent_entries[-1]
                st.text(f"Latest: {latest['message'][:40]}...")
        
        with col3:
            st.text(f"{len(entries)} total entries")
    
    def add_processing_start(self, item_id: str):
        """Add entry for processing start"""
        self.add_entry("INFO", f"Started processing item {item_id}")
    
    def add_processing_complete(self, item_id: str, duration: float = None):
        """Add entry for processing completion"""
        message = f"Completed processing item {item_id}"
        if duration:
            message += f" ({duration:.1f}s)"
        
        self.add_entry("SUCCESS", message)
    
    def add_error(self, error_message: str, details: Optional[Dict[str, Any]] = None):
        """Add error entry with optional details"""
        self.add_entry("ERROR", error_message, details)
    
    def add_model_loading(self, model_name: str):
        """Add entry for model loading"""
        self.add_entry("INFO", f"Loading AI model: {model_name}")
    
    def add_api_call(self, endpoint: str, status: str):
        """Add entry for API calls"""
        level = "SUCCESS" if status == "success" else "ERROR"
        self.add_entry(level, f"ContentDM API call to {endpoint}: {status}")
