#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import time
import requests
import json
from urllib.parse import urlparse

# subreddits = ['worldnews','sports','news','UpliftingNews','technology','gaming','space','science']
# subreddits = ['movies', 'gaming', 'Music', 'television', 'anime', 'entertainment', 'BritishTV', 'tvPlus', 'TvShows']
subreddits = ['BritishTV', 'tvPlus', 'TvShows']
# subreddits = ['finance']


# 设置API参数
# Reddit API
# https://www.reddit.com/r/{subreddit}/{listing}.json?limit={count}&t={timeframe}
# The values that you can choose from are:
#     timeframe = hour, day, week, month, year, all
#     listing = controversial, best, hot, new, random, rising, top
# For example, to get the top 100 posts in the past year for the r/python subreddit, you would query that URL:
# https://www.reddit.com/r/python/top.json?limit=100&t=year

limit = 100
timeframe = 'month'

# 配置Cookie, 此处内容需要登陆后从浏览器Cookie中拷贝对应内容
cookies = {
'csrf_token': 'aaa',
'csv': '2',
'edgebucket': 'aaa',
'g_state': '{"i_l":0}',
'loid': 'aaa.2.1715920994509.Z0FBQUFBQm1SdUJpb3lpaEY0M0xjYTVpUG5uYmlZMUkwVG1fT2JfRXhwcENkTEltUTI3bTlTTzdpYTNsanppTmJrRjFlSm9QMjd5VXNWaDRESXhDaHdqZHBWWWxDcWNHVjUxVlRjaEZ3TmRDeEkzNXQ2U3RGb1pDWllpclR1bmFKRXJMNjU2OHJJak4',
'pc': 'sd',
'rdt': 'aa',
'reddit_session': 'aa%2C2024-05-17T04%3A44%3A07%2Cae11ee09e6f416fa8899dc44e98a58f98d8179ea',
'session_tracker': 'aa.0.1716285009221.Z0FBQUFBQm1URzVSUkhmS2pDbjdPckhMTldIMUVhN0JCTW9zbmZVbFFGN3RSS0FWekpHdGpMbTBKb0wwNWtxRFRlUzFSYjJnV0Q0MDhOTk9rdFVnYzNtQnNWTHl2dUZhZENtRW1EX21LenRENEE4Y2dxTGI3MEEtUTZJbjNpVkxfTFlVSXVzT3NMR0s',
't2_10j1sj3o69_recentclicks3': 'aa,t3_1cweery,t3_1cwb81p,t3_1cwle1a,t3_1cwmyi4,t3_1cwgsxc,t3_avsaq2,t3_j59evd,t3_8113jx,t3_6796wu',
'token_v2': 'aa.eyJzdWIiOiJ1c2VyIiwiZXhwIjoxNzE2MzcxNDAwLjY1NTU0OSwiaWF0IjoxNzE2Mjg1MDAwLjY1NTU0OCwianRpIjoiUzNDWnp4RjQ3Xy1pbGg5RDkyeW15SnFZVEtuTFpRIiwiY2lkIjoiOXRMb0Ywc29wNVJKZ0EiLCJsaWQiOiJ0Ml8xMGoxc2ozbzY5IiwiYWlkIjoidDJfMTBqMXNqM282OSIsImxjYSI6MTcxNTkyMDk5NDUwOSwic2NwIjoiZUp4a2tkR090REFJaGQtbDF6N0JfeXBfTmh0c2NZYXNMUWFvazNuN0RWb2NrNzA3Y0w0aUhQOG5LSXFGTEUydUJLR2tLV0VGV3RPVU5pTHY1OHk5T1pFRlN5RlRSODQzeXdva2FVcFBVbU41cHlsUndXWmtMbGZhc1VLREI2WXBWUzZaMjBLUFM1dlEzSTFGejA2TXFseFdIdFRZbzNKcGJHTUsyeFBqemNacVF5cXV5NmxNWUZrb244V0xmdnlHLXRZLWY3YmZoSFl3cktnS0RfVE91Rnh3WV9IREZIYl9ucHIwYkYyd3FMM1hnOVEtMS1OMjdiTm1vZG01X1Z6UHZ6YVNjVG1HNWlmWXY3dC1DUjE0NUhtWlVRY3dZZzBfeXJBajZfQ3ZPb0RLQlFXTUpZaFBJNUFybDJfX0pkaXVUZjhhdHlkLS1HYkVUV180clJtbzV4TEVvVV9qNnpjQUFQX19YRF9lNHciLCJyY2lkIjoiUWYzYzVuNWZycmVZNWZlbVlKMHQ4UVlCSEx0UnBrUV9fN0RJaWdGRlFwcyIsImZsbyI6Mn0.Gm3YEsoUpRNfsYcFfX5HcOeFjn1lFNuSiv18UocQGjeJtuqsUzH2sYIoVObRNYCIv3VAgJzffAPYXjZTHQYVGIiFms4hh8O4IBw0vhDHvhJ4zmTlpjnPoDhxO4pPIMRv5n6Q375ealZ0oytjOTFo4W2dt_izJOok-KR669aJdjj8b9IBnn8OYmjoHPNYQC6IYo7BHh_uYZMF34g-ZTHPebRQcVlEef6c7NzB4rqzwwlVgZU_8r9pocUj7W9A3fbJ0IU3a0Z0nvL20r_XZUqSqx0Q5NkyRsKPrS8hp_MBzhjgz0ECPPHSUJnWKkZMzvk7M3KzE17XC4oszdVUFPlhlg'
}
    

for subreddit in subreddits:
    url = 'https://www.reddit.com/r/'+subreddit+'/top.json?limit='+str(limit)+'&t='+timeframe
    # url = 'https://www.reddit.com/r/'+subreddit+'/hot.json?limit='+str(limit)
    print(url)
    
    # 获取 TOP Post
    response = requests.get(url,headers = {'User-agent': 'mybot 0.1'}, cookies = cookies)
    
    # response = requests.get(url)
    top_data = json.loads(response.text)
    top_posts = top_data['data']['children']

    # 写入表头
    csv_dir = 'output/' + subreddit + '.csv'
    f = open(csv_dir, mode='w', newline='')
    f.write('n,domain,url\n')

    # 把Post中的链接记录下来
    n = 0
    for post in top_posts:
        n += 1
        resrow = str(n) + ','
        resrow += urlparse(post['data']['url']).netloc + ','
        resrow += post['data']['url']+ '\n'
        print(resrow)
        f.write(resrow)
        f.flush()
    f.close
    time.sleep(2)  # Sleep for 2 seconds
    

