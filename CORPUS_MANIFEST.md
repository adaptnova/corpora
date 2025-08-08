# Nova Training Corpus Manifest

## Available Data (2025-08-07)

### Local Extracted Data: 15GB
Located at `/home/x/data/corpora/extracted/`

#### Available for Processing:
1. **C4 Dataset** - Web crawl data
2. **OpenWebText** - Reddit-sourced text  
3. **StackOverflow** - Programming Q&A
4. **Awesome Lists** - Curated resources
5. **Entrepreneur** - Startup/business content

### Archived Source Files (Need Re-extraction on Nebius)
- Wikipedia (24GB compressed)
- CommonCrawl (multiple files)
- Additional StackExchange dumps
- The Pile subsets

## Processing Pipeline

The corpus will be processed on Nebius infrastructure:

1. **Upload compressed archives to Nebius COS**
2. **Extract on Nebius compute instances** (more disk space)
3. **Clean and normalize text**
4. **Categorize by topic**
5. **Version and track changes**

## Next Steps

1. Set up Nebius COS bucket
2. Upload compressed archives
3. Spin up Nebius compute for processing
4. Run full pipeline with 200GB+ disk space

## For Vertex Training

Current available: 15GB cleaned, ready for initial training
Target: 67GB after full pipeline on Nebius