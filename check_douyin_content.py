import asyncio
import aiohttp

async def f(): 
    headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36'}
    async with aiohttp.ClientSession(headers=headers, trust_env=True) as s:
        async with s.get('https://v.douyin.com/pxilvvfoQ8s/') as r:
            text = await r.text()
            print(text[:2000])

if __name__ == "__main__":
    asyncio.run(f())
