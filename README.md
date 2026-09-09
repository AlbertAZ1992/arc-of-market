# ArcOfMarket Open Market Data

ArcOfMarket 的公开美股数据与研究信号层。它每天从公开网页和免费接口读取必要输入，在内存中
完成计算，只向 GitHub 发布一个紧凑、可校验的 `Market Release`。账户、订阅、AI Brief、提醒
和个性化产品逻辑属于独立的 ArcOfMarket Cloud。

## 当前能力

- 市场：SPY、QQQ、DIA、IWM 的收益、MA50/MA200、回撤和实现波动率；
- 趋势：SPY、QQQ 的 MA5/10/20/50 和多因子 Trend Score；
- 参与度：三组指数广度、RSP/SPY、QQEW/QQQ 和 Participation Score；
- 风格：对外名 NR35、内部标识 `roc35`，保持 VTV/QQQ 35 日公式和复算证据；
- 周期：SMH/QQQ、小盘/大盘、周期/防守行业与 Cycle Score；
- 风险：VIX 当前读数、SPY 波动/回撤、利率、OFR 与 Risk Score；
- 仓位：CFTC VIX TFF 历史净持仓占未平仓量；
- 行业与 Mega7：轻量阶段收益、相对强弱和排名；
- 宏观：FRED 的利率、流动性、通胀和就业紧凑读数；
- 综合状态：透明权重的 `RISK_ON / WATCH / DEFENSIVE`，附分数与置信度。

首发不接入主题 ETF、SEC 13F、ICE/BofA 信用利差、完整 Cboe VIX 历史或期权链。CFTC TFF
仓位时间序列属于公开数据能力，但不把 Asset Manager 直接宣传为“Smart Money”。

## 唯一数据链

源码与正式 Market Release 都保存在默认的 `main` 分支。打开仓库即可检查当前
`latest.json`、不可变历史文件和生成它们的代码，不需要切换到单独的数据分支。

```text
config/market-data-v2.json
        ↓
fetchers（仅内存）→ collector → calculations + scores
        ↓
contracts/market-release.schema.json
        ↓
releases/market/2.2.0/<as-of>/<release-id>.json
        ├─ ledger.jsonl
        └─ latest.json
```

旧 Snapshot、Indicator Release、Signal Release、Bridge 和周频重复采集已经删除。周度产品直接
读取当周最后一个日频 Release。

## 旗舰策略输入与历史回溯

Market Release 2.2.0 额外提供 `coreRotationInputs`，供 Cloud 的
`us-core-rotation@1.0.0` 确定性规则使用。数据项目不生成用户组合、不调用 AI，也不处理订阅。

最近一个月的回溯观察保存在 `releases/history/roc35-v1.0.0.json`。它使用当前可得的复权日线
重算，并明确标记为历史回溯；不会生成过去日期的正式 Market Release，不写入
`releases/market/ledger.jsonl`，也不声称是当日实发信号。重新生成：

```bash
uv run python scripts/backfill_rotation.py \
  --start 2026-08-03 \
  --end 2026-09-03 \
  --output releases/history/roc35-v1.0.0.json
```

## 本地运行

```bash
uv sync --locked --group dev
uv run python scripts/market_data.py --strict
```

指定目标日期：

```bash
uv run python scripts/market_data.py --as-of 2026-08-28 --strict
```

Yahoo 日线缺失时不会用小时数据修复收盘。相同输入、方法版本和代码提交会得到相同内容寻址
Release ID；同日已通过的 Release 不会被后续降级运行覆盖。

## Point-in-Time Research Store

本地研究库用于从今天开始积累可回放观察，不进入 Git：

```bash
uv run python scripts/research_store.py init
uv run python scripts/research_store.py ingest-latest
uv run python scripts/research_store.py status
```

它只保存 Release、来源可用时间、评分和分项证据，不保存第三方原始行情。完整说明见
[Research Store 与回测路线](docs/RESEARCH_STORE_AND_BACKTEST.md)。

## 验证

```bash
uv run ruff format --check scripts tests src
uv run ruff check scripts tests src
uv run ty check scripts src
uv run pytest -q
```

架构、方法和公开边界：

- [数据层架构](docs/ARCHITECTURE.md)
- [Signal v2 方法](docs/SIGNAL_METHODOLOGY.md)
- [数据来源与公开边界](docs/DATA_SOURCES_AND_PUBLICATION.md)

维护与再现：

- 日更由 [GitHub Actions](.github/workflows/daily.yml) 执行，验证通过后将正式发布物提交回
  `main`，再通知 Cloud 生成邮报与邮件；
- 本地研究库和回测边界见
  [Research Store 与回测路线](docs/RESEARCH_STORE_AND_BACKTEST.md)。

原创代码以 [Apache License 2.0](LICENSE) 开源。上游数据和品牌不随代码许可证开放。本项目提供
市场研究信息，不构成个性化投资建议。
