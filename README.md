# Nova Training Corpus Pipeline

## Current Status (2025-08-07)
- **Extracted**: 24GB across 668 files
- **Target**: 67GB total corpus
- **Status**: Actively extracting and processing

## Available Datasets

### Extracted (24GB)
- **C4 Dataset**: 3.9GB - Web crawl data for language modeling
- **Wikipedia**: 10.5GB - Complete English Wikipedia dump
- **CommonCrawl**: 5.4GB - Web crawl archives
- **StackOverflow**: 2.2GB - Programming Q&A data
- **OpenWebText**: 14MB (partial) - Reddit-sourced web text
- **Entrepreneur Content**: 8.1GB - Startup/business focused content

### Processing Pipeline
1. **Extraction**: Decompress archives → `/data/extracted/`
2. **Cleaning**: Remove noise, normalize → `/data/cleaned/`
3. **Categorization**: Topic classification → `/data/categorized/`
4. **Versioning**: Track changes → Git LFS

## Directory Structure
```
data/
├── extracted/     # Raw extracted files (24GB)
├── cleaned/       # Cleaned text (in progress)
├── categorized/   # Topic-sorted (pending)
└── processed/     # Training-ready (pending)
```

## Usage
```bash
# Check corpus status
python scripts/check_status.py

# Extract remaining archives
python pipeline/extractors/extract_all.py

# Clean extracted data
python pipeline/cleaners/clean_corpus.py
```

## For Vertex Training
The corpus is being prepared for Nova NLM training. Current focus:
- Entrepreneur/startup content
- Innovation/disruption topics
- Resource-constrained solutions
- Anti-corporate language patterns

## Collaboration
This pipeline integrates with other Nova agents via DragonflyDB streams:
- `nova.meridian.status` - Pipeline status updates
- `nova.vertex.requests` - Training data requests
- `nova.collaboration` - Inter-agent coordination