import csv
import os
import re
import requests
from collections import defaultdict

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

def extract_url(text):
    match = re.search(r'https?://[^\s,]+', text)
    return match.group(0) if match else None

def get_url_category(url):
    parsed = re.search(r'https?://([^/]+)(/[^?#]*)', url)
    if not parsed: return "unknown"
    domain, path = parsed.groups()
    if 'weixin.qq.com' in domain:
        return "wechat_short" if '/s/' in path else "wechat_long"
    if 'x.com' in domain or 'twitter.com' in domain:
        return "x_status" if '/status/' in path else "x_video"
    return domain

def verify_link_verbose(url, clean_url):
    try:
        # 使用 Session 保持一定的持久性
        session = requests.Session()
        r1 = session.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        r2 = session.get(clean_url, headers=HEADERS, timeout=10, allow_redirects=True)
        
        len_orig, len_clean = len(r1.content), len(r2.content)
        len_ratio = abs(len_orig - len_clean) / (len_orig + 1)
        
        is_safe = (r1.status_code == r2.status_code) and (len_ratio < 0.1)
        
        print(f"    - [原始] 状态: {r1.status_code}, 长度: {len_orig}, 最终地址: {r1.url[:50]}...")
        print(f"    - [清洗] 状态: {r2.status_code}, 长度: {len_clean}, 最终地址: {r2.url[:50]}...")
        
        # 深度怀疑：如果两个都被重定向到了 login，长度没准也一样，这里要小心
        if "login" in r1.url.lower() and "login" in r2.url.lower():
            print("    ⚠️ 警告：两个链接都被重定向到了登录页，实验数据可能不可信（被反爬虫拦截）。")
        
        return is_safe
    except Exception as e:
        print(f"    ❌ 实验异常: {e}")
        return False

def run_deep_verify(csv_path):
    if not os.path.exists(csv_path): return
    categories = defaultdict(list)
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            url = extract_url(row.get('content', ''))
            if not url: continue
            cat = get_url_category(url)
            if len(categories[cat]) < 2: categories[cat].append(url)

    print(f"\n===== 深度验证: {csv_path} =====")
    for cat, urls in categories.items():
        print(f"\n[类别: {cat}]")
        for url in urls:
            cleaned = url.split('?')[0]
            if url == cleaned: continue
            print(f"  🔍 测试链接: {url[:70]}...")
            safe = verify_link_verbose(url, cleaned)
            print(f"  💡 结论: {'✅ 安全' if safe else '❌ 风险'}")

if __name__ == '__main__':
    run_deep_verify('data/x/x_url.csv')
    run_deep_verify('data/wechat/wechat_url.csv')
