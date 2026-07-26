# 数据供应商接入指引

最后更新：2026-07-26

## Forward EPS

如果 MVP 不展示真正的 Forward PE，现在不需要购买任何东西，保持
`analyst_forward=null` 即可。

需要上线时，向 S&P Capital IQ Estimates、FactSet Estimates 或 LSEG I/B/E/S 等供应商
询价。下单前要求销售人员书面确认：

1. 可以在公开网站或订阅产品展示计算结果；
2. 可以保存历史快照并在合同终止后保留历史；
3. 可以生成并对终端用户展示 derived data；
4. 是否允许展示 NTM EPS、Forward PE、百分位和历史曲线；
5. 是否允许 API、CSV 下载或只允许不可逆的信号。

拿到许可后，需要提供：

- API 文档和测试账号；
- API key/secret；
- 合同或订单中对应的使用权条款引用；
- 供应商的 S&P 500 标识符和 NTM aggregate EPS 字段；
- 允许的展示范围：`internal` 或 `public`。

仅有一个从新闻文章抄来的 EPS 数字不够，因为无法稳定更新、回填或证明再分发权。

## TTM PE、ROE 和基本面

有两种产品口径，不能混称：

### 精确 S&P 500 指数口径

采购 S&P DJI index earnings/constituents 权利和 estimates/fundamentals 数据。优点是可以
称为 S&P 500 PE、EPS、ROE；缺点是价格和合同复杂。

### ArcOfMarket 自算代理

使用 SEC XBRL 基本面、经授权的证券价格和公开可用的当前成分，定义自己的聚合公式。
输出必须命名为“Arc 美国大盘股估值代理”，不能冒充 S&P 官方指数估值。该方案仍需取得
证券价格的商业使用与 derived-data 权利。

## SEC Form 4 与 13F

`SEC_IDENTITY` 不是账号、API key 或审批资格，而是请求头里的身份声明。格式为：

```text
ArcOfMarket research data@your-domain.com
```

邮箱必须真实、有人查看，不能使用 `.local` 或 `example.com`。在 GitHub 仓库中将完整
字符串保存为 Actions secret `SEC_IDENTITY`。SEC 当前要求总请求速率不超过每秒 10 次；
代码还应缓存、重试和只下载需要的文件。

## Congress 交易

`invest-data` 与本项目原来的适配器都指向 `api.capitoltrades.com`。相关单元测试使用的是
mock 数据，不是实时集成测试；2026-07-26 实测该域名无法解析，不能继续作为生产源。

可选路径：

1. 向 Quiver Quantitative 询价 Commercial API，并要求合同覆盖 commercial use、
   redistribution 和 derived indicators；
2. 直接解析 House/Senate 官方披露，但 House 页面明确限制商业用途，仅对面向公众传播的
   新闻与通讯媒体例外；付费指标是否适用必须由律师确认；
3. 暂时不提供 Congress 付费指标，只保留 SEC Form 4/13F。

选择商业供应商后，需要提供 API key、字段文档、商业订单和允许展示/下载的范围，再实现
适配器。不能用 Hobbyist、Trader 或个人版 key 支撑订阅产品。

## S&P 500 成分变更

`sp500_changes.json` 现在直接来自 Wikipedia 固定版本，按 CC BY-SA 4.0 标注，包含 1976
年以来 406 条“selected changes”。它足以做公开的调入调出表，但不保证构成完整
point-in-time universe。

严肃无幸存者偏差回测仍需要：

- 官方或授权供应商提供的每日/月末历史成分；
- 每次生效日期、证券标识符变更、并购和分拆处理；
- delisted securities 与当时可用价格；
- 数据在历史时点的可见日期。

## 数据授权询价模板

向任何供应商询价时，明确写出：

```text
We operate a public, ad-free market-history website and a paid subscription
product that displays ArcOfMarket-derived indicators. Please quote rights for:
(1) server-side commercial use, (2) public digital display, (3) historical
storage, (4) derived-data display, (5) subscriber access, and (6) optional
CSV/API redistribution. Raw source data will not be resold unless licensed.
```
