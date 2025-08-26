
"""
ContentDM AI Metadata Generator
Main Streamlit application for generating AI-enhanced metadata for ContentDM collections
"""

import streamlit as st
import os
import sys
import logging
from pathlib import Path
import yaml
import pandas as pd
from typing import Dict, List, Optional, Tuple
import asyncio

# Add src directory to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from contentdm_api import ContentDMAPI
from ai_processor import AIProcessor
from data_manager import DataManager
from utils.config_manager import ConfigManager
from utils.logger import setup_logger
from components.iframe_monitor import IFrameMonitor
from components.processing_log import ProcessingLog

# Configure Streamlit page
st.set_page_config(
    page_title="ContentDM AI Metadata Generator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

class ContentDMApp:
    """Main application class for ContentDM AI Metadata Generator"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config()
        self.logger = setup_logger(self.config.get('logging', {}))
        
        # Initialize components
        self.api = ContentDMAPI(self.config.get('contentdm', {}))
        self.ai_processor = AIProcessor(self.config.get('ai_models', {}))
        self.data_manager = DataManager(self.config.get('export', {}))
        self.processing_log = ProcessingLog()
        
        # Initialize session state
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize Streamlit session state"""
        if 'current_url' not in st.session_state:
            st.session_state.current_url = ""
        if 'current_item_id' not in st.session_state:
            st.session_state.current_item_id = None
        if 'current_collection' not in st.session_state:
            st.session_state.current_collection = None
        if 'processing_results' not in st.session_state:
            st.session_state.processing_results = {}
        if 'batch_progress' not in st.session_state:
            st.session_state.batch_progress = 0
        if 'ai_models_loaded' not in st.session_state:
            st.session_state.ai_models_loaded = False
    
    def run(self):
        """Main application runner"""
        st.title("🤖 ContentDM AI Metadata Generator")
        st.markdown("Generate enhanced metadata for historical images and artwork using AI")
        
        # Create main layout
        col_main, col_sidebar = st.columns([0.8, 0.2])
        
        with col_main:
            self._render_main_content()
        
        with col_sidebar:
            self._render_sidebar()
    
    def _render_main_content(self):
        """Render main content area with iframe"""
        st.markdown("### ContentDM Browser")
        
        # ContentDM URL input
        contentdm_url = st.text_input(
            "ContentDM URL",
            value=self.config['contentdm']['base_url'],
            help="Navigate to any ContentDM collection or item"
        )
        
        # Create iframe container
        iframe_container = st.container()
        
        with iframe_container:
            # Monitor URL changes and display iframe
            iframe_monitor = IFrameMonitor(contentdm_url, height=600)
            current_url = iframe_monitor.render()
            
            # Update session state if URL changed
            if current_url != st.session_state.current_url:
                st.session_state.current_url = current_url
                self._handle_url_change(current_url)
    
    def _render_sidebar(self):
        """Render metadata extraction sidebar"""
        st.markdown("### 📊 Metadata Extraction")
        
        # Show current item info
        if st.session_state.current_item_id:
            st.success(f"**Item ID:** {st.session_state.current_item_id}")
            st.success(f"**Collection:** {st.session_state.current_collection}")
            
            # Load AI models button
            if not st.session_state.ai_models_loaded:
                if st.button("🔄 Load AI Models", help="Initialize AI models for processing"):
                    with st.spinner("Loading AI models..."):
                        self._load_ai_models()
            
            # Auto generate button
            if st.session_state.ai_models_loaded:
                if st.button("🤖 Auto Generate Additional Metadata", type="primary"):
                    self._process_current_item()
            
            # Processing results
            if st.session_state.current_item_id in st.session_state.processing_results:
                self._render_processing_results()
            
            # Export options
            st.markdown("---")
            st.markdown("### 💾 Export Options")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save Item"):
                    self._save_current_item()
            
            with col2:
                if st.button("📦 Export Item"):
                    self._export_current_item()
            
            # Batch processing
            st.markdown("---")
            st.markdown("### 🔄 Batch Processing")
            
            if st.button("📊 Process Collection", help="Process all items in current collection"):
                self._process_collection()
            
            if st.button("📦 Export All", help="Export all processed items"):
                self._export_all()
            
            # Show batch progress
            if st.session_state.batch_progress > 0:
                st.progress(st.session_state.batch_progress)
        
        else:
            st.info("👈 Navigate to a ContentDM item detail page to begin metadata extraction")
            
        # Processing log
        st.markdown("---")
        self.processing_log.render()
    
    def _handle_url_change(self, url: str):
        """Handle URL change in iframe"""
        try:
            # Check if URL contains item ID pattern
            if '/id/' in url:
                # Extract collection and item ID from URL
                collection, item_id = self._parse_contentdm_url(url)
                
                if collection and item_id:
                    st.session_state.current_collection = collection
                    st.session_state.current_item_id = item_id
                    
                    self.processing_log.add_entry(
                        "INFO", 
                        f"Detected item: {collection}/{item_id}"
                    )
                    
                    # Fetch basic metadata
                    self._fetch_item_metadata(collection, item_id)
            else:
                # Reset current item if not on detail page
                st.session_state.current_item_id = None
                st.session_state.current_collection = None
                
        except Exception as e:
            self.logger.error(f"Error handling URL change: {e}")
            st.error(f"Error processing URL: {e}")
    
    def _parse_contentdm_url(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse ContentDM URL to extract collection and item ID"""
        try:
            # Pattern: .../collection/id/123
            parts = url.split('/')
            id_index = None
            
            for i, part in enumerate(parts):
                if part == 'id' and i + 1 < len(parts):
                    id_index = i + 1
                    break
            
            if id_index and id_index - 1 >= 0:
                item_id = parts[id_index]
                collection = parts[id_index - 1]
                return collection, item_id
            
            return None, None
            
        except Exception as e:
            self.logger.error(f"Error parsing ContentDM URL: {e}")
            return None, None
    
    def _fetch_item_metadata(self, collection: str, item_id: str):
        """Fetch basic item metadata from ContentDM API"""
        try:
            with st.spinner("Fetching item metadata..."):
                metadata = self.api.get_item_info(collection, item_id)
                
                if metadata:
                    # Store metadata in session state
                    if 'item_metadata' not in st.session_state:
                        st.session_state.item_metadata = {}
                    
                    st.session_state.item_metadata[f"{collection}/{item_id}"] = metadata
                    
                    self.processing_log.add_entry(
                        "SUCCESS", 
                        f"Fetched metadata for {collection}/{item_id}"
                    )
                else:
                    self.processing_log.add_entry(
                        "ERROR", 
                        f"Failed to fetch metadata for {collection}/{item_id}"
                    )
                    
        except Exception as e:
            self.logger.error(f"Error fetching item metadata: {e}")
            self.processing_log.add_entry("ERROR", f"Metadata fetch failed: {e}")
    
    def _load_ai_models(self):
        """Load AI models for processing"""
        try:
            success = self.ai_processor.initialize_models()
            if success:
                st.session_state.ai_models_loaded = True
                st.success("✅ AI models loaded successfully!")
                self.processing_log.add_entry("SUCCESS", "AI models loaded")
            else:
                st.error("❌ Failed to load AI models")
                self.processing_log.add_entry("ERROR", "AI model loading failed")
                
        except Exception as e:
            self.logger.error(f"Error loading AI models: {e}")
            st.error(f"Error loading AI models: {e}")
            self.processing_log.add_entry("ERROR", f"AI model error: {e}")
    
    def _process_current_item(self):
        """Process current item with AI"""
        if not st.session_state.current_item_id or not st.session_state.current_collection:
            st.error("No item selected")
            return
        
        collection = st.session_state.current_collection
        item_id = st.session_state.current_item_id
        
        try:
            with st.spinner("Processing item with AI..."):
                # Get image data
                image_data = self.api.get_image_data(collection, item_id)
                
                if not image_data:
                    st.error("Failed to fetch image data")
                    return
                
                # Process with AI
                results = self.ai_processor.process_item(
                    image_data, 
                    collection, 
                    item_id,
                    callback=lambda msg: self.processing_log.add_entry("INFO", msg)
                )
                
                if results:
                    # Store results
                    st.session_state.processing_results[item_id] = results
                    st.success("✅ Processing complete!")
                    self.processing_log.add_entry("SUCCESS", f"Processed {collection}/{item_id}")
                else:
                    st.error("Processing failed")
                    self.processing_log.add_entry("ERROR", f"Processing failed for {collection}/{item_id}")
                    
        except Exception as e:
            self.logger.error(f"Error processing item: {e}")
            st.error(f"Processing error: {e}")
            self.processing_log.add_entry("ERROR", f"Processing error: {e}")
    
    def _render_processing_results(self):
        """Render AI processing results"""
        item_id = st.session_state.current_item_id
        results = st.session_state.processing_results.get(item_id, {})
        
        if not results:
            return
        
        st.markdown("---")
        st.markdown("### 🤖 AI Processing Results")
        
        # Object Description
        if 'description' in results:
            with st.expander("📝 Object Description", expanded=True):
                st.write(results['description'])
        
        # Text Transcription
        if 'transcription' in results:
            with st.expander("📄 Text Transcription", expanded=False):
                st.text_area("Extracted Text", results['transcription'], height=100)
        
        # Named Entities
        if 'entities' in results and results['entities']:
            with st.expander("🏷️ Named Entities & Linked Data", expanded=False):
                df_entities = pd.DataFrame(results['entities'])
                st.dataframe(df_entities)
        
        # Dublin Core Fields
        if 'dublin_core' in results:
            with st.expander("📋 Enhanced Dublin Core", expanded=False):
                for field, value in results['dublin_core'].items():
                    if value:
                        st.write(f"**{field.title()}:** {value}")
    
    def _save_current_item(self):
        """Save current item data"""
        if not st.session_state.current_item_id:
            st.error("No item selected")
            return
        
        try:
            item_id = st.session_state.current_item_id
            collection = st.session_state.current_collection
            
            # Get metadata and processing results
            metadata = st.session_state.item_metadata.get(f"{collection}/{item_id}", {})
            processing_results = st.session_state.processing_results.get(item_id, {})
            
            # Save to CSV
            success = self.data_manager.save_item_csv(
                collection, item_id, metadata, processing_results
            )
            
            if success:
                st.success("✅ Item saved successfully!")
                self.processing_log.add_entry("SUCCESS", f"Saved {collection}/{item_id}")
            else:
                st.error("❌ Failed to save item")
                self.processing_log.add_entry("ERROR", f"Save failed for {collection}/{item_id}")
                
        except Exception as e:
            self.logger.error(f"Error saving item: {e}")
            st.error(f"Save error: {e}")
            self.processing_log.add_entry("ERROR", f"Save error: {e}")
    
    def _export_current_item(self):
        """Export current item as data package"""
        if not st.session_state.current_item_id:
            st.error("No item selected")
            return
        
        try:
            item_id = st.session_state.current_item_id
            collection = st.session_state.current_collection
            
            # Create data package
            zip_path = self.data_manager.create_item_package(collection, item_id)
            
            if zip_path and os.path.exists(zip_path):
                # Provide download link
                with open(zip_path, "rb") as file:
                    st.download_button(
                        label="📦 Download Item Package",
                        data=file.read(),
                        file_name=f"{collection}_{item_id}_metadata.zip",
                        mime="application/zip"
                    )
                st.success("✅ Export package created!")
                self.processing_log.add_entry("SUCCESS", f"Exported {collection}/{item_id}")
            else:
                st.error("❌ Failed to create export package")
                self.processing_log.add_entry("ERROR", f"Export failed for {collection}/{item_id}")
                
        except Exception as e:
            self.logger.error(f"Error exporting item: {e}")
            st.error(f"Export error: {e}")
            self.processing_log.add_entry("ERROR", f"Export error: {e}")
    
    def _process_collection(self):
        """Process entire collection in batch"""
        if not st.session_state.current_collection:
            st.error("No collection selected")
            return
        
        collection = st.session_state.current_collection
        
        try:
            with st.spinner("Starting batch processing..."):
                # Get collection items
                items = self.api.get_collection_items(collection)
                
                if not items:
                    st.error("No items found in collection")
                    return
                
                # Process items in batch
                total_items = len(items)
                progress_bar = st.progress(0)
                
                for i, item in enumerate(items):
                    item_id = str(item.get('pointer', ''))
                    
                    if item_id and item_id not in st.session_state.processing_results:
                        # Process item
                        image_data = self.api.get_image_data(collection, item_id)
                        if image_data:
                            results = self.ai_processor.process_item(
                                image_data, collection, item_id
                            )
                            if results:
                                st.session_state.processing_results[item_id] = results
                    
                    # Update progress
                    progress = (i + 1) / total_items
                    progress_bar.progress(progress)
                    st.session_state.batch_progress = progress
                
                st.success(f"✅ Processed {total_items} items from collection {collection}")
                self.processing_log.add_entry("SUCCESS", f"Batch processed collection {collection}")
                
        except Exception as e:
            self.logger.error(f"Error processing collection: {e}")
            st.error(f"Batch processing error: {e}")
            self.processing_log.add_entry("ERROR", f"Batch processing error: {e}")
    
    def _export_all(self):
        """Export all processed items"""
        try:
            if not st.session_state.processing_results:
                st.warning("No processed items to export")
                return
            
            with st.spinner("Creating collection export..."):
                # Create collection package
                zip_path = self.data_manager.create_collection_package(
                    st.session_state.current_collection or "mixed_collection",
                    st.session_state.processing_results
                )
                
                if zip_path and os.path.exists(zip_path):
                    # Provide download link
                    with open(zip_path, "rb") as file:
                        st.download_button(
                            label="📦 Download Collection Package",
                            data=file.read(),
                            file_name=f"collection_export_{st.session_state.current_collection}.zip",
                            mime="application/zip"
                        )
                    st.success("✅ Collection export created!")
                    self.processing_log.add_entry("SUCCESS", "Collection export completed")
                else:
                    st.error("❌ Failed to create collection export")
                    self.processing_log.add_entry("ERROR", "Collection export failed")
                    
        except Exception as e:
            self.logger.error(f"Error exporting all: {e}")
            st.error(f"Export error: {e}")
            self.processing_log.add_entry("ERROR", f"Export error: {e}")

def main():
    """Main application entry point"""
    try:
        app = ContentDMApp()
        app.run()
    except Exception as e:
        st.error(f"Application error: {e}")
        st.stop()

if __name__ == "__main__":
    main()
