import os
from typing import Any, List, Tuple

from aqt import gui_hooks, mw
from aqt.webview import WebContent
from aqt.editor import Editor, EditorWebView
from aqt.qt import *
from aqt.utils import qtMenuShortcutWorkaround

from .i18n import tr

addon_dir = os.path.dirname(__file__)
config = mw.addonManager.getConfig(__name__)
mw.addonManager.setWebExports(__name__, r".*\.js")

def load_web(webcontent: WebContent, context: Any):
    if isinstance(context, Editor):
        addon_package = mw.addonManager.addonFromModule(__name__)
        base_path = f"/_addons/{addon_package}/"
        webcontent.js.append(f"{base_path}/bidi.js")


def wrap_block_in_dir(editor: Editor, direction: str) -> None:
    modify_text_align = "true" if config.get("auto_align_on_direction_change", False) else "false"
    editor.web.eval(f'BidiToolsSetBlockDir("{direction}", {modify_text_align});')

def wrap_inline_in_dir(editor: Editor, direction: str) -> None:
    editor.web.eval(f'BidiToolsSetInlineDir("{direction}");')

def ltr_block_action(editor: Editor):
    wrap_block_in_dir(editor, "ltr")

def rtl_block_action(editor: Editor):
    wrap_block_in_dir(editor, "rtl")

def ltr_inline_action(editor: EditorWebView):
    wrap_inline_in_dir(editor.editor, "ltr")

def rtl_inline_action(editor: EditorWebView):
    wrap_inline_in_dir(editor.editor, "rtl")


chars = (
    ("Left-to-Right Mark (LRM)", "\u200e"),
    ("Right-to-Left Mark (RLM)", "\u200f"),
    ("Left-to-Right Embedding (LRE)", "\u202a"),
    ("Right-to-Left Embedding (RLE)", "\u202b"),
    ("Left-to-Right Override (LRO)", "\u202d"),
    ("Right-to-Left Override (RLO)", "\u202e"),
    ("Pop Directional Format (PDF)", "\u202c"),
    ("Arabic Letter Mark (ALM)", "\u061c"),
    ("Left-to-Right Isolate (LRI)", "\u2066"),
    ("Right-to-Left Isolate (RLI)", "\u2067"),
    ("First Strong Isolate (FSI)", "\u2068"),
    ("Pop Directional Isolate (PDI)", "\u2069"),
)

def insert_char(editor: Editor, char: str):
    editor.web.eval(f"document.execCommand('inserttext', false, '{char}');")


def on_editor_will_show_context_menu(webview_editor: EditorWebView, m: QMenu) -> None:
    for text, handler, shortcut in actions[2:]:
        a = m.addAction(text, lambda cb=handler: cb(webview_editor))
        if shortcut:
            a.setShortcut(QKeySequence(shortcut))

    m.addMenu(create_insert_menu(webview_editor.editor))
    qtMenuShortcutWorkaround(m)

def create_insert_menu(editor: Editor) -> QMenu:
    m = QMenu(editor.mw)
    for name, char in chars:
        a = m.addAction(name)
        qconnect(a.triggered, lambda t, char=char: insert_char(editor, char))
    m.setTitle(tr('insert_chars'))

    return m


actions = (
    (tr('ltr_block_label'), ltr_block_action, config["ltr_block_shortcut"]),
    (tr('rtl_block_label'), rtl_block_action, config["rtl_block_shortcut"]),
    (tr('ltr_inline_label'), ltr_inline_action, config["ltr_inline_shortcut"]),
    (tr('rtl_inline_label'), rtl_inline_action, config["rtl_inline_shortcut"]),
)

editor_button_labels = ("ltr", "rtl")

def on_button_click(editor: Editor):
    m = QMenu(editor.mw)
    for text, handler, shortcut in actions[2:]:
        a = m.addAction(text)
        qconnect(a.triggered, lambda t, cb=handler: cb(editor))
        if shortcut:
            a.setShortcut(QKeySequence(shortcut))

    m.addMenu(create_insert_menu(editor))
    qtMenuShortcutWorkaround(m)
    m.exec(QCursor.pos())


def add_editor_button(buttons: List[str], editor: Editor) -> None:
    for i, (text, handler, shortcut) in enumerate(actions[0:2]):
        label = editor_button_labels[i]
        btn = editor.addButton(
            icon=os.path.join(addon_dir, f"icons/{label}.svg"),
            cmd=f"bidi_tools_{label}",
            tip=f"{text} ‎({shortcut})",
            func=handler,
            keys=shortcut,
        )
        buttons.insert(i, btn)

def add_shortcuts(shortcuts: List[Tuple], editor: Editor) -> None:
    for text, handler, shortcut in actions[2:]:
        if shortcut:
            shortcuts.append((shortcut, lambda cb=handler: cb(editor)))


gui_hooks.editor_did_init_buttons.append(add_editor_button)
gui_hooks.editor_did_init_shortcuts.append(add_shortcuts)
gui_hooks.webview_will_set_content.append(load_web)
gui_hooks.editor_will_show_context_menu.append(on_editor_will_show_context_menu)
