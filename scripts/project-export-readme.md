# ArcOfMarket 数据项目恢复包

该目录包含当前数据采集、计算、评分、合同、测试和正式 Market Release，不包含密钥、虚拟环境、
缓存、本地研究库、`outputs/` 或二进制文件。

## 恢复

```bash
shasum -a 256 -c SHA256SUMS
bash restore_project.sh PROJECT_SOURCES.md /absolute/path/to/empty-target
cd /absolute/path/to/empty-target
uv sync --locked --group dev
uv run ruff format --check scripts tests src
uv run ruff check scripts tests src
uv run ty check scripts src
uv run pytest -q
```

目标目录必须为空。生产环境的 `.env` 和第三方凭证需要重新配置。

项目的运行、验证和数据边界以恢复后的 `README.md` 与 `docs/` 为准。若同时恢复 Cloud 项目，
两个目录必须保持同级，名称分别为 `arc-of-market` 和 `arc-of-market-cloud`。
