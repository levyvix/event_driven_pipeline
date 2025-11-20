# Pagination Guide - Visual Walkthrough

This guide explains how pagination works in the Weather API using real examples and diagrams.

---

## What is Pagination?

Pagination breaks large datasets into smaller **pages** so you don't fetch millions of records at once. Instead, you request one page at a time.

```
Database (1000 records)
│
├─ Page 1 (records 1-50)  ← You ask for this
├─ Page 2 (records 51-100)
├─ Page 3 (records 101-150)
└─ ... (more pages)
```

---

## How Your API Uses Pagination

Your API has **two paginated endpoints**:

1. **`GET /api/weather`** - Get all weather records (paginated)
2. **`GET /api/weather/location/{location_name}`** - Get records for a specific location (paginated)

Both use the same pagination pattern:
- **`page`**: Which page to fetch (default: 1, must be ≥ 1)
- **`page_size`**: How many records per page (default: 50, max: 100)

---

## Example 1: Fetching All Weather Records

### Request
```bash
curl "http://localhost:8000/api/weather?page=1&page_size=10"
```

### What Happens Behind the Scenes

```
Step 1: Calculate offset (skip)
┌─────────────────────────────────────┐
│ skip = (page - 1) * page_size       │
│ skip = (1 - 1) * 10 = 0             │
│ → Start at record 0 (first record)  │
└─────────────────────────────────────┘

Step 2: Query Database
┌──────────────────────────────────────────────────────┐
│ SELECT * FROM weather_records                        │
│ ORDER BY created_at DESC             ← Newest first  │
│ OFFSET 0                             ← Skip 0        │
│ LIMIT 10                             ← Get 10        │
│                                                      │
│ Also count TOTAL records (no offset/limit)          │
└──────────────────────────────────────────────────────┘

Step 3: Build Response
┌─────────────────────────────────────────────────────┐
│ {                                                   │
│   "total": 1000,         ← Total records in DB      │
│   "page": 1,             ← You asked for page 1    │
│   "page_size": 10,       ← 10 per page             │
│   "records": [           ← Array of 10 records     │
│     {id: 1, ...},                                  │
│     {id: 2, ...},                                  │
│     ...                                            │
│     {id: 10, ...}                                  │
│   ]                                                │
│ }                                                   │
└─────────────────────────────────────────────────────┘
```

### Response
```json
{
  "total": 1000,
  "page": 1,
  "page_size": 10,
  "records": [
    {
      "id": 1000,
      "location": {
        "id": 1,
        "name": "San Francisco",
        "region": "California",
        "country": "United States",
        "lat": 37.77,
        "lon": -122.42,
        "tz_id": "America/Los_Angeles",
        "created_at": "2025-11-20T10:00:00",
        "updated_at": "2025-11-20T10:00:00"
      },
      "condition": {
        "id": 5,
        "text": "Partly cloudy",
        "icon": "partly_cloud.png",
        "code": 1003,
        "created_at": "2025-11-20T09:00:00",
        "updated_at": "2025-11-20T09:00:00"
      },
      "localtime_epoch": 1700000000,
      "localtime": "2025-11-20 10:00",
      "last_updated_epoch": 1700000000,
      "last_updated": "2025-11-20 10:00",
      "temp_c": 15.0,
      "temp_f": 59.0,
      "humidity": 65,
      "wind_kph": 10.5,
      "created_at": "2025-11-20T10:00:00",
      "updated_at": "2025-11-20T10:00:00"
    },
    // ... 9 more records (11 total in response)
  ]
}
```

---

## Example 2: Navigating Through Pages

You have 1000 records with `page_size=10`. Let's see how to navigate:

### Page 1: Records 1-10
```bash
curl "http://localhost:8000/api/weather?page=1&page_size=10"
```
```
skip = (1 - 1) * 10 = 0       ← Start at 0
limit = 10                    ← Get 10

Database records: [1, 2, 3, ..., 10, 11, ...]
                   ↑────────────────────↑
                      Response (10 items)
```

### Page 2: Records 11-20
```bash
curl "http://localhost:8000/api/weather?page=2&page_size=10"
```
```
skip = (2 - 1) * 10 = 10      ← Start at 10 (skip first 10)
limit = 10                    ← Get 10

Database records: [1, 2, ..., 10, 11, 12, ..., 20, 21, ...]
                                    ↑────────────────────↑
                                      Response (10 items)
```

