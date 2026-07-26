// ArcOfMarket · Anyway-style ECharts theme.

export const ARC_ECHARTS_THEME = {
  backgroundColor: "transparent",
  textStyle: {
    fontFamily: '"Noto Sans SC", "Open Sans", "PingFang SC", sans-serif',
    color: "#595959",
  },
  title: {
    textStyle: {
      fontFamily: '"Noto Serif SC", Merriweather, "Songti SC", serif',
      fontWeight: 700,
      color: "#272727",
    },
  },
  color: ["#f60c3e", "#272727", "#989898", "#4d6ea9", "#00a487", "#f08a24"],
  grid: { left: "8%", right: "6%", top: "12%", bottom: "12%" },
  xAxis: {
    axisLine: { lineStyle: { color: "#989898", width: 1 } },
    axisTick: { show: false },
    axisLabel: { color: "#989898", fontSize: 11 },
    splitLine: { show: false },
  },
  yAxis: {
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: "#989898", fontSize: 11 },
    splitLine: { lineStyle: { color: "#ddd", type: "dashed", width: 0.6 } },
  },
  tooltip: {
    backgroundColor: "#fff",
    borderColor: "#ddd",
    textStyle: { color: "#272727", fontSize: 12 },
    axisPointer: {
      type: "cross",
      lineStyle: { color: "#f60c3e", width: 0.6, type: "dashed" },
      crossStyle: { color: "#f60c3e", width: 0.6 },
    },
  },
  legend: { textStyle: { color: "#595959", fontSize: 12 } },
};

export const ARC_ECHARTS_THEME_DARK = ARC_ECHARTS_THEME;
