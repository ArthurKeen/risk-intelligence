# Theme Icon and Color Fix

## Issue
After fixing the `isDefault` field, themes were switching (name changed) but icons and colors were not being applied in the ArangoDB Visualizer.

## Root Cause

Two issues were identified:

1. **Missing `rules` field**: The database themes were missing the `rules` field in `nodeConfigMap` and `edgeConfigMap`. While the working database has `rules: []` (empty array) for nodes without rules, the problem database had the field completely missing.

2. **Partial updates**: The installation script was using `theme_col.update()` which performs a **merge** operation in ArangoDB, not a full document replacement. This could cause fields to persist from old versions or new fields to not be properly added.

## Solution Applied

### 1. Updated `scripts/install_theme.py`

**Changes made:**
- Changed from `update()` to `replace()` to ensure full document replacement
- Added explicit `rules: []` initialization for all node and edge configs that don't have rules
- Ensures theme structure matches the working database pattern

**Key code changes:**
```python
# Ensure rules field exists (even if empty) for all node configs
if "nodeConfigMap" in theme:
    for node_type, node_config in theme["nodeConfigMap"].items():
        if "rules" not in node_config:
            node_config["rules"] = []

# Use replace() instead of update() for full document replacement
theme["_key"] = existing[0]["_key"]
theme["_id"] = existing[0]["_id"]
theme_col.replace(theme)
```

### 2. Reinstalled All Themes

All themes have been reinstalled with the corrected structure:
- ✅ `rules` field now present in all node and edge configs
- ✅ Full document replacement ensures no stale fields
- ✅ Structure now matches working database pattern

## Verification

After reinstallation, theme structure verification shows:
- ✅ `sentries_standard`: All fields including `rules` are present
- ✅ `sentries_risk_heatmap`: All fields including `rules` are present
- ✅ Structure matches source JSON files exactly

## Next Steps for Testing

If icons and colors still don't apply after this fix:

### 1. Clear Browser Cache
The ArangoDB Visualizer may be caching old theme data:
- **Chrome/Edge**: Press `Ctrl+Shift+Delete` (or `Cmd+Shift+Delete` on Mac)
- Select "Cached images and files"
- Clear cache and reload the ArangoDB UI

### 2. Hard Refresh
- Press `Ctrl+F5` (or `Cmd+Shift+R` on Mac) to force a hard refresh
- This bypasses browser cache

### 3. Check Browser Console
Open Chrome Developer Tools (F12) and check for:
- JavaScript errors when switching themes
- Network requests to fetch theme data
- Console warnings about theme structure

### 4. Verify Theme Selection
In ArangoDB Visualizer:
1. Navigate to a graph (e.g., KnowledgeGraph)
2. Open the theme dropdown
3. Select a theme
4. Check if the theme name changes
5. Verify if nodes/edges update visually

### 5. Check Node Data
Verify that nodes have the required attributes:
- `label` attribute (for labelAttribute)
- `riskScore` (for risk heatmap rules)
- `dataSource` (for synthetic entity rules)

If nodes are missing these attributes, the theme rules won't apply correctly.

## Expected Behavior

After the fix and cache clearing:
1. **Theme name changes** when switching themes ✅ (already working)
2. **Node colors change** based on theme background colors
3. **Node icons change** based on theme iconName
4. **Edge colors change** based on theme lineStyle colors
5. **Rules apply** (e.g., risk-based coloring, synthetic entity styling)

## Files Modified

1. `scripts/install_theme.py` - Updated to use `replace()` and ensure `rules` field exists
2. `docs/theme_icon_color_fix.md` - This documentation

## Technical Details

### Theme Structure Requirements

For ArangoDB Visualizer to properly apply themes, each node/edge config should have:
- `background` object with `color` and `iconName` (for nodes)
- `lineStyle` object with `color` and `thickness` (for edges)
- `rules` array (even if empty) - **This was missing and is now fixed**
- `labelAttribute` string
- `hoverInfoAttributes` array

The working database pattern shows that even nodes without rules should have `rules: []` explicitly set.
