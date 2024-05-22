#!/usr/bin/env python
# coding: utf-8

# In[6]:


import requests
import json
import pandas as pd
import base64
from PIL import Image
from io import BytesIO
from IPython.display import display


# In[35]:


# 查看feed

# 通过API获取数据
# 查看某feedname下的所有feeds
# api = "https://recommend-server-prd.bttcdn.com/api/feednames/662247115f27ae9dbeaf3d39/feeds"

# 查看所有feeds，每100条分页
# api = "https://recommend-server-prd.bttcdn.com/api/feeds?offset=0&limit=100"

# 初始化 DataFrame
df = pd.DataFrame()
retrieved = 0

# 设置api参数
offset = 0
limit = 100
api = "https://recommend-server-test.bttcdn.com/api/feeds"

while True:
    # 发送 GET 请求,获取 Feed 数据
    params = {
        "offset": offset,
        "limit": limit
    }
    response = requests.get(api, params=params)

    # 检查请求是否成功
    if response.status_code == 200:
        # 获取 JSON 数据
        json_data = response.json()
        feed_num = json_data['total']
        
        # 将数据添加到 DataFrame
        new_df = pd.DataFrame(json_data['feeds'])
        df = pd.concat([df, new_df], ignore_index=True)
        
        retrieved = len(df)
        print(f"Progess: {retrieved}/{feed_num}")

        # 检查是否已取回所有数据
        if retrieved >= feed_num or offset > feed_num:
            break
        else:
            # 更新 offset,继续下一次请求
            offset += limit
    else:
        print(f"请求失败,错误代码: {response.status_code}")
        break

# 解析feed表
# df.head(10)

print(df.shape)

# 导出成Excel方便查看。为减小体积，去掉IconContent列
df_export = df.drop('IconContent', axis=1)
print(df_export.shape)

df_export.to_excel('output/feedlist_test_ent.xlsx', index=False)


# # # 查看feed icon
# # feed_icon = feeds[0]['IconContent'].split(',')[1]
# # image_data = base64.b64decode(feed_icon)   
# # image = Image.open(BytesIO(image_data))
# # display(image)



# In[ ]:


# 添加Feed


# In[41]:


# 查看所有Feed_names

# 通过API获取数据
url = "https://recommend-server-dev.bttcdn.com/api/feednames"

# 发送GET请求
response = requests.get(url)

# 检查请求是否成功
if response.status_code == 200:
    # 获取JSON数据
    json_data = response.json()
    print('Feednames fetched:', len(json_data))
else:
    print(f"请求失败，错误代码：{response.status_code}")

# 解析feedname表
df = pd.DataFrame.from_dict(json_data)
df.head(10)


# In[4]:


# 创建Feed_names

url = "https://recommend-server-test.bttcdn.com/api/feednames"

feedname_data = {
    "name": "test0327",
    "language": ["en"],
    "feed_provider": "https://recommend-provider-dev.bttcdn.com/api/provider/feeds?feed_name=test0327",
    "entry_provider": "https://recommend-provider-dev.bttcdn.com/api/provider/entries?feed_name=test0327&language=en",
    "description": "feedname test",
    "feed_id": ["65af71ff27ae275014b31cb0","65af720127ae275014b31ccc"]
}

response = requests.post(url, json = feedname_data)

# 检查请求是否成功
if response.status_code == 201:
    print('添加成功, feedname id = ',response.text)
else:
    print(f"请求失败，错误代码：{response.status_code}")


# In[60]:


# 删除Feed_names

api = "https://recommend-server-test.bttcdn.com/api/feednames/"
feedname_id = "6602718ba0684c6957ce26d0"
url = api+feedname_id
print(url)

response = requests.delete(url)
print(response)

if response.status_code == 204:
    print('删除成功')
else:
    print(f"请求失败，错误代码：{response.status_code}")


# In[40]:


# 批量添加feed

# 读取feed列表
excel_file = 'input/prd_ent.xlsx'  # feed文件
df = pd.read_excel(excel_file)

# 对应环境的category_id
category_id = '66175739a84f9620f108cf27'

# 在DataFrame中添加category_id列
df['category_id'] = category_id

# df.head(10)

# 组装成json
json_data = df[["category_id","feed_url"]].to_json(orient="records", force_ascii=False)
json_list = json.loads(json_data)

num_entries = len(json_list)
print(f"Number of entries to be added: {num_entries}")

json_data = json.dumps(json_list, indent=4)

# 设置接口
url = "https://recommend-server-test.bttcdn.com/api/batchCreateFeeds"
print(url)

headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, headers=headers, data=json_data)
if response.status_code == 200:
    print('添加成功, 以下feed已存在')
    print(json.dumps(json.loads(response.text), indent=4))
else:
    print(f"请求失败，错误代码：{response.status_code}")


# In[50]:


# 添加Feed到Feedname

# 读取feed列表
excel_file = 'input/test_ent.xlsx'  # feed文件
df = pd.read_excel(excel_file)

# 组装成json
feed_ids = df['ID'].tolist()
json_data = {
    "feed_id": feed_ids
}
json_data = json.dumps(json_data, indent=4) # Convert the dictionary to a JSON string
print(json_data)

# 设置API
feedNamesID = '664d6256a84f9620f108cf5d'
url= f"https://recommend-server-test.bttcdn.com/api/feednames/{feedNamesID}/setFeeds"
headers = {
    'Content-Type': 'application/json'
}

# 发送PUT请求,
response = requests.put(url, data=json_data, headers=headers)

# 检查响应
if response.status_code == 204:
    print("成功更新数据")
else:
    print("请求失败:", response.status_code, response.text)

