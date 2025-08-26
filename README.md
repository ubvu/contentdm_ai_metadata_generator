
# ContentDM AI Metadata Generator

An intelligent Streamlit application that generates enhanced metadata for ContentDM digital collections using AI technologies including image captioning, OCR, and Named Entity Recognition with linked data.

## 🚀 Features

### Core Functionality
- **Integrated ContentDM Browser**: 80/20 split layout with embedded ContentDM website
- **Automatic Item Detection**: Monitors URL changes to detect item detail pages (`/id/` pattern)
- **AI-Powered Processing**: Generates descriptions, extracts text, and identifies entities
- **Linked Data Integration**: Connects entities to Wikidata and DBpedia URIs
- **Data Export System**: Creates CSV files and JSON data packages following Frictionless Data standards

### AI Processing Pipeline
1. **Image Captioning**: Uses BLIP model for automatic image description
2. **OCR Text Extraction**: Tesseract-based text extraction from images
3. **Named Entity Recognition**: spaCy NER with Wikidata/DBpedia linking
4. **Dublin Core Enhancement**: Generates enhanced DC metadata fields

### Data Management
- Individual CSV files per processed item (named with record ID + timestamp)
- Collection-based folder organization
- JSON data package standard compliance
- ZIP export for collections with metadata and documentation
- Batch processing capabilities with progress tracking

## 📦 Installation

### Prerequisites
- Python 3.9+
- Docker (optional but recommended)
- Tesseract OCR
- Git

### Local Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/contentdm-ai-generator.git
   cd contentdm-ai-generator
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download spaCy model**
   ```bash
   python -m spacy download en_core_web_sm
   ```

5. **Configure application**
   ```bash
   cp config.example.yaml config.yaml
   # Edit config.yaml with your settings
   ```

6. **Run the application**
   ```bash
   streamlit run app.py
   ```

### Docker Installation

1. **Clone and configure**
   ```bash
   git clone https://github.com/your-username/contentdm-ai-generator.git
   cd contentdm-ai-generator
   cp config.example.yaml config.yaml
   ```

2. **Build and run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

3. **Access the application**
   - Open http://localhost:8501 in your browser

### Production Deployment

For production deployment with nginx reverse proxy:

```bash
docker-compose --profile production up -d
```

## ⚙️ Configuration

### Basic Configuration (`config.yaml`)

```yaml
contentdm:
  base_url: "https://vu.contentdm.oclc.org"
  api_endpoint: "/digital/bl/dmwebservices/index.php"
  default_collection: "vko"
  timeout: 30

ai_models:
  image_captioning:
    model_name: "Salesforce/blip-image-captioning-base"
    device: "auto"  # auto, cpu, cuda
  
  ner:
    model: "en_core_web_sm"
    enable_wikidata: true
    enable_dbpedia: true
    confidence_threshold: 0.7

export:
  output_dir: "outputs"
  csv_encoding: "utf-8"
  zip_compression: true
```

### Environment Variables

Key environment variables for Docker deployment:

- `CONTENTDM_BASE_URL`: Override ContentDM base URL
- `AI_DEVICE`: Force CPU/GPU usage (`cpu`, `cuda`, `auto`)
- `OUTPUT_DIR`: Custom output directory path
- `LOG_LEVEL`: Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`)

## 📖 Usage Guide

### Basic Workflow

1. **Start the application** and navigate to the ContentDM browser
2. **Browse to an item detail page** (URL containing `/id/`)
3. **Load AI models** using the "Load AI Models" button
4. **Generate metadata** with "Auto Generate Additional Metadata"
5. **Review results** in the expandable sections
6. **Save or export** the enhanced metadata

### Navigation Options

- **Manual URL Entry**: Enter ContentDM URLs directly
- **Quick Navigation**: Use browse, search, and home buttons
- **History**: Access recently visited items

### Processing Results

The application generates:
- **Object Description**: AI-generated image caption
- **Text Transcription**: OCR-extracted text content
- **Named Entities**: People, places, organizations with confidence scores
- **Linked Data URIs**: Wikidata and DBpedia links
- **Enhanced Dublin Core**: Improved DC metadata fields

### Data Export Options

1. **Single Item Export**
   - CSV file with combined metadata
   - JSON data package with schema
   - README documentation

2. **Collection Export**
   - Individual CSV files per item
   - Combined collection CSV
   - ZIP package with metadata

### Batch Processing

For processing entire collections:

1. Navigate to any item in the target collection
2. Click "Process Collection" to start batch processing
3. Monitor progress in the processing log
4. Use "Export All" to create collection package

## 🔧 API Integration

### ContentDM API Endpoints Used

- `dmGetItemInfo`: Fetch item metadata
- `dmGetImageInfo`: Get image technical metadata
- `dmGetFile`: Download image files
- `dmQuery`: Search and browse collections
- `dmGetCollectionInfo`: Collection metadata

### Supported URL Patterns

The application detects ContentDM item pages from URLs like:
- `https://site.contentdm.oclc.org/digital/collection/alias/id/123`
- `https://site.contentdm.oclc.org/alias/id/123`
- Query parameter formats with `collection=` and `id=`

