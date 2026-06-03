---
name: polymer-db
version: 1.0.0
description: "Polymer database search: query the Polymer-Data-Bank for polymer data, supporting searches by DOI, polymer name, properties, etc. Returns structure, thermal, optical, mechanical, and electrical property information. Use when users ask about polymer properties (Tg/Td/transmittance/mechanical properties), look up polymer data from specific papers, or need to filter polymers by performance criteria."
---

# Polymer Database Search (Polymer-Data-Bank)

## API Information

- **Endpoint**: `POST https://open.bohrium.com/openapi/v1/database/common_data/list`
- **Authentication**: Header `Authorization: Bearer $BOHR_ACCESS_KEY`
- **tableAk**: `123zl00` (Polymer-Data-Bank, 280k+ records)
- **Data Source**: Bohrium Materials Database

## Request Format

```bash
curl -s -X POST 'https://open.bohrium.com/openapi/v1/database/common_data/list' \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $BOHR_ACCESS_KEY" \
  -d '<JSON body>'
```

### Basic Request Body

```json
{
  "tableAk": "123zl00",
  "page": 1,
  "pageSize": 50,
  "filters": { ... },
  "selectedFields": ["field1", "field2"],
  "orderBy": [{"field": "fieldName", "order": "asc"}]
}
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tableAk` | string | Yes | Fixed `"123zl00"` |
| `page` | int | Yes | Page number, starting from 1 |
| `pageSize` | int | Yes | Items per page, max 5000 |
| `filters` | object | No | Filter conditions (Filter structure) |
| `selectedFields` | []string | No | Only return specified fields |
| `orderBy` | []object | No | Sort by `{"field": "xxx", "order": "asc/desc"}` |

### Filter Structure

```json
{
  "type": 2,
  "groupOperator": "and",
  "sub": [
    {
      "type": 1,
      "field": "field_name (dataIndex)",
      "operator": "eq",
      "value": "value"
    }
  ]
}
```

- `type`: `1` = Simple condition, `2` = Compound condition (with sub)
- `groupOperator`: `"and"` | `"or"`
- `operator`: `eq` / `neq` / `like` / `gt` / `gte` / `lt` / `lte` / `in` / `nin` / `between`

**Important limitation**: All property fields are **string type** (values like `"71.3 °C"`, `"[255 °C,288 °C]"`). Operators like `gt`/`lt` perform lexicographic comparison, not numeric. Numeric range filtering must be done client-side after parsing.

## Field Name Mapping

### Basic Information
| Common Name | dataIndex | Example Value |
|-------------|-----------|---------------|
| DOI | `doi` | `"10.1021/acs.macromol.9b02359"` |
| Polymer name | `polymer_name` | `"PI"`, `"PU"` |
| Polymer type | `polymer_type` | `"Polyimide"` |
| Monomer composition/structure | `components` | `"6FDA:O=C1OC...;ODA:Nc1ccc..."` |
| Feed ratio | `feed_ratio_text` | `"DABz/m-BAPS = 1/1"` |
| Ratio type | `ratio_type` | `"mole"`, `"weight"` |

### Thermal Properties
| Common Name | dataIndex | Related Fields |
|-------------|-----------|----------------|
| Tg / Glass transition temperature | `GlassTransitionTemperature(Tg)` | `test_method_GlassTransitionTemperature(Tg)`, `heating_rate_GlassTransitionTemperature(Tg)`, `atmosphere_GlassTransitionTemperature(Tg)` |
| Td / Decomposition temperature | `DecompositionTemperature(Td)` | `decomposition_criterion_DecompositionTemperature(Td)`, `atmosphere_DecompositionTemperature(Td)` |
| Tm / Melting temperature | `MeltingTemperature(Tm)` | `test_method_MeltingTemperature(Tm)` |
| Tc / Crystallization temperature | `CrystallizationTemperature(Tc)` | — |
| CTE / Coefficient of thermal expansion | `CoefficientofThermalExpansion(CTE)` | — |
| Thermal conductivity | `ThermalConductivity` | — |

### Optical Properties
| Common Name | dataIndex | Related Fields |
|-------------|-----------|----------------|
| Transmittance | `Transmittance` | `wavelength_Transmittance`, `thickness_Transmittance` |
| Refractive index | `RefractiveIndex(n)` | `wavelength_RefractiveIndex(n)` |
| Yellow index | `YellowIndex(YI)/WhitenessIndex(WI)` | — |
| Haze | `Haze` | — |
| Birefringence | `Birefringence(Δn)` | — |
| Cut-off wavelength | `Cut-offWavelength(λ_cut)` | — |
| Abbe number | `AbbeNumber(νd)` | — |

