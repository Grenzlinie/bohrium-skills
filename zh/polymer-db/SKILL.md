---
name: polymer-db
version: 2.0.2
description: "高分子数据库检索：查询 Polymer-Data-Bank 中的聚合物数据（28万+条），支持按 DOI、聚合物名称、性能指标等条件检索，返回结构、热性能、光学性能、力学性能等信息。当用户询问聚合物性质（Tg/Td/透光率/力学性能等）、查找特定论文中的聚合物数据、或需要按性能筛选聚合物时使用。"
---

# 高分子数据库检索 (Polymer-Data-Bank)

## 接口信息

- **Endpoint**: `POST https://open.bohrium.com/openapi/v2/database/common_data/list`
- **认证**: Header `Authorization: Bearer $BOHR_ACCESS_KEY`
- **tableAk**: `123zl00`（Polymer-Data-Bank，28万+条记录）
- **数据来源**: Bohrium Materials Database

## 请求格式

```bash
curl -s -X POST 'https://open.bohrium.com/openapi/v2/database/common_data/list' \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $BOHR_ACCESS_KEY" \
  -d '<JSON body>'
```

### 基本请求体

```json
{
  "tableAk": "123zl00",
  "page": 1,
  "pageSize": 50,
  "filters": { ... },
  "selectedFields": ["field1", "field2"]
}
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `tableAk` | string | 是 | 固定 `"123zl00"` |
| `page` | int | 是 | 页码，从 1 开始 |
| `pageSize` | int | 是 | 每页条数，最大 5000 |
| `filters` | object | 否 | 过滤条件（Filter 结构） |
| `selectedFields` | []string | 否 | 只返回指定字段（推荐使用以减少响应体积） |
| `orderBy` | []object | 否 | 不推荐使用。此接口排序参数容易触发 `$sort key ordering must be 1 or -1`；性能筛选默认不要传 `orderBy`，返回后在本地排序。 |

### 响应结构

接口返回的记录列表在 `data.list`，总候选数在 `data.count`。

```json
{
  "data": {
    "count": 123,
    "list": [{ "polymer_name": "...", "GlassTransitionTemperature(Tg)(°C)": "455.0" }]
  }
}
```

**不要使用 `data.rows` 读取结果。** 如果 `data.count` 有值但 `data.list` 为空，先检查 `page`/`pageSize`、字段名、排序参数和响应结构，不要立刻判断为数据库无结果。

### 调用策略（避免反复查询）

1. **不要传 `orderBy`**：尤其是 `Tg/Td/力学/光学` 等性能字段。先拉候选，转数字后在本地排序。
2. **普通查询只调用一次**：用户只说"查询一下/有哪些/给我看看"时，用 `page=1&pageSize=50`，展示本页本地校验通过的代表记录即可。
3. **代表性 Top 结果最多两次调用**：如果第一页本地命中太少，而用户需要 Top/代表性列表，可把同一查询扩大到 `pageSize=500` 再本地过滤排序。不要直接跳到 `5000`。
4. **只有明确全量任务才分页**：用户明确要求"全部/完整列表/统计分布/导出/尽可能全量"时，才用更大 `pageSize` 或分页拉取。
5. **不要把采样结果说成全库精确总数**：没有全量分页时，只能说"在本次采样中本地校验得到 N 条"。

### Filter 结构

```json
{
  "type": 2,
  "groupOperator": "and",
  "sub": [
    {
      "type": 1,
      "field": "字段名（dataIndex）",
      "operator": "eq",
      "value": "值"
    }
  ]
}
```

- `type`: `1` = 单条件（Simple），`2` = 组合条件（Compound，含 sub）
- `groupOperator`: `"and"` | `"or"`
- `operator`: `eq` / `neq` / `like` / `gt` / `gte` / `lt` / `lte` / `in` / `nin` / `between`

## 字段名映射

**重要说明**：

1. 所有性能字段的值通常是纯数字或数字字符串，单位已编码在字段名中。例如 `GlassTransitionTemperature(Tg)(°C)` 的值为 `71.3` 或 `"71.3"`（不带单位字符串）。
2. `gt`/`lt`/`gte`/`lte` 操作符可用于缩小候选集。例如 `{"field": "GlassTransitionTemperature(Tg)(°C)", "operator": "gt", "value": "350"}` 可请求 Tg > 350°C 的候选记录；返回后仍需本地 `float()` 二次校验。
3. 数据库中每个性能字段存在**两种写法**（紧凑版和空格版），两者等价，推荐使用紧凑版（无空格）作为 `dataIndex`。

### 基本信息

| 用户说法 | dataIndex | 数据类型 | 说明 |
|---------|-----------|----------|------|
| DOI | `doi` | str | 论文 DOI |
| 聚合物名 | `polymer_name` | str | 如 `"PI"`, `"PU"` |
| 聚合物类型 | `polymer_type` | str | 如 `"Polyimide"`, `"Polyurethane"` |
| 配比描述 | `feed_ratio_text` | str | 原始配比文本 |
| 配比数值 | `ratio_values_text` | str | 如 `"6FDA:DDM = 1.04:1.00"` |
| 配比类型 | `ratio_type` | str | `"mole"` / `"weight"` |
| 二胺配比 | `diamine_ratio` | str | 如 `"ODA:TBDS = 0.05:49.58"` |
| 二酐配比 | `dianhydride_ratio` | str | 如 `"PMDA:6FDA = 9.83:39.31"` |

### 单体结构（monomer_1 ~ monomer_19）

| dataIndex | 数据类型 | 说明 |
|-----------|----------|------|
| `monomer_N` | str | 第 N 个单体的缩写名（如 `"6FDA"`, `"ODA"`） |
| `monomer_N_fullname` | str | 单体全名 |
| `monomer_N_smiles` | smiles | 单体 SMILES 结构式 |

N 取值 1~19。大多数记录有 2~4 个单体。

### 分子量

| 用户说法 | dataIndex | 数据类型 | 单位 |
|---------|-----------|----------|------|
| 数均分子量 Mn | `mn_value(g/mol)` | num | g/mol |
| 重均分子量 Mw | `mw_value(g/mol)` | num | g/mol |
| PDI / 分散度 | `pdi_value` | num | 无量纲 |

### 热性能

| 用户说法 | dataIndex | 数据量 |
|---------|-----------|--------|
| Tg / 玻璃化转变温度 | `GlassTransitionTemperature(Tg)(°C)` | ~100k |
| Td / 热分解温度 | `DecompositionTemperature(Td)(°C)` | 大量 |
| Tm / 熔融温度 | `MeltingTemperature(Tm)(°C)` | ~7k |
| Tc / 结晶温度 | `CrystallizationTemperature(Tc)(°C)` | ~2.4k |
| CTE / 热膨胀系数 | `CoefficientofThermalExpansion(CTE)(ppm/K)` | ~425 |
| 热导率 | `ThermalConductivity(W/(m·K))` | ~1.7k |

每个热性能字段有以下附属字段（前缀 + 性能名）：
- `test_method_GlassTransitionTemperature(Tg)` — 测试方法（如 DSC, TGA, DMA）
- `heating_rate_GlassTransitionTemperature(Tg)(°C/min)` — 升温速率
- `atmosphere_GlassTransitionTemperature(Tg)` — 气氛（如 N2, Air）
- `decomposition_criterion_DecompositionTemperature(Td)` — 分解标准（如 "5% weight loss"）
- `test_conditions_GlassTransitionTemperature(Tg)` — 测试条件
- `notes_GlassTransitionTemperature(Tg)` — 备注

### 光学性能

| 用户说法 | dataIndex | 数据量 |
|---------|-----------|--------|
| 透光率 / 透过率 | `Transmittance(%)` | ~11.7k |
| 折射率 | `RefractiveIndex(n)(dimensionless)` | 有（schema 声明） |
| 黄色指数 | `YellowIndex(YI)/WhitenessIndex(WI)(dimensionless)` | 有 |
| 雾度 | `Haze(%)` | ~349 |
| 双折射 | `Birefringence(Δn)(dimensionless)` | 有 |
| 截止波长 | `Cut-offWavelength(λ_cut)(nm)` | ~1.4k |
| 阿贝数 | `AbbeNumber(νd)(dimensionless)` | 有 |

光学性能附属字段：
- `wavelength_Transmittance(nm)` — 测试波长
- `thickness_Transmittance` — 薄膜厚度（str）
- `test_method_Transmittance` — 测试方法
- `test_conditions_Transmittance` — 测试条件
- `test_standard_Transmittance` — 测试标准
- `notes_Transmittance` — 备注

### 力学性能

| 用户说法 | dataIndex | 数据量 |
|---------|-----------|--------|
| 拉伸强度 | `TensileStrength(MPa)` | ~19.9k |
| 拉伸模量 / 杨氏模量 | `TensileModulus(GPa)` | ~14.4k |
| 断裂伸长率 | `ElongationatBreak(%)` | ~7.8k |
| 弯曲强度 | `FlexuralStrength(MPa)` | ~3.3k |
| 弯曲模量 | `FlexuralModulus(GPa)` | ~2.2k |
| 冲击强度 | `ImpactStrength(kJ/m²)` | ~3.0k |
| 剪切强度 | `ShearStrength(MPa)` | ~6.8k |
| 邵氏硬度 | `ShoreHardness` | ~813 |
| 储能模量 | `StorageModulus(E'orG')(GPa)` | 有 |
| 损耗模量 | `LossModulus(E''orG'')(GPa)` | 有 |
| 剪切模量 | `ShearModulus(GPa)` | 有 |
| 泊松比 | `Poisson'sRatio(dimensionless)` | 有 |
| Tan Delta | `TanDelta(dimensionless)` | 有 |

