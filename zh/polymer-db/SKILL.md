---
name: polymer-db
version: 1.0.0
description: "高分子数据库检索：查询 Polymer-Data-Bank 中的聚合物数据，支持按 DOI、聚合物名称、性能指标等条件检索，返回结构、热性能、光学性能、力学性能等信息。当用户询问聚合物性质（Tg/Td/透光率/力学性能等）、查找特定论文中的聚合物数据、或需要按性能筛选聚合物时使用。"
---

# 高分子数据库检索 (Polymer-Data-Bank)

## 接口信息

- **Endpoint**: `POST https://open.bohrium.com/openapi/v1/database/common_data/list`
- **认证**: Header `accessKey: $BOHR_ACCESS_KEY`
- **tableAk**: `123zl00`（Polymer-Data-Bank，28万+条记录）
- **数据来源**: Bohrium Materials Database

## 请求格式

```bash
curl -s -X POST 'https://open.bohrium.com/openapi/v1/database/common_data/list' \
  -H 'Content-Type: application/json' \
  -H "accessKey: $BOHR_ACCESS_KEY" \
  -d '<JSON body>'
```

### 基本请求体

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

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `tableAk` | string | 是 | 固定 `"123zl00"` |
| `page` | int | 是 | 页码，从 1 开始 |
| `pageSize` | int | 是 | 每页条数，最大 5000 |
| `filters` | object | 否 | 过滤条件（Filter 结构） |
| `selectedFields` | []string | 否 | 只返回指定字段 |
| `orderBy` | []object | 否 | 排序 `{"field": "xxx", "order": "asc/desc"}` |

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

**重要限制**：所有性能字段均为 **string 类型**（值如 `"71.3 °C"`、`"[255 °C,288 °C]"`），`gt`/`lt` 等操作符做字典序比较而非数值比较。数值范围筛选必须在客户端解析处理。

## 字段名映射（用户常用说法 → dataIndex）

### 基本信息
| 用户说法 | dataIndex | 示例值 |
|---------|-----------|--------|
| DOI | `doi` | `"10.1021/acs.macromol.9b02359"` |
| 聚合物名 | `polymer_name` | `"PI"`, `"PU"` |
| 聚合物类型 | `polymer_type` | `"Polyimide"` |
| 单体组成/结构 | `components` | `"6FDA:O=C1OC...;ODA:Nc1ccc..."` |
| 配比 | `feed_ratio_text` | `"DABz/m-BAPS = 1/1"` |
| 配比类型 | `ratio_type` | `"mole"`, `"weight"` |

### 热性能
| 用户说法 | dataIndex | 附属字段 |
|---------|-----------|---------|
| Tg / 玻璃化转变温度 | `GlassTransitionTemperature(Tg)` | `test_method_GlassTransitionTemperature(Tg)`, `heating_rate_GlassTransitionTemperature(Tg)`, `atmosphere_GlassTransitionTemperature(Tg)` |
| Td / 热分解温度 | `DecompositionTemperature(Td)` | `decomposition_criterion_DecompositionTemperature(Td)`, `atmosphere_DecompositionTemperature(Td)` |
| Tm / 熔融温度 | `MeltingTemperature(Tm)` | `test_method_MeltingTemperature(Tm)` |
| Tc / 结晶温度 | `CrystallizationTemperature(Tc)` | — |
| CTE / 热膨胀系数 | `CoefficientofThermalExpansion(CTE)` | — |
| 热导率 | `ThermalConductivity` | — |

### 光学性能
| 用户说法 | dataIndex | 附属字段 |
|---------|-----------|---------|
| 透光率 / 透过率 | `Transmittance` | `wavelength_Transmittance`, `thickness_Transmittance` |
| 折射率 | `RefractiveIndex(n)` | `wavelength_RefractiveIndex(n)` |
| 黄色指数 | `YellowIndex(YI)/WhitenessIndex(WI)` | — |
| 雾度 | `Haze` | — |
| 双折射 | `Birefringence(Δn)` | — |
| 截止波长 | `Cut-offWavelength(λ_cut)` | — |
| 阿贝数 | `AbbeNumber(νd)` | — |

