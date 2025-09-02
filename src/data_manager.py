
"""
Data Management Module
Handles CSV export, JSON data packages, and file organization
"""

import logging
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import zipfile
import yaml
from datetime import datetime
import uuid
import csv

class DataManager:
    """Manages data export and packaging for ContentDM metadata"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.output_dir = Path(config.get('output_dir', 'outputs'))
        self.csv_encoding = config.get('csv_encoding', 'utf-8')
        self.include_thumbnails = config.get('include_thumbnails', True)
        self.zip_compression = config.get('zip_compression', True)
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def save_item_csv(self, collection: str, item_id: str, 
                     metadata: Dict[str, Any], 
                     ai_results: Dict[str, Any]) -> bool:
        """Save individual item data as CSV file"""
        try:
            import pandas as pd  # type: ignore
            # Create collection directory
            collection_dir = self.output_dir / collection
            collection_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{item_id}_{timestamp}.csv"
            csv_path = collection_dir / filename
            
            # Prepare data for CSV
            csv_data = self._prepare_csv_data(metadata, ai_results)
            
            # Write CSV file
            df = pd.DataFrame([csv_data])
            df.to_csv(csv_path, index=False, encoding=self.csv_encoding)
            
            self.logger.info(f"Saved CSV file: {csv_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving CSV for {collection}/{item_id}: {e}")
            return False
    
    def _prepare_csv_data(self, metadata: Dict[str, Any], 
                         ai_results: Dict[str, Any]) -> Dict[str, str]:
        """Prepare data for CSV export"""
        csv_data = {}
        
        # Original metadata fields
        if metadata:
            for key, value in metadata.items():
                if isinstance(value, (str, int, float)):
                    csv_data[f"original_{key}"] = str(value)
                elif isinstance(value, dict) and 'value' in value:
                    csv_data[f"original_{key}"] = str(value['value'])
                else:
                    csv_data[f"original_{key}"] = str(value)
        
        # AI generated fields
        if ai_results:
            if 'description' in ai_results:
                csv_data['ai_description'] = ai_results['description']
            
            if 'transcription' in ai_results:
                csv_data['ai_transcription'] = ai_results['transcription']
            
            if 'entities' in ai_results:
                # Flatten entities data
                entity_texts = []
                entity_types = []
                entity_uris = []
                
                for entity in ai_results['entities']:
                    entity_texts.append(entity.get('text', ''))
                    entity_types.append(entity.get('label', ''))
                    
                    uris = []
                    if entity.get('wikidata_uri'):
                        uris.append(entity['wikidata_uri'])
                    if entity.get('dbpedia_uri'):
                        uris.append(entity['dbpedia_uri'])
                    entity_uris.append(' | '.join(uris))
                
                csv_data['ai_entities'] = ' | '.join(entity_texts)
                csv_data['ai_entity_types'] = ' | '.join(entity_types)
                csv_data['ai_entity_uris'] = ' | '.join(entity_uris)
            
            if 'dublin_core' in ai_results:
                for dc_field, dc_value in ai_results['dublin_core'].items():
                    csv_data[f'dc_{dc_field}'] = str(dc_value)
        
        # Add processing metadata
        csv_data['processed_date'] = datetime.now().isoformat()
        csv_data['processing_id'] = str(uuid.uuid4())
        
        return csv_data
    
    def create_item_package(self, collection: str, item_id: str) -> Optional[str]:
        """Create data package for single item"""
        try:
            # Find CSV file for item
            collection_dir = self.output_dir / collection
            csv_files = list(collection_dir.glob(f"{item_id}_*.csv"))
            
            if not csv_files:
                self.logger.error(f"No CSV file found for {collection}/{item_id}")
                return None
            
            csv_file = csv_files[0]  # Use most recent
            
            # Create package directory
            package_dir = self.output_dir / "packages" / f"{collection}_{item_id}"
            package_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy CSV file
            package_csv = package_dir / f"{item_id}_metadata.csv"
            import shutil
            shutil.copy2(csv_file, package_csv)
            
            # Create data package JSON
            package_json = self._create_datapackage_json(
                title=f"ContentDM Item {collection}/{item_id}",
                description=f"AI-enhanced metadata for ContentDM item {item_id} from collection {collection}",
                resources=[{
                    "name": f"{item_id}_metadata",
                    "path": f"{item_id}_metadata.csv",
                    "title": f"Metadata for item {item_id}",
                    "description": "Combined original and AI-generated metadata"
                }]
            )
            
            # Save package JSON
            package_json_path = package_dir / "datapackage.json"
            with open(package_json_path, 'w', encoding='utf-8') as f:
                json.dump(package_json, f, indent=2, ensure_ascii=False)
            
            # Create README
            readme_content = self._create_readme(collection, [item_id])
            readme_path = package_dir / "README.md"
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            # Create ZIP package
            if self.zip_compression:
                zip_path = package_dir.with_suffix('.zip')
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for file_path in package_dir.rglob('*'):
                        if file_path.is_file():
                            arc_name = file_path.relative_to(package_dir)
                            zf.write(file_path, arc_name)
                
                # Clean up directory
                shutil.rmtree(package_dir)
                
                self.logger.info(f"Created item package: {zip_path}")
                return str(zip_path)
            else:
                self.logger.info(f"Created item package directory: {package_dir}")
                return str(package_dir)
                
        except Exception as e:
            self.logger.error(f"Error creating item package for {collection}/{item_id}: {e}")
            return None
    
    def create_collection_package(self, collection: str, 
                                processing_results: Dict[str, Dict[str, Any]]) -> Optional[str]:
        """Create data package for entire collection"""
        try:
            import pandas as pd  # type: ignore
            # Create package directory
            package_dir = self.output_dir / "packages" / f"collection_{collection}"
            package_dir.mkdir(parents=True, exist_ok=True)
            
            # Create data directory
            data_dir = package_dir / "data"
            data_dir.mkdir(exist_ok=True)
            
            # Process each item
            resources = []
            item_ids = []
            
            for item_key, ai_results in processing_results.items():
                if '/' in item_key:
                    item_collection, item_id = item_key.split('/', 1)
                    if item_collection == collection:
                        item_ids.append(item_id)
                        
                        # Create CSV for item
                        csv_filename = f"{item_id}_metadata.csv"
                        csv_path = data_dir / csv_filename
                        
                        # Get original metadata if available (from session state or API)
                        metadata = {}  # You might want to pass this in
                        
                        csv_data = self._prepare_csv_data(metadata, ai_results)
                        df = pd.DataFrame([csv_data])
                        df.to_csv(csv_path, index=False, encoding=self.csv_encoding)
                        
                        # Add to resources
                        resources.append({
                            "name": f"{item_id}_metadata",
                            "path": f"data/{csv_filename}",
                            "title": f"Metadata for item {item_id}",
                            "description": f"AI-enhanced metadata for ContentDM item {item_id}"
                        })
            
            # Create combined CSV with all items
            if item_ids:
                combined_csv_path = data_dir / f"{collection}_combined_metadata.csv"
                self._create_combined_csv(data_dir, combined_csv_path)
                
                resources.append({
                    "name": f"{collection}_combined",
                    "path": f"data/{collection}_combined_metadata.csv",
                    "title": f"Combined metadata for collection {collection}",
                    "description": f"All items from collection {collection} in single file"
                })
            
            # Create data package JSON
            package_json = self._create_datapackage_json(
                title=f"ContentDM Collection {collection}",
                description=f"AI-enhanced metadata for ContentDM collection {collection}",
                resources=resources
            )
            
            # Save package JSON
            package_json_path = package_dir / "datapackage.json"
            with open(package_json_path, 'w', encoding='utf-8') as f:
                json.dump(package_json, f, indent=2, ensure_ascii=False)
            
            # Create README
            readme_content = self._create_readme(collection, item_ids)
            readme_path = package_dir / "README.md"
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            # Create ZIP package
            if self.zip_compression:
                zip_path = package_dir.with_suffix('.zip')
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for file_path in package_dir.rglob('*'):
                        if file_path.is_file():
                            arc_name = file_path.relative_to(package_dir)
                            zf.write(file_path, arc_name)
                
                # Clean up directory
                import shutil
                shutil.rmtree(package_dir)
                
                self.logger.info(f"Created collection package: {zip_path}")
                return str(zip_path)
            else:
                self.logger.info(f"Created collection package directory: {package_dir}")
                return str(package_dir)
                
        except Exception as e:
            self.logger.error(f"Error creating collection package for {collection}: {e}")
            return None
    
    def _create_combined_csv(self, data_dir: Path, output_path: Path):
        """Combine all CSV files in directory into one"""
        try:
            import pandas as pd  # type: ignore
            csv_files = list(data_dir.glob("*_metadata.csv"))
            if not csv_files:
                return
            
            # Read all CSV files
            dfs = []
            for csv_file in csv_files:
                df = pd.read_csv(csv_file, encoding=self.csv_encoding)
                dfs.append(df)
            
            # Combine into single DataFrame
            combined_df = pd.concat(dfs, ignore_index=True, sort=False)
            
            # Save combined CSV
            combined_df.to_csv(output_path, index=False, encoding=self.csv_encoding)
            
            self.logger.info(f"Created combined CSV with {len(combined_df)} records")
            
        except Exception as e:
            self.logger.error(f"Error creating combined CSV: {e}")
    
    def _create_datapackage_json(self, title: str, description: str, 
                               resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create data package JSON following Frictionless Data standard"""
        
        # Enhance resources with table schema
        enhanced_resources = []
        for resource in resources:
            enhanced_resource = resource.copy()
            
            if resource['path'].endswith('.csv'):
                # Add CSV table schema
                enhanced_resource.update({
                    "format": "csv",
                    "mediatype": "text/csv",
                    "encoding": self.csv_encoding,
                    "profile": "tabular-data-resource",
                    "schema": self._get_table_schema()
                })
            
            enhanced_resources.append(enhanced_resource)
        
        package = {
            "profile": "data-package",
            "name": title.lower().replace(' ', '_').replace('/', '_'),
            "title": title,
            "description": description,
            "version": "1.0.0",
            "created": datetime.now().isoformat(),
            "keywords": ["contentdm", "metadata", "ai", "cultural-heritage"],
            "contributors": [
                {
                    "title": "ContentDM AI Metadata Generator",
                    "role": "author"
                }
            ],
            "resources": enhanced_resources,
            "sources": [
                {
                    "title": "ContentDM Digital Collection",
                    "web": "https://vu.contentdm.oclc.org"
                }
            ]
        }
        
        return package
    
    def _get_table_schema(self) -> Dict[str, Any]:
        """Generate table schema for CSV files"""
        
        # Define common fields
        fields = [
            {"name": "processing_id", "type": "string", "description": "Unique processing identifier"},
            {"name": "processed_date", "type": "datetime", "description": "Date and time of processing"},
            {"name": "ai_description", "type": "string", "description": "AI-generated image description"},
            {"name": "ai_transcription", "type": "string", "description": "OCR extracted text"},
            {"name": "ai_entities", "type": "string", "description": "Named entities found in content"},
            {"name": "ai_entity_types", "type": "string", "description": "Types of named entities"},
            {"name": "ai_entity_uris", "type": "string", "description": "Linked data URIs for entities"},
            {"name": "dc_description", "type": "string", "description": "Enhanced Dublin Core description"},
            {"name": "dc_subject", "type": "string", "description": "Enhanced Dublin Core subjects"},
            {"name": "dc_subject_uris", "type": "string", "description": "Linked data URIs for subjects"},
            {"name": "dc_type", "type": "string", "description": "Dublin Core type classification"},
            {"name": "dc_coverage", "type": "string", "description": "Dublin Core coverage (locations)"}
        ]
        
        schema = {
            "fields": fields,
            "missingValues": [""],
            "primaryKey": ["processing_id"]
        }
        
        return schema
    
    def _create_readme(self, collection: str, item_ids: List[str]) -> str:
        """Create README content for data package"""
        
        readme = f"""# ContentDM AI Metadata Generator - Collection {collection}

## Overview

This data package contains AI-enhanced metadata for items from ContentDM collection `{collection}`.

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Items processed:** {len(item_ids)}

## Contents

### Data Files

- Individual CSV files for each processed item
- Combined CSV file with all items (if applicable)
- JSON data package descriptor (datapackage.json)

### Processing Details

The metadata enhancement process includes:

1. **Image Captioning**: AI-generated descriptions using BLIP model
2. **OCR Text Extraction**: Optical character recognition for text content
3. **Named Entity Recognition**: Identification of people, places, organizations
4. **Linked Data Integration**: URIs from Wikidata and DBpedia
5. **Dublin Core Enhancement**: Improved metadata following DC standards

### Field Descriptions

#### Original ContentDM Fields
Fields prefixed with `original_` contain data from the ContentDM API.

#### AI-Generated Fields
- `ai_description`: Generated image caption
- `ai_transcription`: Extracted text via OCR
- `ai_entities`: Named entities found (pipe-separated)
- `ai_entity_types`: Entity types (PERSON, ORG, LOC, etc.)
- `ai_entity_uris`: Linked data URIs (pipe-separated)

#### Dublin Core Fields
- `dc_description`: Enhanced description field
- `dc_subject`: Subject terms with entities
- `dc_subject_uris`: Linked data URIs for subjects
- `dc_type`: Resource type classification
- `dc_coverage`: Geographic coverage from entities

### Usage

This data follows the [Frictionless Data](https://datapackage.org/) standard and can be:

- Imported into spreadsheet applications
- Processed with pandas: `pd.read_csv('filename.csv')`
- Validated with frictionless-py tools
- Integrated with DPLA, Omeka, or other platforms

### License

Data is provided under the same terms as the original ContentDM collection.

### Citation

Please cite as:
> ContentDM AI Metadata Generator. Enhanced metadata for collection {collection}. Generated {datetime.now().strftime('%Y-%m-%d')}.

---

Generated by ContentDM AI Metadata Generator v1.0
"""
        
        return readme
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get statistics about processed items"""
        try:
            stats = {
                'total_collections': 0,
                'total_items': 0,
                'collections': {}
            }
            
            # Count files by collection
            for collection_dir in self.output_dir.iterdir():
                if collection_dir.is_dir() and collection_dir.name != 'packages':
                    collection_name = collection_dir.name
                    csv_files = list(collection_dir.glob("*.csv"))
                    
                    stats['collections'][collection_name] = len(csv_files)
                    stats['total_items'] += len(csv_files)
            
            stats['total_collections'] = len(stats['collections'])
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting processing stats: {e}")
            return {}
    
    def cleanup_old_files(self, days: int = 30):
        """Clean up files older than specified days"""
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days)
            removed_count = 0
            
            for file_path in self.output_dir.rglob("*"):
                if file_path.is_file():
                    file_date = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_date < cutoff_date:
                        file_path.unlink()
                        removed_count += 1
            
            self.logger.info(f"Cleaned up {removed_count} old files")
            return removed_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old files: {e}")
            return 0
