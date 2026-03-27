# Pinecone Architecture Gaps — Critical Issues

## Current State

**Only 1 Pinecone index exists**: `asahio-semantic-cache` (hardcoded in config.py)

### What's Missing

#### 1. **No Per-Org Index Provisioning**
- When a new org signs up, no Pinecone index is created for them
- All orgs share the same `asahio-semantic-cache` index
- Isolation relies on metadata filtering (not true isolation)
- **Risk**: Cross-org data leakage if metadata filter fails

#### 2. **No Master Model C Index**
- Model C (ABA behavioral patterns) is **in-memory only**
- Lines 89 and 117 in `model_c_pool.py` have `TODO` comments
- No cross-org pattern storage at all
- **Impact**: ABA engine can't learn from behavioral patterns

#### 3. **No Org Creation Hook**
- `orgs.py` has no POST endpoint to create orgs
- No Pinecone provisioning service exists
- No index lifecycle management

---

## Required Architecture

### Pinecone Index Structure

```
Per-org semantic cache:
  └─ asahio-cache-{org_id}         1024 dims, cosine, org-specific prompts

Master Model C (ABA):
  └─ asahio-model-c                1024 dims, cosine, anonymized fingerprints
```

### Index Naming Convention

```python
# Semantic cache (per-org isolation)
index_name = f"asahio-cache-{org_id}"

# Model C master pool (cross-org, anonymized)
index_name = "asahio-model-c"
```

---

## Implementation Plan

### Phase 1: Pinecone Index Provisioning Service

**File**: `backend/app/services/pinecone_provisioner.py`

```python
async def provision_org_index(org_id: str) -> bool:
    """Create a Pinecone index for a new org's semantic cache."""
    # 1. Connect to Pinecone
    # 2. Create index: asahio-cache-{org_id}
    # 3. Configure: 1024 dims, cosine, serverless
    # 4. Store index metadata in DB (orgs.pinecone_index_name)
    # 5. Return success/failure
```

**File**: `backend/app/services/pinecone_provisioner.py`

```python
async def provision_model_c_index() -> bool:
    """Create the master Model C index (one-time, global)."""
    # 1. Connect to Pinecone
    # 2. Create index: asahio-model-c
    # 3. Configure: 1024 dims, cosine, serverless
    # 4. Return success/failure
```

### Phase 2: Org Creation Endpoint + Hook

**File**: `backend/app/api/orgs.py`

Add POST endpoint:
```python
@router.post("/", status_code=201)
async def create_org(body: CreateOrgRequest, ...):
    # 1. Validate slug uniqueness
    # 2. Create Organisation record
    # 3. Create Member record (creator = owner)
    # 4. Provision Pinecone index (async background task)
    # 5. Generate first API key
    # 6. Return org details
```

**File**: `backend/alembic/versions/XXX_add_pinecone_index_name.py`

Add column:
```python
op.add_column('organisations', sa.Column('pinecone_index_name', sa.String(), nullable=True))
```

### Phase 3: Update Cache Service to Use Org-Specific Indexes

**File**: `backend/app/services/cache.py`

Change from:
```python
# Current: single shared index with metadata filter
pc.Index(settings.pinecone_index_name)
results = index.query(..., filter={"org_id": org_id})
```

To:
```python
# New: org-specific index (true isolation)
org = await db.get(Organisation, org_id)
pc.Index(org.pinecone_index_name or f"asahio-cache-{org_id}")
results = index.query(...)  # No metadata filter needed
```

### Phase 4: Model C Pinecone Integration

**File**: `backend/app/services/model_c_pool.py`

Replace TODO comments:
```python
# Line 89: conditional_add
if self._index is not None:
    # Embed the fingerprint as a vector
    vector = await _embed_fingerprint(record)
    self._index.upsert(vectors=[{
        "id": f"{record.agent_type}-{record.complexity_bucket}-{uuid.uuid4()}",
        "values": vector,
        "metadata": {
            "agent_type": record.agent_type,
            "complexity": record.complexity_bucket,
            "hallucination": record.hallucination_detected,
            "model": record.model_used,
        }
    }])

# Line 117: query_risk_prior
results = self._index.query(
    vector=await _embed_query(agent_type, complexity_bucket),
    top_k=100,
    include_metadata=True,
)
```

### Phase 5: Startup Task — Ensure Model C Index Exists

**File**: `backend/app/api/app.py` (startup event)

