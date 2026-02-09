import yaml
import os
import re
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode

class URLCleaner:
    def __init__(self, config_path="rules.yaml"):
        self.rules = self._load_rules(config_path)
        self.url_regex = re.compile(r'https?://[^\s,]+')

    def _load_rules(self, path):
        if not os.path.exists(path):
            return {"global": {"default_strip": []}, "platforms": []}
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def extract_urls(self, text):
        """从文本中提取所有 URL"""
        if not text: return []
        return self.url_regex.findall(text)

    def normalize(self, url):
        """清洗单个 URL"""
        if not url: return ""
        
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        query_params = parse_qs(parsed.query)
        
        # 1. 查找匹配的任务规则
        platform_rule = None
        for rule in self.rules.get('platforms', []):
            if any(d in domain for d in rule.get('domains', [])):
                platform_rule = rule
                break
        
        # 2. 执行清洗策略
        new_params = {}
        
        if platform_rule:
            strategy = platform_rule.get('strategy')
            if strategy == 'strip_all':
                # 推特模式：清空所有参数
                new_params = {}
            elif strategy == 'whitelist':
                # 微信模式：仅保留白名单
                whitelist = platform_rule.get('keep', [])
                new_params = {k: v for k, v in query_params.items() if k in whitelist}
        else:
            # 通用模式：只删全局黑名单
            strip_list = self.rules.get('global', {}).get('default_strip', [])
            new_params = {k: v for k, v in query_params.items() if k not in strip_list}

        # 重新拼接 URL，去掉片段标识符 #
        new_query = urlencode(new_params, doseq=True)
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            "" # 移除碎片 #xxx
        ))

# 单例模式，方便全局调用
cleaner = URLCleaner()
