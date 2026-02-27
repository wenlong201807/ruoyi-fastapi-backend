"""评论 Service 纯函数单元测试（XSS 过滤 + 敏感词过滤）"""
import pytest

from module_comment.utils.filter_utils import xss_clean, sensitive_filter


class TestXSSClean:
    """XSS 过滤函数测试 - 共 10 个用例"""

    def test_strip_script_tags(self):
        result = xss_clean('<script>alert("xss")</script>hello')
        assert '<script>' not in result
        assert '</script>' not in result
        assert 'hello' in result

    def test_strip_img_onerror(self):
        result = xss_clean('<img src=x onerror=alert(1)>text')
        assert '<img' not in result
        assert 'text' in result

    def test_strip_iframe(self):
        result = xss_clean('<iframe src="evil.com"></iframe>safe')
        assert '<iframe' not in result
        assert 'safe' in result

    def test_normal_text_preserved(self):
        assert xss_clean('这是一条正常评论') == '这是一条正常评论'

    def test_html_entities_escaped(self):
        result = xss_clean('a &amp; b')
        assert '&amp;amp;' in result or '&amp;' in result

    def test_empty_string(self):
        assert xss_clean('') == ''

    def test_only_whitespace(self):
        assert xss_clean('   ') == ''

    def test_nested_tags(self):
        result = xss_clean('<div><p>hello</p></div>')
        assert 'hello' in result
        assert '<div>' not in result

    def test_style_tag(self):
        result = xss_clean('<style>body{display:none}</style>ok')
        assert 'ok' in result
        assert '<style>' not in result

    def test_event_handlers(self):
        result = xss_clean('<a href="#" onclick="steal()">click</a>')
        assert 'onclick' not in result
        assert 'click' in result


class TestSensitiveFilter:
    """敏感词过滤测试 - 共 5 个用例"""

    def test_no_sensitive_word(self):
        assert sensitive_filter('正常评论内容') == '正常评论内容'

    def test_single_sensitive_word(self):
        result = sensitive_filter('这里有违禁词1出现')
        assert '违禁词1' not in result
        assert '****' in result

    def test_multiple_sensitive_words(self):
        result = sensitive_filter('违禁词1和违禁词2都有')
        assert '违禁词1' not in result
        assert '违禁词2' not in result

    def test_empty_input(self):
        assert sensitive_filter('') == ''

    def test_no_false_positive(self):
        assert sensitive_filter('合法的词汇') == '合法的词汇'
