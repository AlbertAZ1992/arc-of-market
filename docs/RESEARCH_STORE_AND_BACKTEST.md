# Point-in-Time Research Store 与回测路线

## 当前已经建立的契约

Research Store 是本地 SQLite 文件 `.research-store/research.db`，默认被 Git 忽略。它不需要
Cloud、对象存储、搜索服务或数据库账号。每次正式 Market Release 后追加一条观察：

- `asOf`：数据代表哪个市场日；
- `availableAt`：系统何时生成并实际拿到这条 Release；
- `releaseId`、`coreDigest`、方法版本和质量状态；
- 每个来源当时的状态和来源日期；
- 当时展示的信号、分数、置信度和分项贡献。

契约位于 `contracts/research-observation.schema.json`。修订采用 append-only；FRED/OFR 的最新修订
值按“当时收到的版本”保存，从现在开始形成可回放历史，不伪造过去的 vintage。

```bash
uv run python scripts/research_store.py init
uv run python scripts/research_store.py ingest-latest
uv run python scripts/research_store.py status
```

## 为什么现在不做完整历史回填

当前指数广度使用今日成分股，宏观数据是最新修订值。直接把这些输入回填十年会产生幸存者偏差
和前视偏差。公开 Release 可以有 252 日的基准衍生曲线用于画图，但正式策略验证只使用
`availableAt <= decisionTime` 的 Point-in-Time 观察。

## 分阶段验证

1. **Forward paper record**：每天 CI 发布后追加 Research Store，先积累 60/120/252 个交易日；
2. **规则冻结**：每个评分版本固定权重和阈值，改动必须升版本，禁止看完结果原地调参；
3. **Walk-forward**：滚动训练/校准区间与完全独立测试区间，报告各市场阶段；
4. **经济假设**：明确次日开盘或收盘执行、手续费、滑点、换手和不可成交日；
5. **基准**：与 SPY buy-and-hold、简单 MA200、固定风险预算比较；
6. **报告**：CAGR、波动率、最大回撤、Calmar、Sharpe、换手、最差年度和状态转换次数；
7. **防过拟合**：记录尝试次数，并使用
   [Deflated Sharpe Ratio](https://doi.org/10.2139/ssrn.2460551) 与
   [Probability of Backtest Overfitting](https://doi.org/10.2139/ssrn.2326253) 做补充诊断。

在完成上述验证前，产品应展示“观察分数 + 证据 + 置信度 + 风险条件”，而不是展示模拟收益曲线
或胜率营销。

