---
name: polymer-db
version: 2.0.2
description: "Polymer database retrieval: query Polymer-Data-Bank polymer records (280k+ records), supporting searches by DOI, polymer name, performance properties, and numeric property ranges. Returns structure, thermal, optical, mechanical, electrical, and synthesis information. Use when users ask about polymer properties (Tg/Td/transmittance/mechanical properties), look up polymer data from a paper, or need polymers filtered by performance criteria."
---

# Polymer Database Search (Polymer-Data-Bank)

## API Information

- **Endpoint**: `POST https://open.bohrium.com/openapi/v2/database/common_data/list`
- **Authentication**: Header `Authorization: Bearer $BOHR_ACCESS_KEY`
- **tableAk**: `123zl00` (Polymer-Data-Bank, 280k+ records)
- **Data Source**: Bohrium Materials Database

## Request Format

```bash
curl -s -X POST 'https://open.bohrium.com/openapi/v2/database/common_data/list' \
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
  "selectedFields": ["field1", "field2"]
}
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tableAk` | string | Yes | Fixed `"123zl00"` |
| `page` | int | Yes | Page number, starting from 1 |
| `pageSize` | int | Yes | Items per page, max 5000 |
| `filters` | object | No | Filter conditions (Filter structure) |
| `selectedFields` | []string | No | Only return specified fields; recommended to reduce response size |
| `orderBy` | []object | No | Not recommended. Sorting is fragile for this endpoint and can trigger `$sort key ordering must be 1 or -1`; for performance fields, omit `orderBy` and sort locally after retrieval. |

### Response Structure

Records are returned in `data.list`; the server-side candidate count is in `data.count`.

```json
{
  "data": {
    "count": 123,
    "list": [{ "polymer_name": "...", "GlassTransitionTemperature(Tg)(°C)": "455.0" }]
  }
}
```

**Do not read results from `data.rows`.** If `data.count` is nonzero but `data.list` is empty, check `page`/`pageSize`, field names, sorting parameters, and the response structure before concluding that the database has no results.

### Call Strategy (Avoid Repeated Queries)

1. **Do not pass `orderBy`** for property fields such as `Tg`, `Td`, mechanical, or optical properties. Fetch candidates, parse numbers, and sort locally.
2. **Use one call for ordinary lookup questions**: when the user asks "query/find/show some", use `page=1` and `pageSize=50`, then present representative records that pass local validation.
3. **Use at most two calls for representative Top results**: if the first page has too few locally valid matches and the user asks for top/representative results, repeat the same query once with `pageSize=500`, then filter and sort locally. Do not jump directly to `5000`.
4. **Paginate only for explicit full-data tasks**: use larger `pageSize` or pagination only when the user explicitly asks for all results, a complete list, statistical distribution, export, or as many results as possible.
5. **Do not call sampled results an exact full-database count**: unless full pagination was performed, say "N locally validated records in this sample" instead of presenting a precise total match count.

### Filter Structure

```json
{
  "type": 2,
  "groupOperator": "and",
  "sub": [
    {
      "type": 1,
      "field": "field name (dataIndex)",
      "operator": "eq",
      "value": "value"
    }
  ]
}
```

- `type`: `1` = Simple condition, `2` = Compound condition (with `sub`)
- `groupOperator`: `"and"` | `"or"`
- `operator`: `eq` / `neq` / `like` / `gt` / `gte` / `lt` / `lte` / `in` / `nin` / `between`

## Field Name Mapping

**Important notes**:

1. Property values are usually numbers or numeric strings, with units encoded in the field name. For example, `GlassTransitionTemperature(Tg)(°C)` returns values such as `71.3` or `"71.3"` without a unit suffix.
2. `gt`/`lt`/`gte`/`lte` can be used to narrow candidate records. For example, `{"field": "GlassTransitionTemperature(Tg)(°C)", "operator": "gt", "value": "350"}` asks for Tg > 350°C candidates; still run a local `float()` validation after retrieval.
3. Each property field may have two equivalent spellings in the database: a compact form and a spaced form. Prefer the compact no-space form as the `dataIndex`.

### Basic Information

