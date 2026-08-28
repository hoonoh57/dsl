import unittest

import app_ui
import app_ui_ux


VALID_DSL = '''strategy "UX_Test" {
    timeframe = "1d"
    fast = ta.sma(close, 5)
    slow = ta.sma(close, 20)
    entry_cond = ta.crossover(fast, slow)
    exit_cond = ta.crossunder(fast, slow)
    on(entry_cond) {
        order.buy(type = "MARKET")
    }
    on(exit_cond) {
        order.close_position()
    }
}'''


class UXMaxUIContractTests(unittest.TestCase):
    def test_legacy_root_and_new_ux_route_coexist(self):
        paths = [getattr(route, "path", None) for route in app_ui_ux.app.routes]
        self.assertIn("/", paths)
        self.assertIn("/ux", paths)
        self.assertIn("/api/ux/validate", paths)
        self.assertIs(app_ui.app, app_ui_ux.app)

    def test_legacy_root_is_not_replaced(self):
        legacy = app_ui.index()
        self.assertIn("Enterprise Quant DSL Studio", legacy)
        self.assertNotIn("Human-mediated LLM", legacy)

    def test_natural_language_flow_is_explicitly_human_mediated(self):
        html = app_ui_ux.ux_index()
        for expected in (
            "1. 자연어 입력",
            "2. LLM 요청 생성",
            "3. 인간 매개",
            "4. 로컬 DSL 검증",
            "5. 백테스트",
            "외부 LLM에 보낼 요청 프롬프트",
            "LLM 결과 붙여넣기",
        ):
            self.assertIn(expected, html)

    def test_prompt_mode_does_not_call_legacy_prompt_transpiler(self):
        html = app_ui_ux.ux_index()
        self.assertNotIn("source_type:sourceMode", html)
        self.assertNotIn("PROMPT → DSL 변환 요청", html)
        self.assertIn("buildPrompt()", html)
        self.assertIn("admitLLMResult()", html)

    def test_llm_result_requires_local_parser_semantic_validation(self):
        html = app_ui_ux.ux_index()
        self.assertIn("/api/ux/validate", html)
        self.assertIn("Parser/Semantic 검증", html)
        self.assertIn("runBtn", html)
        self.assertIn("disabled", html)
        result = app_ui_ux.ux_validate(app_ui_ux.UXValidateRequest(dsl_code=VALID_DSL))
        self.assertTrue(result["ok"])
        self.assertEqual(result["parser"], "PASS")
        self.assertEqual(result["semantic"], "PASS")

    def test_invalid_llm_output_fails_closed(self):
        result = app_ui_ux.ux_validate(app_ui_ux.UXValidateRequest(dsl_code="buy now"))
        self.assertFalse(result["ok"])
        self.assertEqual(result["parser"], "FAIL")
        self.assertEqual(result["semantic"], "NOT_RUN")

    def test_existing_strategy_and_backtest_apis_are_reused(self):
        html = app_ui_ux.ux_index()
        self.assertIn("/api/strategies", html)
        self.assertIn("/api/backtest", html)
        self.assertIn('href="/"', html)
        self.assertIn("기존 UI", html)

    def test_llm_has_no_execution_authority_claim(self):
        html = app_ui_ux.ux_index()
        self.assertIn("LLM 출력은 실행 권한이 아닙니다", html)
        self.assertIn("Parser/Semantic 검증을 통과", html)
        self.assertIn("외부 LLM 호출은 이 앱이 자동으로 수행하지 않습니다", html)


if __name__ == "__main__":
    unittest.main()
