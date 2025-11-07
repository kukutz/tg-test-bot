from app.services.markdown import markdown_to_html, render_for_telegram


def test_markdown_sanitized():
    html = markdown_to_html("**bold** <script>alert(1)</script>")
    assert "script" not in html
    assert "<strong>bold</strong>" in html


def test_render_for_telegram():
    assert render_for_telegram('<b>test</b>') == '&lt;b&gt;test&lt;/b&gt;'