力学性能附属字段：
- `temperature_TensileStrength(°C)` — 测试温度
- `frequency_TensileStrength(Hz)` — 测试频率
- `test_method_TensileStrength` — 测试方法
- `test_standard_TensileStrength` — 测试标准
- `test_conditions_TensileStrength` — 测试条件
- `test_mode_TensileStrength` — 测试模式
- `measurement_direction_TensileStrength` — 测量方向
- `notes_TensileStrength` — 备注

### 电学性能

| 用户说法 | dataIndex | 数据量 |
|---------|-----------|--------|
| 介电常数 Dk | `DielectricConstant(Dk)(dimensionless)` | 有 |
| 介电损耗 Df | `DielectricLoss(Df/tanδ)(dimensionless)` | 有 |
| 击穿场强 | `BreakdownStrength(kV/mm)` | ~255 |
| 体积电阻率 | `VolumeResistivity(Ω·cm)` | ~1.6k |
| 表面电阻率 | `SurfaceResistivity(Ω/sq)` | 有 |
| 电导率 | `ElectricalConductivity(S/cm)` | 有 |

电学性能附属字段：
- `frequency_DielectricConstant(Dk)(Hz)` — 测试频率
- `temperature_DielectricConstant(Dk)(°C)` — 测试温度
- `thickness_DielectricConstant(Dk)` — 厚度

