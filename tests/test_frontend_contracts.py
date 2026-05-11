"""
前端契约回归测试

覆盖容易被 Vite/Vue 构建漏掉的运行时变量问题。
"""
from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHAT_PAGE = PROJECT_ROOT / "frontend" / "src" / "views" / "ChatPage.vue"
APP_PAGE = PROJECT_ROOT / "frontend" / "src" / "App.vue"
SETTINGS_PAGE = PROJECT_ROOT / "frontend" / "src" / "views" / "SettingsPage.vue"
STATS_PAGE = PROJECT_ROOT / "frontend" / "src" / "views" / "StatsPage.vue"
API_INDEX = PROJECT_ROOT / "frontend" / "src" / "api" / "index.js"
ROUTER_INDEX = PROJECT_ROOT / "frontend" / "src" / "router" / "index.js"
VIEWS_DIR = PROJECT_ROOT / "frontend" / "src" / "views"
DIARY_LIST = VIEWS_DIR / "DiaryList.vue"


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


def test_vue_pages_do_not_use_nested_success_after_api_interceptor_unwraps_response():
    """api/index.js 已返回 response.data，页面不能再写 res.data.success。"""
    api_source = API_INDEX.read_text(encoding="utf-8")
    assert "response => response.data" in api_source

    offenders = []
    for path in sorted(VIEWS_DIR.glob("*.vue")):
        source = path.read_text(encoding="utf-8")
        if "res.data.success" in source:
            offenders.append(path.relative_to(PROJECT_ROOT).as_posix())

    assert offenders == []


def test_router_guard_is_explicit_and_dev_bypass_is_intentional():
    """路由守卫必须是可执行代码，开发免登录只能是显式 DEV bypass，不应长期注释掉。"""
    source = ROUTER_INDEX.read_text(encoding="utf-8")

    assert re.search(r"(?m)^router\.beforeEach\(", source)
    assert "const publicPages" in source
    assert "import.meta.env.DEV" in source


def test_app_nav_marks_current_section_with_hand_drawn_active_state():
    """顶部导航必须能标记当前一级页面，并保留手绘贴纸式 active 样式。"""
    source = APP_PAGE.read_text(encoding="utf-8")
    script = _script_setup(source)

    assert "useRoute" in script
    assert "navItems" in script
    assert "function isNavActive" in script
    assert "aria-current" in source
    assert "nav-link-active" in source
    assert "bg-sticky" in source
    assert "border-[2px] border-pencil" in source
    assert "DiaryNew" in source
    assert "DiaryEdit" in source


def test_get_diaries_accepts_filters_parameter():
    """getDiaries 必须接受第三个 filters 参数用于搜索/筛选"""
    source = API_INDEX.read_text(encoding="utf-8")
    assert "export function getDiaries(page = 1, perPage = 10, filters = {})" in source
    assert "...filters" in source or "filters" in source


def test_diary_list_has_search_placeholder():
    """DiaryList.vue 必须包含搜索占位文字 '搜索日记'"""
    source = DIARY_LIST.read_text(encoding="utf-8")
    assert "搜索日记" in source


def test_diary_list_has_mood_select_text():
    """DiaryList.vue 必须包含情绪筛选文字 '全部情绪'"""
    source = DIARY_LIST.read_text(encoding="utf-8")
    assert "全部情绪" in source


def test_diary_list_calls_get_diaries_with_filters():
    """DiaryList.vue 调用 getDiaries 时必须传入 filters 对象"""
    source = DIARY_LIST.read_text(encoding="utf-8")
    script = _script_setup(source)
    assert "getDiaries(" in script
    assert "filters" in script


def test_stats_page_renders_personal_insight_contract():
    """统计页必须渲染后端提供的个人温柔回顾 insight。"""
    source = STATS_PAGE.read_text(encoding="utf-8")
    script = _script_setup(source)
    assert "温柔回顾" in source
    assert "stats.insight" in source
    assert "summary" in source
    assert "suggestion" in source
    assert "insight" in script


def test_settings_page_exposes_local_export_action():
    """设置页必须提供本地数据导出入口，且通过 API 包装函数调用 /api/export。"""
    api_source = API_INDEX.read_text(encoding="utf-8")
    settings_source = SETTINGS_PAGE.read_text(encoding="utf-8")
    settings_script = _script_setup(settings_source)

    assert "export function exportLocalData()" in api_source
    assert "api.get('/export')" in api_source
    assert "导出本地数据" in settings_source
    assert "exportLocalData" in settings_script
    assert "heart-garden-export" in settings_script
    assert "new Blob" in settings_script