| User Term | dataIndex | Type | Notes |
|-----------|-----------|------|-------|
| DOI | `doi` | str | Paper DOI |
| Polymer name | `polymer_name` | str | e.g. `"PI"`, `"PU"` |
| Polymer type | `polymer_type` | str | e.g. `"Polyimide"`, `"Polyurethane"` |
| Feed ratio text | `feed_ratio_text` | str | Raw ratio text |
| Ratio values | `ratio_values_text` | str | e.g. `"6FDA:DDM = 1.04:1.00"` |
| Ratio type | `ratio_type` | str | `"mole"` / `"weight"` |
| Diamine ratio | `diamine_ratio` | str | e.g. `"ODA:TBDS = 0.05:49.58"` |
| Dianhydride ratio | `dianhydride_ratio` | str | e.g. `"PMDA:6FDA = 9.83:39.31"` |

### Monomer Structure (`monomer_1` ~ `monomer_19`)

| dataIndex | Type | Notes |
|-----------|------|-------|
| `monomer_N` | str | Abbreviated name of monomer N, e.g. `"6FDA"`, `"ODA"` |
| `monomer_N_fullname` | str | Full monomer name |
| `monomer_N_smiles` | smiles | Monomer SMILES |

N ranges from 1 to 19. Most records have 2 to 4 monomers.

### Molecular Weight

| User Term | dataIndex | Type | Unit |
|-----------|-----------|------|------|
| Number-average molecular weight Mn | `mn_value(g/mol)` | num | g/mol |
| Weight-average molecular weight Mw | `mw_value(g/mol)` | num | g/mol |
| PDI / dispersity | `pdi_value` | num | dimensionless |

### Thermal Properties

| User Term | dataIndex | Data Volume |
|-----------|-----------|-------------|
| Tg / glass transition temperature | `GlassTransitionTemperature(Tg)(°C)` | ~100k |
| Td / decomposition temperature | `DecompositionTemperature(Td)(°C)` | large |
| Tm / melting temperature | `MeltingTemperature(Tm)(°C)` | ~7k |
| Tc / crystallization temperature | `CrystallizationTemperature(Tc)(°C)` | ~2.4k |
| CTE / coefficient of thermal expansion | `CoefficientofThermalExpansion(CTE)(ppm/K)` | ~425 |
| Thermal conductivity | `ThermalConductivity(W/(m·K))` | ~1.7k |

Thermal property auxiliary fields use the property name as a suffix:
- `test_method_GlassTransitionTemperature(Tg)` - test method, e.g. DSC, TGA, DMA
- `heating_rate_GlassTransitionTemperature(Tg)(°C/min)` - heating rate
- `atmosphere_GlassTransitionTemperature(Tg)` - atmosphere, e.g. N2, Air
- `decomposition_criterion_DecompositionTemperature(Td)` - decomposition criterion, e.g. "5% weight loss"
- `test_conditions_GlassTransitionTemperature(Tg)` - test conditions
- `notes_GlassTransitionTemperature(Tg)` - notes

### Optical Properties

| User Term | dataIndex | Data Volume |
|-----------|-----------|-------------|
| Transmittance | `Transmittance(%)` | ~11.7k |
| Refractive index | `RefractiveIndex(n)(dimensionless)` | available in schema |
| Yellow index | `YellowIndex(YI)/WhitenessIndex(WI)(dimensionless)` | available |
| Haze | `Haze(%)` | ~349 |
| Birefringence | `Birefringence(Δn)(dimensionless)` | available |
| Cut-off wavelength | `Cut-offWavelength(λ_cut)(nm)` | ~1.4k |
| Abbe number | `AbbeNumber(νd)(dimensionless)` | available |

Optical property auxiliary fields:
- `wavelength_Transmittance(nm)` - measurement wavelength
- `thickness_Transmittance` - film thickness (str)
- `test_method_Transmittance` - test method
- `test_conditions_Transmittance` - test conditions
- `test_standard_Transmittance` - test standard
- `notes_Transmittance` - notes

### Mechanical Properties

