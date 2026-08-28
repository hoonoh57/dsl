import unittest

import app_ui
import app_ui_ux


class UXMaxUIContractTests(unittest.TestCase):
    def test_legacy_root_and_new_ux_route_coexist(self):
        paths = [getattr(route, "path", None) for route in app_ui_ux.app.routes]
        self.assertIn("/", paths)
        self.assertIn("/ux", paths)
        self.assertIs(app_ui.app, app_ui_ux.app)

    def test_legacy_root_is_not_replaced(self):
        legacy = app_ui.index()
        self.assertIn("Enterprise Quant DSL Studio", legacy)
        self.assertNotIn("무엇을 만들고 싶으세요?", legacy)

    def test_ux_flow_is_idea_to_dsl_to_execution(self):
        html = app_ui_ux.ux_index()
        for expected in (
            "무엇을 만들고 싶으세요?",
            "DSL 초안 만들기",
            "최종 실행 DSL",
            "백테스트 실행",
            "결정론적 안전 레일",
        ):
            self.assertIn(expected, html)

    def test_ux_reuses_existing_api_contracts(self):
        html = app_ui_ux.ux_index()
        for endpoint in (
            "/api/strategies",
            "/api/transpile",
            "/api/backtest",
        ):
            self.assertIn(endpoint, html)

    def test_ux_has_recovery_and_productivity_features(self):
        html = app_ui_ux.ux_index()
        self.assertIn("localStorage", html)
        self.assertIn("Ctrl", html)
        self.assertIn("전략 검색", html)
        self.assertIn("원본 코드 붙여넣기", html)

    def test_ux_keeps_prompt_as_drafting_not_execution_authority(self):
        html = app_ui_ux.ux_index()
        self.assertIn("자연어는 초안을 만들 뿐 실행 권한을 직접 갖지 않습니다.", html)
        self.assertIn("Core guard 유지", html)

    def test_legacy_link_is_exposed_from_new_ui(self):
        html = app_ui_ux.ux_index()
        self.assertIn('href="/"', html)
        self.assertIn("기존 UI", html)


if __name__ == "__main__":
    unittest.main()
