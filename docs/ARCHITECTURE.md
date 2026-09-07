# ArcOfMarket 数据层架构

## 唯一生产链路

```text
config/market-data-v2.json
        ↓
Yahoo / Wikipedia / FRED / Cboe / CFTC / OFR / U.S. Treasury
        ↓ 只在内存中保留抓取结果
fetchers → collector → calculations + scores
        ↓ 质量门 + JSON Schema
releases/market/2.2.0/<as-of>/<release-id>.json
        ├─ ledger.jsonl
        └─ latest.json
```

仓库不再使用 Source Registry → Snapshot → Indicator Release → Signal Release → Bridge 的多层
发布架构。`Market Release` 是数据、评分、来源状态和复算证据的单一公开契约。Cloud 只消费该
契约，不重复联网抓取，也不复制评分公式。

## 代码职责

| 位置 | 职责 |
| --- | --- |
| `config/market-data-v2.json` | 数据范围、代码表、来源和公开口径 |
| `src/arc_market/fetchers/` | 联网读取和来源字段规范化，不落原始文件 |
| `src/arc_market/collection.py` | 截止日、完整性、覆盖率和降级策略 |
| `src/arc_market/calculations.py` | 收益、均线、广度、行业、ROC35、宏观等纯计算 |
| `src/arc_market/scores.py` | 趋势、参与度、周期、风险和综合评分 |
| `src/arc_market/release.py` | 契约验证、内容寻址、不可变发布和 ledger |
| `src/arc_market/research_store.py` | 本地 Point-in-Time 观察存储，供未来回放 |
| `scripts/market_data.py` | 唯一生产采集入口 |
| `scripts/research_store.py` | 本地研究库入口，不进入公开 Release |

## 失败边界

- 核心 Yahoo 行情失败或不足 252 个完整交易日：停止发布；
- 广度、FRED、Cboe、CFTC、OFR、财政部失败：默认发布 `DEGRADED`，严格模式停止；
- Yahoo 缺日线时不使用小时线修复值冒充正式收盘；
- 所有来源以核心市场日为截止日，禁止混入未来观察；
- NaN、Infinity、未知字段或原始 OHLCV/完整供应商历史进入 Release：停止发布；
- ICE/BofA 来源或系列进入公开 Release：停止发布；
- 同日已有 `APPROVED` Release 时，后续 `DEGRADED` 运行不得覆盖 latest。
