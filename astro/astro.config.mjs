import { defineConfig } from "astro/config";

// ArcOfMarket · Astro 静态站配置
// SPA(hash 路由) + 旗舰 panel 的 SEO 静态页双轨。
// data/*.json 作为静态资源直接服务(/data/*)。
export default defineConfig({
  outDir: "../dist",
  publicDir: "public",
  // data/ 软链或拷贝到 public/data，使前端可 fetch("/data/*.json")
  vite: {
    optimizeDeps: { include: ["echarts"] },
  },
  build: {
    // 旗舰 panel 出独立静态 HTML(shipped from src/pages/static/)
    inlineStylesheets: "auto",
  },
});
