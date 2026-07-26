# ArcOfMarket 架构

## 目标

ArcOfMarket 是一个以静态数据和静态页面为核心的市场研究产品。当前架构优先保证：

- 数据更新失败时不发布半成品；
- 每个公开文件都能追溯到来源和计算方法；
- 前端不持有密钥，也不直接依赖上游服务；
- 公开数据、订阅输入和内部研究使用不同的默认拒绝策略；
- 离线计算可以被单元测试和重复验证。

## 分层

```text
外部来源
  │
  ▼
采集适配器 scripts/harvest.py
  │
  ├─ 纯计算 scripts/index_statistics.py
  ├─ 宏观计算 scripts/macro_indicators.py
  └─ 运行结果 scripts/pipeline_runtime.py
  │
  ▼
data/*.json
  │
  ├─ scripts/audit.py：结构、覆盖、变更与来源登记
  ├─ scripts/chain.py：数据快照哈希链
  └─ scripts/license_gate.py：发布范围门禁
  │
  ▼
Astro 数据同步与静态构建
  │
  ▼
GitHub Pages 或 Cloudflare Pages
```

## 数据层

`data/` 是前后端之间唯一的运行时契约。生成文件包含：

- `_provenance`：生成时间、生成器、数据集组、来源 ID 和内部权利记录；
- `_license`：面向仓库维护者的数据归属提示；
- 数据集自身的日期、数值、单位、频率、来源序列和方法字段。

公开构建会移除内部审计字段，只保留读者需要的来源、日期、单位和方法说明。

来源登记分为四个文件：

| 文件 | 责任 |
| --- | --- |
| `config/source-registry.json` | 上游来源、用途、条款链接和必要声明 |
| `config/dataset-registry.json` | 每个 JSON 的来源组合与可用范围 |
| `config/public-data-policy.json` | 免费公开构建白名单 |
| `config/subscriber-data-policy.json` | 订阅产品输入白名单 |

任何未登记文件默认不能发布。

## 更新事务

`scripts.update` 在采集前保存当前 `data/` 快照。正式模式执行顺序如下：

1. 运行所选更新 profile；
2. 记录每个步骤的成功、失败和来源状态；
3. 对 JSON 结构、时间轴、覆盖范围和来源登记执行审计；
4. 追加整套数据的哈希链记录；
5. 验证哈希链；
6. 只有全部阻断条件通过，才保留新数据。

任一阻断步骤失败时，`data/` 会恢复到更新前状态。可选 SEC 数据失败只会留下状态记录。

## 更新频率

- `daily`：指数统计、波动率、相对强弱、市场状态、利率与金融压力；
- `weekly`：月季宏观、股票配置占比、CFTC、经济周期、成分和成分变更；
- `full`：首次部署或重建数据时同时运行两组任务。

GitHub Actions 把验证后的数据提交到 `data/automated-updates`。静态发布只在数据许可门禁
和构建检查通过后进行。

## 前端

Astro 页面按阅读顺序分为：

1. 首页；
2. 宏观；
3. S&P 500；
4. Nasdaq；
5. Dow Jones；
6. 七巨头；
7. 行业与主题；
8. 实验室；
9. 方法论、全部图表和关于页面。

ECharts 用于项目自己的历史统计图。品牌行情组件只在需要第三方承载数据展示时使用。
页面索引来自 `astro/src/lib/chart-catalog.ts`，图表组件与目录锚点必须一一对应。

## 安全边界

- `.env` 和 GitHub Secrets 保存 API 密钥及 SEC identity；
- JSON、日志、前端代码和构建产物不得包含密钥；
- `SEC_IDENTITY` 不是密钥，但应使用真实、受监控的联系邮箱；
- 前端部署不需要 FRED 或 SEC 凭证；
- 自动化仅获得提交数据和部署页面所需的最小权限。

## 后续架构

当前静态架构足以支持免费公开图表。需要账户、订阅、通知和个性化研究时，再引入
Next.js、Cloudflare Workers、D1、R2 和 Better Auth。Python 采集仍保持为 GitHub
Actions 离线任务，避免把数据供应商凭证带入在线请求链路。