### 力学性能
| 用户说法 | dataIndex |
|---------|-----------|
| 拉伸强度 | `TensileStrength` |
| 拉伸模量 / 杨氏模量 | `TensileModulus` |
| 断裂伸长率 | `ElongationatBreak` |
| 弯曲强度 | `FlexuralStrength` |
| 弯曲模量 | `FlexuralModulus` |
| 冲击强度 | `ImpactStrength` |
| 剪切强度 | `ShearStrength` |
| 邵氏硬度 | `ShoreHardness` |

### 电学性能
| 用户说法 | dataIndex |
|---------|-----------|
| 介电常数 Dk | `DielectricConstant(Dk)` |
| 介电损耗 Df | `DielectricLoss(Df/tanδ)` |
| 击穿场强 | `BreakdownStrength` |
| 体积电阻率 | `VolumeResistivity` |
| 质子电导率 | `ProtonConductivity` |

### 分子量
| 用户说法 | dataIndex |
|---------|-----------|
| 数均分子量 Mn | `mn_value` |
| PDI / 分散度 | `pdi_value` |

## 执行策略

### 精确查询（Q1 类型）

用户问"某 DOI/某聚合物的性质"：直接查询，`selectedFields` 限定需要的字段。

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

### 数值范围筛选（Q2 类型）

用户问"Tg > 350°C 的聚合物"：

1. **不能**直接用 `gt` 操作符（字段是 string，字典序比较不准确）
2. **正确做法**：用 `like` 操作符排除空值（`"value": ""`），设置 `pageSize: 5000`，拉取数据后客户端解析数值

```python
import re

def parse_value_celsius(val_str):
    """解析带单位的温度字符串，统一转为 °C"""
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

3. 筛选后做统计分析（类型分布、高频单体等）

### 分析建议类（Q3 类型）

用户问"想合成 XX 性能的聚合物，有什么建议"：

1. 先用 `like ""` 拉取有该性能数据的记录（最多 5000 条/页，可能需多页）
2. 客户端解析数值，筛选满足条件的记录
3. 统计 `polymer_type` 分布、`components` 中高频单体
4. 基于数据规律给出结构设计建议

## 数据格式说明

### components 字段格式
```
单体名:SMILES;单体名:SMILES;...
```
例如：`6FDA:O=C1OC(=O)c2cc(...)ccc21;ODA:Nc1ccc(Oc2ccc(N)cc2)cc1`

### 性能值格式（均为 string）
- 单值：`"71.3 °C"`
- 多值：`"[255 °C,288 °C]"`
- 描述性：`"over 90 %"`, `"greater than 350 °C"`
- 带误差：`"90.8% ± 0.6%"`

### 系统字段（忽略）
- `_id`: MongoDB ObjectID
- `a1b2c3d4e5_is_locked`: 锁定标记
- `a1b2c3d4e5_owner_id`: 数据所有者
- `a1b2c3d4e5_source`: 数据来源
- `a1b2c3d4e5_status`: 审核状态
- `authors`: 录入人信息
- `createTime` / `updateTime`: 时间戳

## 注意事项

1. **单位不统一**：同一字段内可能混合 °C、K、°F，必须做单位转换
2. **字符串数值**：所有性能字段都是 string，数值比较必须客户端解析
3. **多值字段**：一条记录的某个性能可能有多个值（数组格式如 `"[val1,val2]"`）
4. **pageSize 上限**：最大 5000。数据量大时需分页（total count 在 `data.count`）
5. **字段名含特殊字符**：如 `GlassTransitionTemperature(Tg)` 含括号，JSON key 直接使用
6. **like 空字符串**：`"operator": "like", "value": ""` 可匹配所有非空记录
7. **向用户展示结果**时，过滤掉系统字段（`a1b2c3d4e5_*`、`authors`），只展示有意义的数据