### 其他性能

| 用户说法 | dataIndex | 数据量 |
|---------|-----------|--------|
| 密度 | `Density(g/cm³)` | 有 |
| 吸水率 | `WaterAbsorption(%)` | ~6.3k |
| 结晶度 | `Crystallinity(%)` | 有 |
| 结晶度（类别） | `Crystallinity(category)` | str |
| 溶解性 | `Solubility(category)` | str |
| 溶剂吸收率 | `SolventUptake(%)` | 有 |
| 特性粘度 | `IntrinsicViscosity(dL/g)` | 有 |
| 动力学粘度 | `DynamicViscosity(Pa·s)` | 有 |
| 熔体粘度 | `MeltViscosity(Pa·s)` | 有 |
| 气体渗透率 | `GasPermeability(Barrer)` | 有 |
| 气体分离选择性 | `GasSeparationSelectivity(dimensionless)` | 有 |

### 合成工艺字段

| dataIndex | 说明 |
|-----------|------|
| `Synthesis_Solvent` | 合成溶剂 |
| `Synthesis_Solid_Content` | 固含量 |
| `Synthesis_Reaction_Temperature` | 反应温度 |
| `Synthesis_Reaction_Time` | 反应时间 |
| `Synthesis_Atmosphere` | 反应气氛 |
| `Solution_Viscosity` | 溶液粘度 |
| `Coating_Method` | 涂覆方法 |
| `Film_Thickness` | 成膜厚度 |
| `Post_Processing_Type` | 后处理类型 |
| `Post_Thermal_Temperature_Schedule` | 热处理温度程序 |

### 系统字段（忽略，不展示给用户）