## 🤖 AI Models

### Image Captioning
- **Model**: Salesforce BLIP (Bootstrapping Language-Image Pre-training)
- **Purpose**: Generate descriptive captions for images
- **Output**: Natural language descriptions of visual content

### OCR Processing
- **Engine**: Tesseract OCR
- **Languages**: Configurable (default: English)
- **Preprocessing**: Denoising, contrast enhancement, binarization

### Named Entity Recognition
- **Model**: spaCy English model (`en_core_web_sm`)
- **Entities**: PERSON, ORG, GPE, LOC, DATE, etc.
- **Linking**: Automatic linking to Wikidata and DBpedia

### Performance Optimization
- **GPU Support**: Automatic CUDA detection for image processing
- **Caching**: Model and result caching for improved performance
- **Batch Processing**: Efficient processing of multiple items

## 📊 Data Standards

### CSV Output Format

Each processed item generates a CSV with these field categories:

- `original_*`: Fields from ContentDM API
- `ai_*`: AI-generated content and analysis
- `dc_*`: Enhanced Dublin Core fields
- `processing_*`: Metadata about the processing

### JSON Data Package

Follows the [Frictionless Data](https://datapackage.org/) standard:
- `datapackage.json`: Package descriptor with schema
- Table schema definitions for CSV files
- Resource metadata and relationships
- Contributor and source information

### Linked Data Integration

- **Wikidata URIs**: `http://www.wikidata.org/entity/Q*`
- **DBpedia URIs**: `http://dbpedia.org/resource/*`
- **SPARQL Queries**: Automatic entity resolution
- **Confidence Scoring**: Quality metrics for linked entities

## 🐛 Troubleshooting

### Common Issues

1. **AI Models Won't Load**
   ```bash
   # Check available memory and disk space
   df -h
   free -h
   
   # For CUDA issues:
   nvidia-smi
   ```

2. **ContentDM API Timeouts**
   ```yaml
   # Increase timeout in config.yaml
   contentdm:
     timeout: 60
     max_retries: 5
   ```

3. **OCR Not Working**
   ```bash
   # Install/reinstall Tesseract
   sudo apt-get install tesseract-ocr tesseract-ocr-eng
   ```

4. **Permission Errors**
   ```bash
   # Fix output directory permissions
   sudo chown -R $USER:$USER outputs/
   chmod -R 755 outputs/
   ```

### Performance Optimization

- **Memory Usage**: Use CPU-only mode for limited RAM: `device: "cpu"`
- **Processing Speed**: Reduce batch size: `batch_size: 5`
- **Storage**: Enable cleanup of old files: Set retention policies

### Logging

Check application logs for detailed error information:
```bash
tail -f contentdm_ai.log
```

For Docker deployments:
```bash
docker-compose logs -f contentdm-ai
```

## 🔒 Security Considerations

### Data Privacy
- All processing occurs locally or in your controlled environment
- No data sent to external AI services
- ContentDM API calls only to configured endpoints

### Network Security
- Configure firewall rules for production deployment
- Use HTTPS in production (nginx configuration provided)
- Implement authentication if needed (external auth proxy)

### Content Security
- iframe restrictions apply to ContentDM embedding
- CORS and XSRF protections configurable
- Input validation for all user-provided URLs

## 🤝 Contributing

### Development Setup

1. **Fork the repository** and clone your fork
2. **Create development branch**: `git checkout -b feature/your-feature`
3. **Install dev dependencies**: `pip install -r requirements-dev.txt`
4. **Make changes** and test thoroughly
5. **Submit pull request** with detailed description

### Code Standards
- Follow PEP 8 Python style guidelines
- Add type hints for new functions
- Include docstrings for public methods
- Write tests for new functionality

### Testing

```bash
# Run tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=src tests/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📚 Citation

If you use this software in research or academic work, please cite:

```bibtex
@software{contentdm_ai_generator,
  title = {ContentDM AI Metadata Generator},
  author = {Vanderfeesten, Maurice},
  year = {2024},
  url = {https://github.com/your-username/contentdm-ai-generator},
  doi = {10.5281/zenodo.XXXXXX}
}
```

## 🙋 Support

### Documentation
- [ContentDM API Reference](https://help.oclc.org/Metadata_Services/CONTENTdm/Advanced_website_customization/API_Reference/CONTENTdm_API)
- [Frictionless Data Standards](https://datapackage.org/standard/)
- [Dublin Core Metadata](https://dublincore.org/specifications/)

### Community
- **Issues**: [GitHub Issues](https://github.com/your-username/contentdm-ai-generator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/contentdm-ai-generator/discussions)
- **Email**: [your-email@domain.com](mailto:your-email@domain.com)

### Professional Support
For institutional deployments, training, or custom development:
- Contact: Maurice Vanderfeesten (ORCID: 0000-0001-6397-4759)
- Commercial support and consulting available

---

**ContentDM AI Metadata Generator** - Enhancing digital cultural heritage with artificial intelligence.
