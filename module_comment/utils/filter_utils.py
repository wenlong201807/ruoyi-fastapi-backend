"""纯函数工具 - 不依赖项目配置，可独立测试"""
import html
import re

SENSITIVE_WORDS = ['违禁词1', '违禁词2']


def xss_clean(text: str) -> str:
    cleaned = re.sub(r'<[^>]+>', '', text)
    cleaned = html.escape(cleaned)
    return cleaned.strip()


def sensitive_filter(text: str) -> str:
    result = text
    for word in SENSITIVE_WORDS:
        result = result.replace(word, '*' * len(word))
    return result
