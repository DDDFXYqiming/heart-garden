"""
前端契约回归测试

覆盖容易被 Vite/Vue 构建漏掉的运行时变量问题。
"""
from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHAT_PAGE = PROJECT_ROOT / "frontend" / "src" / "views" / "ChatPage.vue"
API_INDEX = PROJECT_ROOT / "frontend" / "src" / "api" / "index.js"


def _script_setup(source: str) -> str:
    match = re.search(r"<script setup>(.*?)</script>", source, re.S)
    assert match, "ChatPage.vue 必须包含 <script setup>"
    return match.group(1)


def test_chat_page_imports_chat_stream_when_used():
    """ChatPage 调用 chatStream 时必须从 @/api 导入，防止运行时 ReferenceError。"""
    source = CHAT_PAGE.read_text(encoding="utf-8")
    script = _script_setup(source)

    assert "chatStream(" in script
    assert re.search(r"import\s*\{[^}]*\bchatStream\b[^}]*\}\s*from\s*['\"]@/api['\"]", script)


def test_api_chat_stream_checks_response_before_returning_body():
    """chatStream fetch 必须显式校验 HTTP 状态和 ReadableStream body。"""
    source = API_INDEX.read_text(encoding="utf-8")

    assert "export async function chatStream" in source
    assert "if (!response.ok)" in source
    assert "if (!response.body)" in source
    assert "return response" in source