| User Term | dataIndex | Data Volume |
|-----------|-----------|-------------|
| Tensile strength | `TensileStrength(MPa)` | ~19.9k |
| Tensile modulus / Young's modulus | `TensileModulus(GPa)` | ~14.4k |
| Elongation at break | `ElongationatBreak(%)` | ~7.8k |
| Flexural strength | `FlexuralStrength(MPa)` | ~3.3k |
| Flexural modulus | `FlexuralModulus(GPa)` | ~2.2k |
| Impact strength | `ImpactStrength(kJ/m²)` | ~3.0k |
| Shear strength | `ShearStrength(MPa)` | ~6.8k |
| Shore hardness | `ShoreHardness` | ~813 |
| Storage modulus | `StorageModulus(E'orG')(GPa)` | available |
| Loss modulus | `LossModulus(E''orG'')(GPa)` | available |
| Shear modulus | `ShearModulus(GPa)` | available |
| Poisson's ratio | `Poisson'sRatio(dimensionless)` | available |
| Tan Delta | `TanDelta(dimensionless)` | available |

Mechanical property auxiliary fields:
- `temperature_TensileStrength(°C)` - test temperature
- `frequency_TensileStrength(Hz)` - test frequency
- `test_method_TensileStrength` - test method
- `test_standard_TensileStrength` - test standard
- `test_conditions_TensileStrength` - test conditions
- `test_mode_TensileStrength` - test mode
- `measurement_direction_TensileStrength` - measurement direction
- `notes_TensileStrength` - notes

### Electrical Properties

| User Term | dataIndex | Data Volume |
|-----------|-----------|-------------|
| Dielectric constant Dk | `DielectricConstant(Dk)(dimensionless)` | available |
| Dielectric loss Df | `DielectricLoss(Df/tanδ)(dimensionless)` | available |
| Breakdown strength | `BreakdownStrength(kV/mm)` | ~255 |
| Volume resistivity | `VolumeResistivity(Ω·cm)` | ~1.6k |
| Surface resistivity | `SurfaceResistivity(Ω/sq)` | available |
| Electrical conductivity | `ElectricalConductivity(S/cm)` | available |

Electrical property auxiliary fields:
- `frequency_DielectricConstant(Dk)(Hz)` - test frequency
- `temperature_DielectricConstant(Dk)(°C)` - test temperature
- `thickness_DielectricConstant(Dk)` - thickness

### Other Properties

| User Term | dataIndex | Data Volume |
|-----------|-----------|-------------|
| Density | `Density(g/cm³)` | available |
| Water absorption | `WaterAbsorption(%)` | ~6.3k |
| Crystallinity | `Crystallinity(%)` | available |
| Crystallinity category | `Crystallinity(category)` | str |
| Solubility | `Solubility(category)` | str |
| Solvent uptake | `SolventUptake(%)` | available |
| Intrinsic viscosity | `IntrinsicViscosity(dL/g)` | available |
| Dynamic viscosity | `DynamicViscosity(Pa·s)` | available |
| Melt viscosity | `MeltViscosity(Pa·s)` | available |
| Gas permeability | `GasPermeability(Barrer)` | available |
| Gas separation selectivity | `GasSeparationSelectivity(dimensionless)` | available |

### Synthesis Process Fields

| dataIndex | Notes |
|-----------|-------|
| `Synthesis_Solvent` | Synthesis solvent |
| `Synthesis_Solid_Content` | Solid content |
| `Synthesis_Reaction_Temperature` | Reaction temperature |
| `Synthesis_Reaction_Time` | Reaction time |
| `Synthesis_Atmosphere` | Reaction atmosphere |
| `Solution_Viscosity` | Solution viscosity |
| `Coating_Method` | Coating method |
| `Film_Thickness` | Film thickness |
| `Post_Processing_Type` | Post-processing type |
| `Post_Thermal_Temperature_Schedule` | Thermal treatment schedule |

### System Fields (Ignore in User-Facing Output)

- `_id`: MongoDB ObjectID
- `a1b2c3d4e5_is_locked` / `a1b2c3d4e5_owner_id` / `a1b2c3d4e5_source` / `a1b2c3d4e5_status`
- `authors`: contributor information
- `createTime` / `updateTime`: timestamps

## Execution Strategy

### Exact Query (by DOI / Polymer Name)

When the user asks for properties of a DOI or a specific polymer, use direct `eq` filters and limit `selectedFields` to the fields needed.

```json
{
  "tableAk": "123zl00",
  "page": 1,
  "pageSize": 50,
  "filters": {
    "type": 2, "groupOperator": "and",
    "sub": [{"type": 1, "field": "doi", "operator": "eq", "value": "10.1021/..."}]
  },
  "selectedFields": ["polymer_name", "polymer_type", "GlassTransitionTemperature(Tg)(°C)", "DecompositionTemperature(Td)(°C)", "monomer_1", "monomer_2", "monomer_3", "monomer_4"]
}
```

**Note**: for the first lookup of a DOI, consider leaving `selectedFields` unset or using only a small field list, because it may be unclear which properties were entered for that paper. Refine the next query based on returned fields.

### Numeric Range Filtering (by Property Value)

When the user asks for "polymers with Tg > 350°C", use the `gt` operator to narrow candidates, but **convert field values to numbers and validate locally after retrieval**. For ordinary questions, fetch only the first page sample; do not automatically do full pagination and do not pass `orderBy`.

```json
{
  "tableAk": "123zl00",
  "page": 1,
  "pageSize": 50,
  "filters": {
    "type": 2, "groupOperator": "and",
    "sub": [{"type": 1, "field": "GlassTransitionTemperature(Tg)(°C)", "operator": "gt", "value": "350"}]
  },
  "selectedFields": ["polymer_name", "polymer_type", "GlassTransitionTemperature(Tg)(°C)", "monomer_1", "monomer_2", "monomer_3", "monomer_4", "monomer_1_smiles", "monomer_2_smiles"]
}
```

Result handling:

1. Read page records from `data.list`; read the server-side candidate count from `data.count`.
2. For each record, run local validation such as `float(record["GlassTransitionTemperature(Tg)(°C)"]) > 350`.
3. If the page contains records that do not meet the threshold after local validation, describe `data.count` as the "server-side candidate count", not as the "exact number of matching records".
4. For ordinary requests such as "query/find/show some", present representative locally validated records from this page and the candidate count, and state that this is not a complete list.
5. If the user needs representative Top results and the first page has too few valid hits, expand once to `pageSize=500` and sort locally by numeric value.
6. Only when the user explicitly asks for all results, complete lists, statistical distribution, export, or maximum coverage, paginate (`page=2`, `page=3`, ...) or use `pageSize=5000`; throttle requests and avoid large bursts.

Python parsing template:

```python
data = response_json.get("data", {})
candidate_count = data.get("count", 0)
rows = data.get("list", [])
matched = []
for row in rows:
    try:
        value = float(row.get("GlassTransitionTemperature(Tg)(°C)", ""))
    except (TypeError, ValueError):
        continue
    if value > 350:
        matched.append(row)
