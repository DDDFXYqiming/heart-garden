"""
前端契约回归测试

覆盖容易被 Vite/Vue 构建漏掉的运行时变量问题。
"""
from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHAT_PAGE = PROJECT_ROOT / "frontend" / "src" / "views" / "ChatPage.vue"
SETTINGS_PAGE = PROJECT_ROOT / "frontend" / "src" / "views" / "SettingsPage.vue"
API_INDEX = PROJECT_ROOT / "frontend" / "src" / "api" / "index.js"


def _script_setup(source: str) -> str:
    match = re.search(r"<script setup>(.*?)</script>", source, re.S)
    assert match, "Vue 文件必须包含 <script setup>"
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


def test_settings_page_does_not_bind_masked_api_key_to_submit_payload():
    """设置页 API Key 输入必须与后端脱敏回显分离，避免把掩码当真实密钥提交。"""
    source = SETTINGS_PAGE.read_text(encoding="utf-8")
    script = _script_setup(source)

    assert 'v-model="apiKeyInput"' in source
    assert 'v-model="llmConfig.api_key"' not in source
    assert "apiKeyInput.value.trim()" in script
    assert "payload.api_key = key" in script
    assert "const { api_key, api_key_saved, api_key_preview, ...safeConfig }" in script


def test_settings_page_custom_mood_dictionary_temporarily_disabled():
    """设置页暂时不能展示或调用自定义情绪词库功能。"""
    source = SETTINGS_PAGE.read_text(encoding="utf-8")
    script = _script_setup(source)

    assert "自定义情绪词库暂时关闭" in source
    assert "getCustomWords" not in script
    assert "addCustomWord" not in script
    assert "deleteCustomWord" not in script
    assert "fetchWords" not in script
    assert "handleAdd" not in script
    assert "handleDelete" not in script