### Page 3: Records 21-30
```bash
curl "http://localhost:8000/api/weather?page=3&page_size=10"
```
```
skip = (3 - 1) * 10 = 20      ← Start at 20 (skip first 20)
limit = 10                    ← Get 10

Database records: [1, 2, ..., 20, 21, 22, ..., 30, 31, ...]
                                    ↑────────────────────↑
                                      Response (10 items)
```

---

## Example 3: Paginating Location-Specific Records

Get all weather records for **San Francisco** with pagination:

```bash
curl "http://localhost:8000/api/weather/location/San%20Francisco?page=1&page_size=25"
```

### What Happens

```
Step 1: Filter by location name
┌─────────────────────────────────────────────────────┐
│ SELECT weather_records.*                            │
│ FROM weather_records                                │
│ JOIN locations ON weather_records.location_id       │
│   = locations.id                                    │
│ WHERE locations.name ILIKE '%San Francisco%'        │
│ ORDER BY weather_records.created_at DESC            │
└─────────────────────────────────────────────────────┘
  ↓
  (Returns: 150 total records for SF)

Step 2: Apply pagination to filtered results
┌─────────────────────────────────────────────────────┐
│ OFFSET (1-1)*25 = 0                                 │
│ LIMIT 25                                            │
└─────────────────────────────────────────────────────┘
  ↓
  (Returns: First 25 SF records)
```

### Response
```json
{
  "total": 150,           ← Total for San Francisco only
  "page": 1,
  "page_size": 25,
  "records": [...]        ← 25 SF weather records
}
```

To get the next page of SF records:
```bash
curl "http://localhost:8000/api/weather/location/San%20Francisco?page=2&page_size=25"
```

---

## Code Walkthrough

### 1. **API Route** (`src/api/api_app/main.py`, lines 60-72)

```python
@app.get("/api/weather", response_model=schemas.WeatherRecordList)
async def list_weather_records(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Records per page"),
    db: Session = Depends(get_db),
):
    """List weather records with pagination."""
    skip = (page - 1) * page_size          # ← Calculate offset
    records, total = crud.get_weather_records(db, skip=skip, limit=page_size)

    return {"total": total, "page": page, "page_size": page_size, "records": records}
```

**What each part does:**

| Code | Purpose |
|------|---------|
| `page: int = Query(1, ge=1)` | Get `?page=` parameter (default 1, minimum 1) |
| `page_size: int = Query(50, ge=1, le=100)` | Get `?page_size=` parameter (default 50, max 100) |
| `skip = (page - 1) * page_size` | Convert page number to database offset |
| `crud.get_weather_records(db, skip=skip, limit=page_size)` | Query DB with skip/limit |
| `return {...}` | Return response with pagination metadata |

---

### 2. **CRUD Function** (`src/api/api_app/crud.py`, lines 116-123)

```python
def get_weather_records(
    db: Session, skip: int = 0, limit: int = 100
) -> tuple[list[models.WeatherRecord], int]:
    """Get paginated weather records"""
    query = db.query(models.WeatherRecord).order_by(desc(models.WeatherRecord.created_at))
    total = query.count()                    # ← Count ALL records
    records = query.offset(skip).limit(limit).all()  # ← Get one page
    return records, total
```

**What each part does:**

| Code | Purpose |
|------|---------|
| `query = db.query(models.WeatherRecord)...` | Build base query |
| `.order_by(desc(models.WeatherRecord.created_at))` | Order by newest first |
| `total = query.count()` | Count total records (without skip/limit) |
| `.offset(skip)` | Skip the first `skip` records |
| `.limit(limit)` | Take only `limit` records |
| `.all()` | Execute and fetch as list |
| `return records, total` | Return records AND total count |

---

### 3. **Response Schema** (`src/api/api_app/schemas.py`, lines 165-171)

```python
class WeatherRecordList(BaseModel):
    """Schema for paginated weather records"""
    total: int                                  # Total records in DB
    page: int                                   # Current page number
    page_size: int                              # Records per page
    records: list[WeatherRecordResponse]        # The actual records
```

This defines the JSON structure of the response.

---

## Key Concepts

### Skip vs Limit

