# Nova Training Corpus Locations

## Current Status (2025-08-08)
Total corpus available: **15GB+ extracted, ready for training**

## Data Locations

### 1. GitHub Repository
**URL:** https://github.com/adaptnova/corpora
**Contains:**
- OpenWebText: 121MB (56 files)
- Awesome Lists: 420KB (curated resources)
- Pipeline code and documentation
- Manifests and status tracking

### 2. Nebius Cloud Object Storage (COS)
**Bucket:** `s3://cos/nova-training/`
**Status:** Currently uploading 15GB+ corpus
**Contains:**
- Full extracted corpus (15GB)
- C4 dataset (3.9GB)
- Wikipedia partial (8.5GB)
- StackOverflow data
- OpenWebText complete
- Entrepreneur content

**Access:**
```bash
# List corpus in Nebius
aws s3 ls s3://cos/nova-training/ --endpoint-url https://storage.us-central1.nebius.cloud:443 --recursive

# Download specific dataset
aws s3 cp s3://cos/nova-training/c4/ ./c4/ --endpoint-url https://storage.us-central1.nebius.cloud:443 --recursive
```

### 3. Local Server
**Path:** `/home/x/data/corpora/extracted/`
**Size:** 15GB
**Note:** Being uploaded to Nebius, will be cleared after upload completes

## Dataset Breakdown

| Dataset | Size | Files | Status | Location |
|---------|------|-------|---------|----------|
| C4 | 3.9GB | 5 | Complete | Nebius COS |
| Wikipedia | 8.5GB | 1 | Partial | Nebius COS |
| OpenWebText | 121MB | 56 | Complete | GitHub + Nebius |
| StackOverflow | ~2GB | Multiple | Complete | Nebius COS |
| Awesome Lists | 420KB | 1 | Complete | GitHub + Nebius |
| Entrepreneur | ~1GB | Multiple | Partial | Nebius COS |

## For Vertex Training

Vertex can access the corpus from:
1. **Nebius COS** - Full 15GB corpus via S3 API
2. **GitHub** - Smaller datasets and samples
3. **Direct transfer** - Can sync via DragonflyDB coordination

## Next Steps
1. Complete Nebius upload (in progress)
2. Set up cleaning pipeline on Nebius compute
3. Process remaining 52GB to reach 67GB target
4. Implement versioning with Git LFS