- `_id`: MongoDB ObjectID
- `a1b2c3d4e5_is_locked` / `a1b2c3d4e5_owner_id` / `a1b2c3d4e5_source` / `a1b2c3d4e5_status`
- `authors`: 录入人信息
- `createTime` / `updateTime`: 时间戳

## 执行策略

### 精确查询（按 DOI / 聚合物名）

用户问"某 DOI / 某聚合物的性质"：直接用 `eq` 过滤，`selectedFields` 限定需要的字段。

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

**注意**：首次查某个 DOI 时，建议不限 `selectedFields`（或少限制），因为不确定该论文录入了哪些性能字段。根据返回字段再做后续精确查询。

### 数值范围筛选（按性能值过滤）

用户问"Tg > 350°C 的聚合物"：使用 `gt` 操作符缩小候选集，但**返回后必须把字段值转为数字并在本地二次校验**。普通查询只取第一页样例，不要自动全量分页，不要传 `orderBy`。

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

结果处理要点：

1. 从 `data.list` 读取本页记录，从 `data.count` 读取服务端候选总数。
2. 对每条记录执行 `float(record["GlassTransitionTemperature(Tg)(°C)"]) > 350` 这类本地校验。
3. 如果本页混入不满足阈值的记录，把 `data.count` 表述为"服务端候选数"，不要称为"满足条件的精确总数"。
4. 对"查询一下/有哪些/给我看看"这类普通请求，展示本页本地校验通过的代表记录和候选总数即可，并说明不是完整列表。
5. 如果用户需要代表性 Top 结果且第一页命中太少，最多扩大到 `pageSize=500` 采样一次，并在本地按数值排序。
6. 只有用户明确要求"全部/完整列表/统计分布/导出/尽可能全量"时，才分页拉取（page=2, 3, ...）或使用 `pageSize=5000`，并控制请求节奏，避免短时间大量并发。

Python 解析模板：

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

### 分析建议类（设计指导）

用户问"想合成某性能的聚合物，有什么建议"：

1. 用范围过滤先拉取第一页候选记录，并做本地数值校验
2. 若用户明确需要统计/设计建议，先扩大到 `pageSize=500` 采样；只有明确要全量时才分页拉取足够样本或全量候选
3. 统计 `polymer_type` 分布，找出主流体系
4. 统计 `monomer_1` ~ `monomer_4` 出现频次，找出高频单体
5. 分析 SMILES 结构中的共同特征（芳环、含氟、脂环等）
6. 结合高分子化学知识给出结构设计建议

### 组合筛选

支持多条件 AND/OR 组合：

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

## 关键行为说明

1. **数值范围先服务端缩小、再本地校验**：性能字段通常是数字或数字字符串，`gt`/`lt`/`gte`/`lte` 可用于缩小候选集，但最终命中必须用 `float()` 校验。
2. **字段名带单位**：字段名中直接包含单位（如 `(°C)`、`(%)`、`(MPa)`），值本身通常不带单位字符串。
3. **响应字段**：记录列表是 `data.list`，不是 `data.rows`；总候选数是 `data.count`。
4. **本地校验必做**：数值范围查询返回后必须 `float()` 二次过滤，避免把服务端候选数误报为精确命中数。
5. **不要传 `orderBy`**：性能字段排序在本地完成，避免后端 `$sort` 参数错误导致重复查询。
6. **pageSize 上限 5000**：大数据量需分页，但普通问答默认 `pageSize=20~50`；代表性 Top 结果最多扩大到 `500`；只有明确要求全量/统计/导出时才用 `5000` 或分页。
7. **两种字段名等价**：`GlassTransitionTemperature(Tg)(°C)` 和 `Glass Transition Temperature (Tg) (°C)` 均可用，推荐用紧凑版。
8. **`like ""` 筛非空**：对 str 类型字段可用 `"operator": "like", "value": ""` 匹配所有非空记录。对 num 类型字段可能不适用，改用 `gt` + `"0"` 或直接不过滤该字段。
9. **向用户展示结果时**：过滤掉系统字段（`a1b2c3d4e5_*`、`authors`、`_id`、时间戳），只展示有意义的数据。
10. **API 有调用频率限制**：避免短时间内大量并发请求。如返回 count=0 且无错误码，可能是临时限流，稍后重试。