### Mechanical Properties
| Common Name | dataIndex |
|-------------|-----------|
| Tensile strength | `TensileStrength` |
| Tensile modulus / Young's modulus | `TensileModulus` |
| Elongation at break | `ElongationatBreak` |
| Flexural strength | `FlexuralStrength` |
| Flexural modulus | `FlexuralModulus` |
| Impact strength | `ImpactStrength` |
| Shear strength | `ShearStrength` |
| Shore hardness | `ShoreHardness` |

### Electrical Properties
| Common Name | dataIndex |
|-------------|-----------|
| Dielectric constant Dk | `DielectricConstant(Dk)` |
| Dielectric loss Df | `DielectricLoss(Df/tanδ)` |
| Breakdown strength | `BreakdownStrength` |
| Volume resistivity | `VolumeResistivity` |
| Proton conductivity | `ProtonConductivity` |

### Molecular Weight
| Common Name | dataIndex |
|-------------|-----------|
| Number-average molecular weight Mn | `mn_value` |
| PDI / Polydispersity index | `pdi_value` |

## Query Strategies

### Exact Query (Q1 type)

User asks "properties of a specific DOI/polymer": query directly with `selectedFields` limiting returned fields.

```json
{
  "tableAk": "123zl00",
  "page": 1,
  "pageSize": 50,
  "filters": {
    "type": 2, "groupOperator": "and",
    "sub": [{"type": 1, "field": "doi", "operator": "eq", "value": "10.1021/..."}]
  },
  "selectedFields": ["polymer_name", "polymer_type", "GlassTransitionTemperature(Tg)", "DecompositionTemperature(Td)"]
}
```

### Numeric Range Filtering (Q2 type)

User asks "polymers with Tg > 350°C":

1. **Cannot** directly use `gt` operator (field is string, lexicographic comparison is inaccurate)
2. **Correct approach**: Use `like` operator to exclude empty values (`"value": ""`), set `pageSize: 5000`, fetch data and parse numerically on client side

```python
import re

def parse_value_celsius(val_str):
    """Parse temperature string with units, convert to °C"""
    if not val_str:
        return None
    nums = re.findall(r'[-+]?\d+\.?\d*', val_str)
    if not nums:
        return None
    values = [float(n) for n in nums]
    max_val = max(values)
    if 'K' in val_str and '°C' not in val_str:
        return max_val - 273.15
    elif '°F' in val_str:
        return (max_val - 32) * 5 / 9
    return max_val
```

3. After filtering, perform statistical analysis (type distribution, frequent monomers, etc.)

### Analysis & Recommendation (Q3 type)

User asks "suggestions for synthesizing a polymer with XX properties":

1. Use `like ""` to fetch records with that property data (max 5000/page, may need pagination)
2. Parse values on client side, filter records meeting criteria
3. Analyze `polymer_type` distribution, frequent monomers in `components`
4. Provide structural design suggestions based on data patterns

## Data Format Notes

### components field format
```
monomer_name:SMILES;monomer_name:SMILES;...
```
Example: `6FDA:O=C1OC(=O)c2cc(...)ccc21;ODA:Nc1ccc(Oc2ccc(N)cc2)cc1`

### Property value format (all strings)
- Single value: `"71.3 °C"`
- Multiple values: `"[255 °C,288 °C]"`
- Descriptive: `"over 90 %"`, `"greater than 350 °C"`
- With error: `"90.8% ± 0.6%"`

### System fields (ignore)
- `_id`: MongoDB ObjectID
- `a1b2c3d4e5_is_locked`: Lock flag
- `a1b2c3d4e5_owner_id`: Data owner
- `a1b2c3d4e5_source`: Data source
- `a1b2c3d4e5_status`: Review status
- `authors`: Contributor info
- `createTime` / `updateTime`: Timestamps

## Important Notes

1. **Inconsistent units**: Same field may mix °C, K, °F — unit conversion is required
2. **String values**: All property fields are strings, numeric comparison must be done client-side
3. **Multi-value fields**: A record may have multiple values for a property (array format like `"[val1,val2]"`)
4. **pageSize limit**: Max 5000. For large datasets, use pagination (total count in `data.count`)
5. **Special characters in field names**: e.g. `GlassTransitionTemperature(Tg)` contains parentheses, use directly as JSON key
6. **like empty string**: `"operator": "like", "value": ""` matches all non-empty records
7. **When presenting results** to user, filter out system fields (`a1b2c3d4e5_*`, `authors`), show only meaningful data
