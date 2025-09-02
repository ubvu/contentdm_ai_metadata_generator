
"""
AI Processing Module
Handles image captioning, OCR, and Named Entity Recognition with linked data
"""

import logging
from typing import Dict, List, Optional, Any, Callable, Tuple
from PIL import Image
import requests
import json
try:
    from SPARQLWrapper import SPARQLWrapper, JSON  # type: ignore
except Exception:
    SPARQLWrapper = None  # type: ignore
    JSON = None  # type: ignore
import re
import time

class AIProcessor:
    """AI processing pipeline for image analysis and metadata enhancement"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Model states
        self.models_loaded = False
        self.blip_processor = None
        self.blip_model = None
        self.nlp = None
        
        # Configuration
        self.image_config = config.get('image_captioning', {})
        self.ocr_config = config.get('ocr', {})
        self.ner_config = config.get('ner', {})
        
        # Device configuration
        self.device = self._get_device()
        
        # SPARQL endpoints for linked data
        self.wikidata_endpoint = "https://query.wikidata.org/sparql"
        self.dbpedia_endpoint = "http://dbpedia.org/sparql"
    
    def _get_device(self):
        """Determine the best available device for processing"""
        device_config = self.image_config.get('device', 'auto')
        
        if device_config == 'auto':
            # Lazy import torch to avoid hard dependency at import time
            try:
                import torch  # type: ignore
                if torch.cuda.is_available():
                    device = 'cuda'
                    self.logger.info("Using CUDA GPU for AI processing")
                else:
                    device = 'cpu'
                    self.logger.info("Using CPU for AI processing")
            except Exception:
                # Torch not available; fall back to CPU gracefully
                device = 'cpu'
                self.logger.info("Torch not available; defaulting to CPU")
        else:
            device = device_config
            self.logger.info(f"Using configured device: {device}")
        
        return device
    
    def initialize_models(self) -> bool:
        """Initialize all AI models"""
        try:
            self.logger.info("Initializing AI models...")
            
            # Initialize BLIP model for image captioning
            success = self._initialize_blip()
            if not success:
                return False
            
            # Initialize spaCy model for NER
            success = self._initialize_spacy()
            if not success:
                return False
            
            self.models_loaded = True
            self.logger.info("All AI models initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing AI models: {e}")
            return False
    
    def _initialize_blip(self) -> bool:
        """Initialize BLIP model for image captioning"""
        try:
            model_name = self.image_config.get('model_name', 'Salesforce/blip-image-captioning-base')
            
            self.logger.info(f"Loading BLIP model: {model_name}")
            
            # Lazy import heavy deps
            try:
                from transformers import BlipProcessor, BlipForConditionalGeneration  # type: ignore
            except Exception as e:
                self.logger.error(f"transformers library not available: {e}")
                return False

            try:
                import torch  # type: ignore
            except Exception:
                torch = None  # type: ignore

            self.blip_processor = BlipProcessor.from_pretrained(model_name)
            self.blip_model = BlipForConditionalGeneration.from_pretrained(model_name)
            
            # Move model to device
            try:
                if self.device == 'cuda' and hasattr(torch, 'cuda') and torch.cuda.is_available():  # type: ignore[attr-defined]
                    self.blip_model = self.blip_model.to('cuda')
            except Exception:
                # If torch is missing or CUDA not available, continue on CPU
                pass
            
            self.logger.info("BLIP model loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing BLIP model: {e}")
            return False
    
    def _initialize_spacy(self) -> bool:
        """Initialize spaCy model for NER"""
        try:
            model_name = self.ner_config.get('model', 'en_core_web_sm')
            
            self.logger.info(f"Loading spaCy model: {model_name}")
            
            # Try to load the model
            try:
                import spacy  # type: ignore
                self.nlp = spacy.load(model_name)
            except OSError:
                # Model not found, try to download it
                self.logger.warning(f"spaCy model {model_name} not found, attempting to download...")
                import subprocess
                result = subprocess.run(['python', '-m', 'spacy', 'download', model_name], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    import spacy  # type: ignore
                    self.nlp = spacy.load(model_name)
                else:
                    self.logger.error(f"Failed to download spaCy model: {result.stderr}")
                    return False
            
            self.logger.info("spaCy model loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing spaCy model: {e}")
            return False
    
    def process_item(self, image: Image.Image, collection: str, item_id: str,
                    callback: Optional[Callable[[str], None]] = None) -> Optional[Dict[str, Any]]:
        """Process a single item with all AI techniques"""
        
        if not self.models_loaded:
            self.logger.error("AI models not loaded")
            return None
        
        try:
            if callback:
                callback(f"Starting AI processing for {collection}/{item_id}")
            
            results = {}
            
            # 1. Image Captioning
            if callback:
                callback("Generating image description...")
            description = self.generate_description(image)
            if description:
                results['description'] = description
            
            # 2. OCR Text Extraction
            if callback:
                callback("Extracting text via OCR...")
            transcription = self.extract_text(image)
            if transcription:
                results['transcription'] = transcription
            
            # 3. Named Entity Recognition
            if callback:
                callback("Processing named entities...")
            
            # Combine description and transcription for NER
            text_for_ner = []
            if description:
                text_for_ner.append(description)
            if transcription:
                text_for_ner.append(transcription)
            
            combined_text = " ".join(text_for_ner)
            
            if combined_text:
                entities = self.extract_entities(combined_text)
                if entities:
                    results['entities'] = entities
            
            # 4. Generate Enhanced Dublin Core
            if callback:
                callback("Generating Dublin Core metadata...")
            dublin_core = self.generate_dublin_core(results)
            if dublin_core:
                results['dublin_core'] = dublin_core
            
            if callback:
                callback(f"AI processing completed for {collection}/{item_id}")
            
            self.logger.info(f"Successfully processed item {collection}/{item_id}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing item {collection}/{item_id}: {e}")
            if callback:
                callback(f"Error processing item: {e}")
            return None
    
    def generate_description(self, image: Image.Image) -> Optional[str]:
        """Generate image caption using BLIP"""
        try:
            if not self.blip_model or not self.blip_processor:
                self.logger.error("BLIP model not initialized")
                return None
            
            # Preprocess image
            inputs = self.blip_processor(image, return_tensors="pt")
            
            # Move to device
            if self.device == 'cuda':
                try:
                    inputs = {k: v.to('cuda') for k, v in inputs.items()}
                except Exception:
                    # If CUDA not available, keep on CPU
                    pass
            
            # Generate caption
            try:
                import torch  # type: ignore
                ctx = torch.no_grad()
            except Exception:
                import contextlib
                ctx = contextlib.nullcontext()

            with ctx:
                out = self.blip_model.generate(
                    **inputs,
                    max_length=self.image_config.get('max_length', 100),
                    num_beams=self.image_config.get('num_beams', 4),
                    do_sample=True,
                    temperature=0.7
                )
            
            # Decode caption
            caption = self.blip_processor.decode(out[0], skip_special_tokens=True)
            
            self.logger.info(f"Generated image caption: {caption}")
            return caption
            
        except Exception as e:
            self.logger.error(f"Error generating image description: {e}")
            return None
    
    def extract_text(self, image: Image.Image) -> Optional[str]:
        """Extract text from image using OCR"""
        try:
            # Lazy import OCR dependencies
            try:
                import numpy as np  # type: ignore
                import cv2  # type: ignore
                import pytesseract  # type: ignore
            except Exception as e:
                self.logger.warning(f"OCR dependencies not available: {e}")
                return None

            # Convert PIL image to numpy array for OpenCV
            img_array = np.array(image)
            
            # Convert RGB to BGR for OpenCV
            if len(img_array.shape) == 3 and img_array.shape[2] == 3:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # Preprocess image for better OCR
            gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY) if len(img_array.shape) == 3 else img_array
            
            # Apply denoising
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Apply threshold to get better contrast
            _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Extract text using Tesseract
            ocr_config = self.ocr_config.get('config', '--psm 6')
            lang = self.ocr_config.get('lang', 'eng')
            
            text = pytesseract.image_to_string(
                thresh,
                lang=lang,
                config=ocr_config
            )
            
            # Clean extracted text
            text = self._clean_ocr_text(text)
            
            if text and len(text.strip()) > 0:
                self.logger.info(f"Extracted text: {text[:100]}...")
                return text
            else:
                self.logger.info("No text extracted from image")
                return None
                
        except Exception as e:
            self.logger.error(f"Error extracting text from image: {e}")
            return None
    
    def _clean_ocr_text(self, text: str) -> str:
        """Clean OCR extracted text"""
        if not text:
            return ""
        
        # Remove extra whitespace and empty lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        cleaned_text = ' '.join(lines)
        
        # Remove multiple spaces
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        
        return cleaned_text.strip()
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities and link to Wikidata/DBpedia"""
        try:
            if not self.nlp:
                self.logger.error("spaCy model not initialized")
                return []
            
            # Process text with spaCy
            doc = self.nlp(text)
            
            entities = []
            confidence_threshold = self.ner_config.get('confidence_threshold', 0.7)
            
            for ent in doc.ents:
                # Basic entity info
                entity_info = {
                    'text': ent.text,
                    'label': ent.label_,
                    'description': spacy.explain(ent.label_),
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'confidence': getattr(ent, 'confidence', 0.8)  # Default confidence
                }
                
                # Skip low confidence entities
                if entity_info['confidence'] < confidence_threshold:
                    continue
                
                # Add linked data URIs
                if self.ner_config.get('enable_wikidata', True):
                    wikidata_uri = self._get_wikidata_uri(ent.text, ent.label_)
                    if wikidata_uri:
                        entity_info['wikidata_uri'] = wikidata_uri
                
                if self.ner_config.get('enable_dbpedia', True):
                    dbpedia_uri = self._get_dbpedia_uri(ent.text, ent.label_)
                    if dbpedia_uri:
                        entity_info['dbpedia_uri'] = dbpedia_uri
                
                entities.append(entity_info)
            
            self.logger.info(f"Extracted {len(entities)} named entities")
            return entities
            
        except Exception as e:
            self.logger.error(f"Error extracting entities: {e}")
            return []
    
    def _get_wikidata_uri(self, entity_text: str, entity_type: str) -> Optional[str]:
        """Get Wikidata URI for entity using SPARQL"""
        try:
            if SPARQLWrapper is None:
                return None
            sparql = SPARQLWrapper(self.wikidata_endpoint)
            if JSON is not None:
                sparql.setReturnFormat(JSON)
            
            # Construct SPARQL query based on entity type
            if entity_type in ['PERSON']:
                query = f"""
                SELECT ?item ?itemLabel WHERE {{
                  ?item rdfs:label "{entity_text}"@en .
                  ?item wdt:P31 wd:Q5 .
                  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
                }}
                LIMIT 1
                """
            elif entity_type in ['GPE', 'LOC']:  # Places
                query = f"""
                SELECT ?item ?itemLabel WHERE {{
                  ?item rdfs:label "{entity_text}"@en .
                  {{ ?item wdt:P31 wd:Q515 }} UNION {{ ?item wdt:P31 wd:Q6256 }} .
                  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
                }}
                LIMIT 1
                """
            elif entity_type in ['ORG']:  # Organizations
                query = f"""
                SELECT ?item ?itemLabel WHERE {{
                  ?item rdfs:label "{entity_text}"@en .
                  ?item wdt:P31/wdt:P279* wd:Q43229 .
                  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
                }}
                LIMIT 1
                """
            else:
                # Generic search
                query = f"""
                SELECT ?item ?itemLabel WHERE {{
                  ?item rdfs:label "{entity_text}"@en .
                  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
                }}
                LIMIT 1
                """
            
            sparql.setQuery(query)
            
            try:
                results = sparql.query().convert()
                if results['results']['bindings']:
                    uri = results['results']['bindings'][0]['item']['value']
                    self.logger.debug(f"Found Wikidata URI for '{entity_text}': {uri}")
                    return uri
            except Exception as query_error:
                self.logger.debug(f"Wikidata query failed for '{entity_text}': {query_error}")
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error getting Wikidata URI for '{entity_text}': {e}")
            return None
    
    def _get_dbpedia_uri(self, entity_text: str, entity_type: str) -> Optional[str]:
        """Get DBpedia URI for entity"""
        try:
            # Use DBpedia Spotlight for entity linking
            url = "https://api.dbpedia-spotlight.org/en/annotate"
            
            params = {
                'text': entity_text,
                'confidence': 0.5,
                'support': 20
            }
            
            headers = {
                'Accept': 'application/json'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'Resources' in data and data['Resources']:
                    uri = data['Resources'][0]['@URI']
                    self.logger.debug(f"Found DBpedia URI for '{entity_text}': {uri}")
                    return uri
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error getting DBpedia URI for '{entity_text}': {e}")
            return None
    
    def generate_dublin_core(self, ai_results: Dict[str, Any]) -> Dict[str, str]:
        """Generate enhanced Dublin Core metadata from AI results"""
        try:
            dublin_core = {}
            
            # Description field
            descriptions = []
            if 'description' in ai_results:
                descriptions.append(ai_results['description'])
            
            # Add entity-based descriptions
            if 'entities' in ai_results:
                entity_descriptions = []
                for entity in ai_results['entities']:
                    if entity.get('description'):
                        entity_descriptions.append(f"{entity['text']} ({entity['description']})")
                
                if entity_descriptions:
                    descriptions.append("Contains: " + ", ".join(entity_descriptions))
            
            if descriptions:
                dublin_core['description'] = " | ".join(descriptions)
            
            # Subject field - use extracted entities
            if 'entities' in ai_results:
                subjects = []
                subject_uris = []
                
                for entity in ai_results['entities']:
                    subjects.append(entity['text'])
                    
                    # Add linked data URIs
                    if entity.get('wikidata_uri'):
                        subject_uris.append(entity['wikidata_uri'])
                    if entity.get('dbpedia_uri'):
                        subject_uris.append(entity['dbpedia_uri'])
                
                if subjects:
                    dublin_core['subject'] = " | ".join(subjects)
                
                if subject_uris:
                    dublin_core['subject_uris'] = " | ".join(subject_uris)
            
            # Type field - infer from content
            if 'description' in ai_results:
                desc = ai_results['description'].lower()
                if any(word in desc for word in ['photograph', 'photo', 'picture']):
                    dublin_core['type'] = 'Image;Photograph'
                elif any(word in desc for word in ['painting', 'artwork', 'art']):
                    dublin_core['type'] = 'Image;Artwork'
                elif any(word in desc for word in ['document', 'text', 'manuscript']):
                    dublin_core['type'] = 'Text'
                else:
                    dublin_core['type'] = 'Image'
            
            # Coverage - extract locations from entities
            if 'entities' in ai_results:
                locations = []
                for entity in ai_results['entities']:
                    if entity['label'] in ['GPE', 'LOC']:
                        locations.append(entity['text'])
                
                if locations:
                    dublin_core['coverage'] = " | ".join(locations)
            
            self.logger.info(f"Generated Dublin Core metadata with {len(dublin_core)} fields")
            return dublin_core
            
        except Exception as e:
            self.logger.error(f"Error generating Dublin Core metadata: {e}")
            return {}
    
    def batch_process_items(self, items: List[Tuple[Image.Image, str, str]], 
                          callback: Optional[Callable[[str], None]] = None) -> Dict[str, Dict[str, Any]]:
        """Process multiple items in batch"""
        results = {}
        
        try:
            total_items = len(items)
            
            for i, (image, collection, item_id) in enumerate(items):
                if callback:
                    callback(f"Processing item {i+1}/{total_items}: {collection}/{item_id}")
                
                item_results = self.process_item(image, collection, item_id, callback)
                if item_results:
                    results[f"{collection}/{item_id}"] = item_results
                
                # Add small delay to prevent overwhelming the system
                time.sleep(0.1)
            
            self.logger.info(f"Batch processed {len(results)} items successfully")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in batch processing: {e}")
            return results
    
    def cleanup_models(self):
        """Clean up loaded models to free memory"""
        try:
            if hasattr(self, 'blip_model') and self.blip_model:
                del self.blip_model
                self.blip_model = None
            
            if hasattr(self, 'blip_processor') and self.blip_processor:
                del self.blip_processor
                self.blip_processor = None
            
            try:
                import torch  # type: ignore
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass
            
            self.models_loaded = False
            self.logger.info("AI models cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up models: {e}")