```python
@app.on_event("startup")
async def ensure_model_c_index():
    """Ensure master Model C index exists on app startup."""
    from app.services.pinecone_provisioner import ensure_model_c_index_exists
    await ensure_model_c_index_exists()
```

---

## Database Schema Changes

```sql
-- Add to organisations table
ALTER TABLE organisations ADD COLUMN pinecone_index_name VARCHAR;

-- For existing orgs, backfill with default
UPDATE organisations SET pinecone_index_name = 'asahio-semantic-cache';
```

---

## Configuration Changes

**File**: `backend/app/config.py`

Add:
```python
# Pinecone index templates
pinecone_cache_index_prefix: str = "asahio-cache"
pinecone_model_c_index: str = "asahio-model-c"
pinecone_dimension: int = 1024
pinecone_metric: str = "cosine"
pinecone_cloud: str = "aws"
pinecone_region: str = "us-east-1"
```

---

## Privacy & Security Considerations

### Per-Org Isolation
- Each org gets a dedicated Pinecone index
- No cross-org queries possible (architectural boundary)
- Metadata filtering not needed (true isolation)

### Model C Anonymization
- No `org_id` or `agent_id` stored in Model C index
- Complexity bucketed to 0.1 granularity
- Only aggregated patterns visible
- Minimum 50 observations before contributing

---

## Cost Implications

### Pinecone Pricing (Serverless)
- $0.10 per 1M reads
- $0.25 per 1M writes
- $0.20 per GB storage / month

### Per-Org Indexes
- **Worst case**: 1000 orgs × 1GB = $200/month storage
- **Likely**: Most orgs < 100MB = $20/month total
- **Tradeoff**: Privacy + isolation worth the cost

### Optimization: Lazy Provisioning
- Don't create index on org signup
- Create index on first cache write
- Delete index after 90 days of inactivity

---

## Migration Path for Existing Data

### Step 1: Backfill Existing Orgs
```python
# Script: scripts/backfill_pinecone_indexes.py
for org in await db.execute(select(Organisation)):
    await provision_org_index(str(org.id))
    org.pinecone_index_name = f"asahio-cache-{org.id}"
    await db.flush()
```

### Step 2: Migrate Cache Data
```python
# Script: scripts/migrate_cache_to_org_indexes.py
old_index = pc.Index("asahio-semantic-cache")
for org_id in org_ids:
    vectors = old_index.query(filter={"org_id": org_id}, top_k=10000)
    new_index = pc.Index(f"asahio-cache-{org_id}")
    new_index.upsert(vectors)
```

### Step 3: Delete Shared Index
```bash
# After migration complete and verified
pc.delete_index("asahio-semantic-cache")
```

---

## Testing Requirements

1. **Unit tests**: Index provisioning success/failure
2. **Integration tests**: Org creation → index exists
3. **Isolation tests**: Org A cannot query Org B's cache
4. **Model C tests**: Write fingerprint → query risk prior
5. **Cleanup tests**: Org deletion → index deleted

---

## Rollout Plan

### Week 1: Infrastructure
- [ ] Build `pinecone_provisioner.py` service
- [ ] Add DB migration for `pinecone_index_name` column
- [ ] Add config settings for index templates
- [ ] Unit tests for provisioner

### Week 2: Org Creation Hook
- [ ] Add POST `/orgs` endpoint
- [ ] Hook provisioner into org creation
- [ ] Background task for async provisioning
- [ ] Integration tests

### Week 3: Cache Migration
- [ ] Update `cache.py` to use org-specific indexes
- [ ] Backfill script for existing orgs
- [ ] Data migration script
- [ ] Gradual rollout with feature flag

### Week 4: Model C Integration
- [ ] Implement Pinecone upsert in `model_c_pool.py`
- [ ] Implement vector query in `model_c_pool.py`
- [ ] Startup task to ensure Model C index
- [ ] Integration tests for ABA → Model C flow

---

## Priority Assessment

| Item | Priority | Rationale |
|------|----------|-----------|
| Model C Pinecone Integration | **P0** | ABA engine completely non-functional without this |
| Per-Org Index Provisioning | **P1** | Security/privacy issue, but metadata filtering works short-term |
| Org Creation Endpoint | **P1** | Required for onboarding, can use Clerk webhook short-term |
| Cache Migration | **P2** | Optimization, existing shared index works |

---

## Next Steps

1. **Immediate**: Implement Model C Pinecone integration (P0)
2. **This week**: Build org provisioning service (P1)
3. **Next week**: Add org creation endpoint + hook (P1)
4. **Later**: Migrate to per-org indexes (P2)
