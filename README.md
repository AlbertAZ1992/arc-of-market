# ArcOfMarket

ArcOfMarket 是面向中文读者的美股市场档案与研究工作台。它把长期历史、宏观环境、
指数统计、行业板块和原创研究指标组织成可复核的静态图表，帮助读者回答三个问题：

- 当前市场处在什么位置；
- 类似历史区间曾出现过什么结果；
- 多个独立维度是否指向相同的市场状态。

项目不提供个性化投资建议，也不替用户作出交易决定。

## 当前能力

- 宏观：利率、通胀、增长、金融压力、信用环境、股票配置占比和经济周期；
- 指数：S&P 500、Nasdaq Composite、Nasdaq-100 的年度表现、回撤、牛熊周期、
  波动率、季节性、滚动收益和持有期统计；
- 市场结构：S&P 500 当前成分、行业分布和成分变更记录；
- 主题：七巨头、半导体、信息技术、金融、消费、奢侈品等研究页面；
- 数据治理：逐文件来源登记、默认拒绝的发布白名单、更新审计和哈希链；
- 自动化：GitHub Actions 日更、周更、测试、静态站构建和发布。

当前公开站点只同步 `config/public-data-policy.json` 明确允许的文件。订阅数据使用独立的
`config/subscriber-data-policy.json`，当前范围更窄；付费价值应来自 ArcOfMarket 的原创
评分、状态解释、变化提醒和研究内容，而不是转售原始数据文件。

## 架构

```text
GitHub Actions
      │
      ├─ daily：价格统计、波动率和高频宏观更新
      └─ weekly：月季宏观、成分变更、CFTC 和可选 SEC 更新
      │
      ▼
Python 采集与计算 → data/*.json → 质量审计 → 哈希链
      │
      ▼
公开数据门禁 → Astro 静态前端 → GitHub Pages / Cloudflare Pages
```

Python 只承担离线采集和计算。前端不直接请求上游服务，也不在浏览器中暴露 API 密钥。

## 本地运行

安装 Python 依赖：

```bash
uv sync --locked --group dev
cp .env.example .env
```

`.env` 中可配置：

- `FRED_API_KEY`：FRED 官方 API 密钥；
- `SEC_IDENTITY`：启用 SEC 采集时使用的应用名称和受监控联系邮箱；
- Forward PE 相关变量：仅在取得可展示的一致预期 EPS 后配置。

更新数据：

```bash
uv run python -m scripts.update --profile daily
uv run python -m scripts.update --profile weekly
uv run python -m scripts.update --profile full
```

启动前端：

```bash
cd astro
pnpm install --frozen-lockfile
pnpm dev
```

`pnpm dev` 与 `pnpm build` 会先执行数据同步，只把公开白名单内的 JSON 复制到
`astro/public/data/`。

## 验证

```bash
uv run ruff check scripts tests
uv run ty check scripts
uv run pytest -q

cd astro
pnpm check
pnpm lint
pnpm build
```

验证最新数据哈希链：

```bash
uv run python scripts/chain.py --verify
```

## 数据与发布

数据源、使用角色和必要声明登记在 `config/source-registry.json`；每个数据文件的来源、
可发布范围和审查状态登记在 `config/dataset-registry.json`。前端的数据来源页面只展示
读者需要的来源、日期和方法说明，不展示内部审计术语。

Forward PE、历史时点成分股和实时指数行情均不能由现有免费数据可靠补齐。没有合适权利
和数据质量保证时，项目选择不生成这些数据，而不是用近似值冒充。

详细说明：

- [架构](./docs/ARCHITECTURE.md)
- [运维手册](./docs/OPERATIONS.md)
- [数据覆盖](./docs/DATA_COVERAGE.md)
- [数据来源与发布矩阵](./docs/DATA_LICENSE_MATRIX.md)
- [Forward PE 数据契约](./docs/FORWARD_PE.md)
- [公开图表与原创指标政策](./docs/PUBLIC_DATA_AND_DERIVED_SIGNALS.md)

## 许可

ArcOfMarket 原创源代码采用 PolyForm Noncommercial 1.0.0。项目所有人保留商业运营、
另行授权和双重许可的权利。数据、商标和第三方材料不包含在该代码授权内，详情见
[LICENSE](./LICENSE) 和 [THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md)。
