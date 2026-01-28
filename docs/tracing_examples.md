# Example Entities for Tracing Analytics

## Recommended Examples for Demonstration

### Best Person Example

**Name:** `Synthetic Relative`  
**_key:** `68088389`  
**_id:** `Person/68088389`  
**Search in Visualizer:** Use `68088389` or `Person/68088389`  
**Risk Profile:**
- Direct Risk (`riskScore`): 0.0 (not directly sanctioned)
- Inferred Risk (`inferredRisk`): 0.5 (has connections to sanctioned entities)
- Data Source: Synthetic (test data)

**Why it's good:**
- Has a clear path to sanctioned entities via family relationships
- Shows how inferred risk works (0.5 = 50% risk via family ties)
- Perfect for demonstrating "[Person] Trace to Sanctioned Entities" action

**How to use:**
1. In DataGraph or KnowledgeGraph, search for: `68088389` (the _key)
2. Right-click on the node
3. Select "Canvas Action" → "[Person] Trace to Sanctioned Entities"
4. View the paths to sanctioned entities

---

### Best 3-Hop Organization Example (Recommended)

**Name:** `Synthetic Vetting Target - 3-Hop Link`  
**_key:** `64166673`  
**_id:** `Organization/64166673`  
**Search in Visualizer:** Use `64166673` or `Organization/64166673`  
**Risk Profile:**
- Direct Risk (`riskScore`): 0.0 (not directly sanctioned)
- Inferred Risk (`inferredRisk`): 1.0 (100% risk via 3-hop ownership chain)
- Data Source: Synthetic (test data)
- **Path Depth:** 3 hops (Sanctioned Org → Layer 1 → Layer 2 → Target)

**Why it's good:**
- Demonstrates deep multi-hop ownership chains (the "Shell Game" scenario)
- Shows how risk propagates through multiple layers
- Perfect for demonstrating complex tracing scenarios
- Shows maximum inferred risk (1.0) despite being 3 hops away

**How to use:**
1. In DataGraph or KnowledgeGraph, search for: `64166673` (the _key)
2. Right-click on the node
3. Select "Canvas Action" → "[Organization] Trace to Sanctioned Entities"
4. View the 3-hop ownership chain to sanctioned entities

---

### Best 2-Hop Organization Example

**Name:** `Synthetic Vetting Target - Indirect Link`  
**_key:** `64166667`  
**_id:** `Organization/64166667`  
**Search in Visualizer:** Use `64166667` or `Organization/64166667`  
**Risk Profile:**
- Direct Risk (`riskScore`): 0.0 (not directly sanctioned)
- Inferred Risk (`inferredRisk`): 1.0 (100% risk via 2-hop ownership chain)
- Data Source: Synthetic (test data)
- **Path Depth:** 2 hops (Sanctioned Org → Holding Co → Target)

**Why it's good:**
- Demonstrates 2-hop ownership chains
- Shows intermediate holding companies
- Good for showing how risk flows through corporate structures

**How to use:**
1. In DataGraph or KnowledgeGraph, search for: `64166667` (the _key)
2. Right-click on the node
3. Select "Canvas Action" → "[Organization] Trace to Sanctioned Entities"
4. View the 2-hop ownership chain to sanctioned entities

---

## Alternative Examples

### Person Examples

1. **Relative** (`Person/68088390`)
   - Similar to "Synthetic Relative"
   - Inferred Risk: 0.5
   - Good alternative if "Synthetic Relative" is not available

### Organization Examples

1. **Vetting Target - Direct Link**
   - **_key:** `64166675`
   - **_id:** `Organization/64166675`
   - Similar to "Synthetic Vetting Target - Direct Link"
   - Inferred Risk: 1.0
   - Good alternative example

2. **Synthetic Holding - Layer 1**
   - **_key:** `64166671`
   - **_id:** `Organization/64166671`
   - Part of a 3-hop ownership chain (the "Shell Game" scenario)
   - Inferred Risk: 1.0
   - Demonstrates deep multi-hop tracing

---

## Real-World Examples (from OFAC data)

These are actual sanctioned entities that can be used to trace FROM (reverse tracing):

1. **Stars Group Holding** (`Organization/17039`)
   - Direct Risk: 1.0 (sanctioned)
   - Can trace FROM this entity to find all connected entities

2. **Asyaf International Holding Group** (`Organization/18536`)
   - Direct Risk: 1.0 (sanctioned)
   - Large holding company with many connections

---

## Usage Tips

### For Demonstrations

1. **Start with clean entities** (riskScore = 0) to show how tracing reveals hidden risk
2. **Use entities with high inferredRisk** (0.5 or 1.0) to ensure paths exist
3. **Explain the difference:**
   - `riskScore`: Direct sanctions (on official lists)
   - `inferredRisk`: Risk inherited through relationships

### Search Tips

- Use the search bar: "Search & add nodes to canvas"
- Search by label name (e.g., "Synthetic Relative")
- Or search by partial name (e.g., "Vetting Target")

### Expected Results

When using the tracing actions:
- **Person tracing**: Should find paths via `family_member_of`, `leader_of`, or `owned_by` relationships
- **Organization tracing**: Should find paths via `owned_by`, `leader_of`, or `operates` relationships
- **Path depth**: Up to 3 hops
- **Result limit**: Up to 50 paths displayed

---

## Quick Reference

| Entity Type | Example Name | _key | _id | Hops | Use Case |
|------------|-------------|------|-----|------|----------|
| Organization | **Synthetic Vetting Target - 3-Hop Link** | `64166673` | `Organization/64166673` | **3** | **Deep multi-hop (Shell Game)** |
| Organization | Synthetic Vetting Target - Indirect Link | `64166667` | `Organization/64166667` | **2** | **2-hop ownership chain** |
| Organization | Synthetic Holding - Layer 2 | `64166672` | `Organization/64166672` | 2 | Intermediate in 3-hop chain |
| Organization | Vetting Target - 3-Hop Link | `64166683` | `Organization/64166683` | 3 | Alternative 3-hop example |
| Person | Synthetic Relative | `68088389` | `Person/68088389` | 1-2 | Family ties to sanctions |
