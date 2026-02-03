# Canvas Actions and Stored Queries Fix

## Issues Found

### Canvas Actions
Our canvas actions had the wrong structure compared to working actions:

**Working action structure:**
- ✅ Only `queryText` field (no `query` field)
- ✅ No `title` field
- ✅ `bindVariables.nodes` is empty string `""` (not empty array `[]`)

**Our action structure (before fix):**
- ❌ Both `query` and `queryText` fields
- ❌ Has `title` field
- ❌ `bindVariables.nodes` is empty array `[]`

### Stored Queries
Our stored queries are in the **wrong collection**:

**Working query:**
- Collection: `_queries`
- Structure: `name`, `description`, `graphId`, `queryText`, `bindVariables`, `createdAt`, `updatedAt`

**Our queries:**
- Collection: `_editor_saved_queries` ❌
- Structure: `name`, `value` (not `queryText`), `updatedAt` (missing many fields)

## Fixes Applied

### 1. Canvas Actions Fixed ✅
- Removed `query` field (kept only `queryText`)
- Removed `title` field
- Changed `bindVariables.nodes` from `[]` to `""`
- Updated installation script to create actions with correct structure

### 2. Stored Queries Need Fix
- Need to create queries in `_queries` collection (not `_editor_saved_queries`)
- Need to use `queryText` field (not `value`)
- Need to add `graphId`, `description`, `bindVariables`, `createdAt` fields

## Next Steps

Update `scripts/install_dashboard.py` to:
1. Create queries in `_queries` collection
2. Use correct structure matching working query
3. Include all required fields: `graphId`, `description`, `queryText`, `bindVariables`, `createdAt`, `updatedAt`
