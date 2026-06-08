import unittest
from unittest.mock import patch

import app


class ChartLayoutTests(unittest.TestCase):
    def _capture_chart(self, render_func, *args, **kwargs):
        captured = {}

        def fake_plotly_chart(fig, *plot_args, **plot_kwargs):
            captured["fig"] = fig

        with patch.object(app.st, "plotly_chart", fake_plotly_chart):
            render_func(*args, **kwargs)

        return captured["fig"]

    def test_horizontal_bar_keeps_outside_value_labels_visible(self):
        fig = self._capture_chart(
            app._plotly_bar,
            {
                "较低风险": 18,
                "最高风险": 100,
            },
            "测试柱状图",
            orientation="h",
        )

        self.assertFalse(fig.data[0].cliponaxis)
        self.assertGreater(fig.layout.margin.r, 70)
        self.assertGreater(fig.layout.xaxis.range[1], 100)

    def test_vertical_bar_keeps_top_value_labels_visible(self):
        fig = self._capture_chart(
            app._plotly_bar,
            {
                "每天都用": 61,
                "偶尔使用": 12,
            },
            "测试频率图",
            orientation="v",
        )

        self.assertFalse(fig.data[0].cliponaxis)
        self.assertGreater(fig.layout.margin.t, 56)
        self.assertGreater(fig.layout.yaxis.range[1], 61)

    def test_radar_wraps_dimension_labels_and_expands_canvas(self):
        fig = self._capture_chart(
            app._plotly_radar,
            {
                "academic_integrity": 82,
                "data_privacy": 48,
                "reliability": 76,
                "fairness": 25,
                "transparency": 88,
                "learning_agency": 64,
                "accountability": 70,
                "copyright": 58,
            },
            app.DIMENSION_LABELS,
        )

        self.assertTrue(any("<br>" in label for label in fig.data[0].theta))
        self.assertGreaterEqual(fig.layout.margin.l, 70)
        self.assertGreaterEqual(fig.layout.margin.r, 70)
        self.assertGreaterEqual(fig.layout.height, 500)

    def test_coded_bar_uses_option_codes_on_axis(self):
        fig = self._capture_chart(
            app._plotly_coded_bar,
            {
                "查资料 / 解释概念": 75,
                "总结要点 / 列提纲": 64,
                "润色改写表达": 50,
            },
            "AI 用途选择频率",
            option_order=[
                "查资料 / 解释概念",
                "总结要点 / 列提纲",
                "润色改写表达",
            ],
        )

        self.assertEqual(list(fig.data[0].y), ["C", "B", "A"])
        self.assertNotIn("查资料 / 解释概念", list(fig.data[0].y))

    def test_stacked_bar_uses_option_codes_on_axis(self):
        fig = self._capture_chart(
            app._plotly_stacked_bar,
            {
                "查资料 / 解释概念": {"允许": 71, "允许但需要说明": 8, "不允许": 0},
                "总结要点 / 列提纲": {"允许": 72, "允许但需要说明": 7, "不允许": 0},
            },
            "作业场景接受度",
            option_order=["查资料 / 解释概念", "总结要点 / 列提纲"],
        )

        self.assertEqual(list(fig.data[0].y), ["A", "B"])
        self.assertEqual(list(fig.data[0].customdata), ["查资料 / 解释概念", "总结要点 / 列提纲"])


if __name__ == "__main__":
    unittest.main()
