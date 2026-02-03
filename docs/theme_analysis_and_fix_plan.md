# Theme Analysis and Fix Plan

## Executive Summary

After analyzing the working `themes` database (2 graphs) and the problematic `risk-management` database (3 graphs), the theme structures were **structurally identical**. However, to ensure proper UI state management with 3+ graphs, we needed to make `isDefault` field values **explicit** on all themes.

**✅ FIX APPLIED**: All themes now have explicit `isDefault` values set. See `theme_fix_summary.md` for details.

## Analysis Findings

### Database Comparison

| Aspect | Working DB (`themes`) | Problem DB (`risk-management`) |
|--------|----------------------|-------------------------------|
| **Graph Count** | 2 graphs (FOAF-Graph, Property-Graph) | 3 graphs (DataGraph, KnowledgeGraph, OntologyGraph) |
| **Total Themes** | 5 themes | 8 themes |
| **Theme Structure** | Identical | Identical |
| **isDefault Field** | Only on Default themes | Only on Default themes |
| **Custom Themes** | Missing `isDefault` field | Missing `isDefault` field |

### Theme Structure Analysis

**Before Fix:**
- **Default themes**: Had `isDefault: true` field
- **Custom themes**: Did NOT have `isDefault` field (field was absent, not set to `false`)

**After Fix:**
- **Default themes**: Have `isDefault: true` field (explicit)
- **Custom themes**: Now have `isDefault: false` field (explicit)

### Key Observations

1. **Structure is Correct**: The theme documents in both databases have identical structure
2. **isDefault is Set**: Default themes correctly have `isDefault: true`
3. **Graph Count Difference**: The only significant difference is the number of graphs (2 vs 3)

### Potential Root Causes

Given that the structures are identical, the issue likely stems from:

1. **UI State Management**: ArangoDB Visualizer may have issues persisting theme selection when switching between 3+ graphs
2. **Theme Query Logic**: The UI might be querying themes in a way that doesn't scale well to 3 graphs
3. **Cache/State Persistence**: Theme selection state might not be properly isolated per graph when there are multiple graphs

## Fix Plan

### Phase 1: Ensure Explicit Theme State (Recommended First Step)

Even though the structure matches, we should ensure all themes have explicit `isDefault` values:

1. **Set `isDefault: false` explicitly on all custom themes**
   - This ensures the UI has clear, explicit state for every theme
   - May help with UI state management when switching graphs

2. **Verify only one `isDefault: true` per graph**
   - Each graph should have exactly one theme with `isDefault: true`
   - This is the "fallback" theme when switching graphs

### Phase 2: Theme Installation Script Update

Update `scripts/install_theme.py` to:
- Explicitly set `isDefault: false` on all custom themes
- Ensure `isDefault: true` is only set on the Default theme (or first theme if no Default exists)
- Add validation to prevent multiple `isDefault: true` themes per graph

### Phase 3: Verification and Testing

1. Re-run theme installation script
2. Verify theme structure matches working database pattern
3. Test theme switching between all 3 graphs in UI
4. Document any remaining issues

## Implementation

### ✅ Step 1: Updated install_theme.py

Modified the theme installation logic to explicitly set `isDefault` on all themes:

```python
# Set isDefault explicitly: only Default themes or Ontology theme should be default
if g_id == "OntologyGraph" and theme["name"] == "Ontology":
    theme["isDefault"] = True
elif theme["name"] == "Default":
    theme["isDefault"] = True
else:
    theme["isDefault"] = False
```

### ✅ Step 2: Created Fix Script

Created `scripts/fix_themes.py` to update existing themes:
- Sets `isDefault: false` on all custom themes
- Ensures only Default theme (or Ontology for OntologyGraph) has `isDefault: true`
- Verifies correct state after updates

### ✅ Step 3: Applied Fix

Successfully ran the fix script. All themes now have explicit `isDefault` values:
- **DataGraph**: Default=true, sentries_standard=false, sentries_risk_heatmap=false
- **KnowledgeGraph**: Default=true, sentries_standard=false, sentries_risk_heatmap=false  
- **OntologyGraph**: Ontology=true, Default=false

## Expected Outcome

After applying the fix:
- All custom themes will have `isDefault: false` explicitly set
- Only Default themes will have `isDefault: true`
- Theme switching between graphs should work consistently
- UI state should be properly isolated per graph

## Alternative Investigation Paths

If the explicit `isDefault` fix doesn't resolve the issue:

1. **Check ArangoDB Version**: Ensure both databases are on the same ArangoDB version
2. **Browser Cache**: Clear browser cache/localStorage for ArangoDB UI
3. **Theme Order**: Check if theme display order matters (try reordering themes)
4. **Graph Creation Order**: Verify if the order graphs were created affects theme behavior
5. **UI Logs**: Check browser console for errors when switching graphs

## Files to Modify

1. `scripts/install_theme.py` - Update theme installation logic
2. `scripts/fix_themes.py` - Create/update one-time fix script
3. (Optional) Add theme validation script for future debugging