```
┌─────────────────────────────────────────────────────────┐
│  Database: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]     │
│             ↑        (skip=2)                           │
│                      ↓                                  │
│  After skip:  [3, 4, 5, 6, 7, 8, 9, 10, 11, 12]       │
│                ↑                 (limit=5)             │
│                                   ↓                    │
│  After limit: [3, 4, 5, 6, 7]                          │
└─────────────────────────────────────────────────────────┘

skip=2    → Skip first 2 records
limit=5   → Take next 5 records
Result:   → Records 3-7
```

### Total Count

The **total** count represents ALL records matching the query, NOT just the current page:

```
Database: 1000 total records
Request:  page=5, page_size=10

Response:
{
  "total": 1000,     ← ALL records (not 10)
  "page": 5,         ← Current page
  "page_size": 10,   ← Per page
  "records": [...]   ← Only 10 records (41-50)
}
```

This lets the client know:
- How many total records exist
- How many pages they need to fetch: `total / page_size` → 100 pages

---

## Common Queries

### Get first 50 records (default)
```bash
curl "http://localhost:8000/api/weather"
```

### Get records 51-100
```bash
curl "http://localhost:8000/api/weather?page=2&page_size=50"
```

### Get records 1-20
```bash
curl "http://localhost:8000/api/weather?page=1&page_size=20"
```

### Get all records for a location, 25 per page
```bash
curl "http://localhost:8000/api/weather/location/London?page=1&page_size=25"
```

### Get next page of London results
```bash
curl "http://localhost:8000/api/weather/location/London?page=2&page_size=25"
```

---

## Performance Notes

### Why Pagination?

Without pagination, this would be slow/impossible:
```python
# ❌ Bad: Fetch ALL 1 million records
GET /api/weather
# Response: 50MB+ JSON, takes 10+ seconds

# ✅ Good: Fetch one page at a time
GET /api/weather?page=1&page_size=50
# Response: ~50KB, takes <100ms
```

### Database Optimization

Your API uses:
- **ORDER BY created_at DESC**: Ensures newest records first (uses index on created_at)
- **OFFSET + LIMIT**: Efficient for small pages (skips not found in index)
- **Composite index**: `idx_weather_upsert` on (location_id, condition_id, localtime_epoch) speeds up location filtering

---

## Debugging Pagination

### Issue: Getting wrong records

Check your math:
```
Page 3, page_size=10
skip = (3-1) * 10 = 20
Expect records 21-30 ✓
```

### Issue: Response shows wrong total

The **total** is the count of ALL records matching the filter, not the page count:
```json
{
  "total": 1000,      ← This is the full count
  "page": 5,          ← Not related to total
  "page_size": 10,
  "records": [...]    ← Only 10 here
}
```

### Issue: Getting empty records on valid page

Check if you're past the last page:
```
total=100, page_size=10 → Max page is 10
Page 11: returns empty records (no error)
Page 12: same
```

---

## Visual Reference: The Pagination Flow

```
┌──────────────────────────────────────────────────────────────┐
│  User requests: GET /api/weather?page=2&page_size=10         │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│  FastAPI Route Handler (main.py:60-72)                       │
│  • Extract page=2, page_size=10                              │
│  • Calculate skip = (2-1)*10 = 10                            │
│  • Call crud.get_weather_records(db, skip=10, limit=10)      │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│  CRUD Function (crud.py:116-123)                             │
│  • Count ALL records: total = 1000                           │
│  • Query with OFFSET 10 LIMIT 10                            │
│  • Return: records[11-20], total=1000                        │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│  API Response (Pydantic Schema validation)                   │
│  {                                                           │
│    "total": 1000,                                            │
│    "page": 2,                                                │
│    "page_size": 10,                                          │
│    "records": [record_11, record_12, ..., record_20]        │
│  }                                                           │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│  Client receives JSON response                               │
└──────────────────────────────────────────────────────────────┘
```

---

## Summary

| Concept | Explanation |
|---------|-------------|
| **Page** | Which "chunk" of data to fetch (starts at 1) |
| **page_size** | How many records per chunk (1-100) |
| **skip/offset** | How many records to skip: `(page-1) * page_size` |
| **limit** | How many records to return: `page_size` |
| **total** | Count of ALL records, not just current page |
| **Order** | Newest first (`ORDER BY created_at DESC`) |

Now you can use pagination to efficiently fetch large datasets from your API! 🎯