```

### Analysis and Recommendation (Design Guidance)

When the user asks for suggestions to synthesize a polymer with a target property:

1. Use a range filter to fetch the first page of candidates, then run local numeric validation.
2. If the user explicitly needs statistics or design guidance, expand to a `pageSize=500` sample first; only paginate enough samples or all candidates when full coverage is explicitly requested.
3. Summarize the `polymer_type` distribution to identify dominant polymer families.
4. Count `monomer_1` ~ `monomer_4` frequencies to identify frequent monomers.
5. Analyze common SMILES structural features such as aromatic rings, fluorinated groups, or alicyclic groups.
6. Combine observed data patterns with polymer chemistry knowledge to provide structural design suggestions.

### Combined Filtering

AND/OR combinations are supported:

```json
{
  "filters": {
    "type": 2, "groupOperator": "and",
    "sub": [
      {"type": 1, "field": "polymer_type", "operator": "eq", "value": "Polyimide"},
      {"type": 1, "field": "Transmittance(%)", "operator": "gt", "value": "90"}
    ]
  }
}
```

## Key Behavior Notes

1. **Use server-side numeric ranges only to narrow candidates, then validate locally**: property fields are usually numbers or numeric strings; `gt`/`lt`/`gte`/`lte` can reduce candidates, but final matches must pass local `float()` validation.
2. **Field names include units**: units such as `(°C)`, `(%)`, and `(MPa)` are part of the field name; values usually do not include unit strings.
3. **Response fields**: records are in `data.list`, not `data.rows`; the candidate count is in `data.count`.
4. **Local validation is required** for numeric range queries to avoid reporting server-side candidate counts as exact match counts.
5. **Do not pass `orderBy`** for property sorting; sort locally to avoid backend `$sort` parameter errors and repeated failed queries.
6. **`pageSize` max is 5000**: for ordinary Q&A use `pageSize=20~50`; for representative Top results expand at most to `500`; use `5000` or pagination only for explicit full-list/statistics/export requests.
7. **Two field-name styles are equivalent**: `GlassTransitionTemperature(Tg)(°C)` and `Glass Transition Temperature (Tg) (°C)` can both work; prefer the compact form.
8. **`like ""` for non-empty matching**: for string fields, `"operator": "like", "value": ""` can match non-empty records. It may not work for numeric fields; use `gt` with `"0"` or omit that field filter.
9. **When presenting results**, filter out system fields (`a1b2c3d4e5_*`, `authors`, `_id`, timestamps) and show only meaningful user-facing data.
10. **The API has rate limits**: avoid large bursts of concurrent requests. If `count=0` with no error code, it may be transient rate limiting; retry later.
