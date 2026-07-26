# 运维手册

## 必要环境

- Python 3.13（GitHub Actions）；
- `uv`；
- Node.js 22；
- pnpm 10.24.0。

本地初始化：

```bash
uv sync --locked --group dev
cp .env.example .env
cd astro
pnpm install --frozen-lockfile
```

## 凭证

### `FRED_API_KEY`

用于 FRED 官方 API。放在本地 `.env` 和 GitHub Actions Secret 中。不得写入代码、JSON、
日志或前端环境变量。

### `SEC_IDENTITY`

用于 SEC 公平访问请求头，不是 API 密钥。可以使用私人邮箱，但必须是长期有效且有人查看
的邮箱。推荐格式：

```text
ArcOfMarket research your-email@example.com
```

只有启用 Form 4 或 13F 更新时才需要。当前这两类文件默认不公开。

### Forward PE

只有取得带展示范围的一致预期未来十二个月 EPS 后才配置：

- `SP500_FORWARD_EPS_NTM`；
- `SP500_FORWARD_EPS_AS_OF`；
- `SP500_FORWARD_EPS_SOURCE`；
- `SP500_FORWARD_EPS_LICENSE_SCOPE`。

不要把密钥或供应商数据直接写入 GitHub Variables。

## 本地更新

日更：

```bash
uv run python -m scripts.update --profile daily
```

周更：

```bash
uv run python -m scripts.update --profile weekly
```

首次回填：

```bash
uv run python -m scripts.update --profile full
```

仅在诊断源故障时允许部分结果：

```bash
uv run python -m scripts.update --profile weekly --allow-partial
```

正式更新不要使用 `--allow-partial`。阻断源失败时程序恢复整个 `data/` 快照并返回非零。

## 更新后检查

```bash
uv run python scripts/chain.py --verify
uv run python -m scripts.license_gate --scope public
uv run ruff check scripts tests
uv run ty check scripts
uv run pytest -q

cd astro
pnpm check
pnpm lint
pnpm build
```

还应人工查看：

- `data/meta.json` 中本 profile 的失败列表；
- `data/audit_report.json` 中是否有 blocker；
- 核心数据的最新日期是否符合源频率；
- 图表是否出现突然断点、零值或单位变化；
- `git diff -- data/` 是否只包含预期更新。

## GitHub Actions

| Workflow | 计划 | 作用 |
| --- | --- | --- |
| `ci.yml` | PR 和非 main push | Python、前端检查与生产构建 |
| `daily.yml` | 美东交易日之后 | 运行 `daily` profile |
| `weekly.yml` | 每周六 | 运行 `weekly` profile |
| `update-data.yml` | 复用工作流 | 更新、验证、提交数据和部署 |

自动数据提交进入 `data/automated-updates`。远程仓库重建后必须重新创建该分支，或让第一次
更新工作流自动创建。

GitHub Secrets：

- `FRED_API_KEY`；
- `SEC_IDENTITY`。

可选的 Forward PE 凭证只在采购完成后配置。公开部署需要仓库变量
`PUBLIC_DATA_APPROVED=true`，并启用 GitHub Pages 权限。

## Cloudflare Pages

当前 Astro 项目位于 `astro/`，构建产物输出到仓库根目录 `dist/`。使用 Cloudflare Pages
时应固定 Node 22 与 pnpm 10.24.0，并把生产分支指向验证后的数据分支。仓库删除重建后，
需要重新授权 GitHub 仓库；旧部署不会自动获得新仓库权限。

## 常见故障

### Yahoo 返回限流或空数据

项目让 yfinance 自己管理 `curl_cffi` 会话、cookie 和 crumb，不注入普通
`requests.Session`。排查顺序：

1. 确认 yfinance 版本与锁文件一致；
2. 单独请求一个流动性高的 ETF；
3. 检查本机代理、共享 IP 和短时间重复全量回填；
4. 等待限流窗口结束后再运行；
5. 不要用高并发轮询规避上游限制。

能成功抓取不等于取得公开展示或商业再分发权，数据发布仍受独立白名单约束。

### FRED 失败

检查密钥是否存在、是否被空格包围，以及系列 ID 是否仍在
`config/fred-series-registry.json`。FRED 更新没有匿名回退。

### 数据日期落后

先确认源本身的发布频率和交易日。季度、月度和周度序列不应按日频新鲜度判断。数据审计
中的阈值按数据集分别配置。

### 自动提交冲突

数据工作流先合并触发它的代码提交，再更新专用数据分支。不要直接在人工作业中编辑
`data/automated-updates` 的生成文件；需要修改算法时在代码分支完成并通过 CI。

## 故障处理原则

- 连续三次失败后暂停重试，检查上游响应和实现假设；
- 不删除上一版有效数据来掩盖源故障；
- 不用替代指标冒充缺失指标；
- 不手工修改哈希链；
- 数据源条款或字段含义不清时，先停止相应数据集发布。
