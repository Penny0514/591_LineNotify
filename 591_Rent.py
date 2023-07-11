#!/usr/bin/env python
# coding: utf-8

# In[1]:


import re
import emoji
import time
import random
import requests
from bs4 import BeautifulSoup

class House591Spider():
    def __init__(self):
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36 Edg/88.0.705.68',
        }

    def search(self, filter_params=None, sort_params=None, want_page=1):
        
        """ 搜尋房屋
        :param filter_params: 篩選參數
        :param sort_params: 排序參數
        :param want_page: 想要抓幾頁
        :return total_count: requests 房屋總數
        :return house_list: requests 搜尋結果房屋資料
        """
        
        total_count = 0
        house_list = []
        page = 0

        # 紀錄 Cookie 取得 X-CSRF-TOKEN
        s = requests.Session()
        url = 'https://rent.591.com.tw/'
        r = s.get(url, headers=self.headers)
        soup = BeautifulSoup(r.text, 'html.parser')
        token_item = soup.select_one('meta[name="csrf-token"]')

        headers = self.headers.copy()
        headers['X-CSRF-TOKEN'] = token_item.get('content')

        # 搜尋房屋
        url = 'https://rent.591.com.tw/home/search/rsList'
        params = 'is_format_data=1&is_new_list=1&type=1'
        if filter_params:
            # 加上篩選參數，要先轉換為 URL 參數字串格式
            params += ''.join([f'&{key}={value}' for key, value, in filter_params.items()])
        else:
            params += '&region=1&kind=0'
        # 在 cookie 設定地區縣市，避免某些條件無法取得資料
        s.cookies.set('urlJumpIp', filter_params.get('region', '1') if filter_params else '1', domain='.591.com.tw')

        # 排序參數
        if sort_params:
            params += ''.join([f'&{key}={value}' for key, value, in sort_params.items()])

        while page < want_page:
            params += f'&firstRow={page*30}'
            r = s.get(url, params=params, headers=headers)
            if r.status_code != requests.codes.ok:
                print('請求失敗', r.status_code)
                break
            page += 1

            data = r.json()
            total_count = data['records']
            house_list.extend(data['data']['data'])
            # 隨機 delay 一段時間
            time.sleep(random.uniform(2, 5))

        return total_count, house_list

    def get_house_detail(self, house_id):
        """ 房屋詳情

        :param house_id: 房屋ID
        :return house_detail: requests 房屋詳細資料
        """
        # 紀錄 Cookie 取得 X-CSRF-TOKEN, deviceid
        s = requests.Session()
        url = f'https://rent.591.com.tw/home/{house_id}'
        r = s.get(url, headers=self.headers)
        soup = BeautifulSoup(r.text, 'html.parser')
        token_item = soup.select_one('meta[name="csrf-token"]')

        headers = self.headers.copy()
        headers['X-CSRF-TOKEN'] = token_item.get('content')
        headers['deviceid'] = s.cookies.get_dict()['T591_TOKEN']
        # headers['token'] = s.cookies.get_dict()['PHPSESSID']
        headers['device'] = 'pc'

        url = f'https://bff.591.com.tw/v1/house/rent/detail?id={house_id}'
        r = s.get(url, headers=headers)
        if r.status_code != requests.codes.ok:
            print('請求失敗', r.status_code)
            return
        house_detail = r.json()['data']
        return house_detail


if __name__ == "__main__":
    house591_spider = House591Spider()

    # 篩選條件
    filter_params = {
        'region': '15',  # 地區
        'searchtype': '1', 
        'section' : '238',
#         'kind': '2',  # (類型) 獨立套房
        'rentprice': '8000,20000',  # (自訂租金範圍) 3000~6000元
        'multiRoom': '1,2,3',  # (格局) 2房 & 3房
        'other': 'cook',  # (特色) 可開伙 
        # --- 以下要加 showMore=1 ---
        'showMore': '1',
        'option' : 'bed',
        'area': '7,25',  # (自訂坪數範圍) 
    }
    # 排序依據
    sort_params = {
        # 租金由小到大
        'order': 'money',  # posttime, area
        'orderType': 'desc'  # asc
    }
    total_count, houses = house591_spider.search(filter_params, sort_params, want_page=1)
    print('搜尋結果房屋總數：', total_count)


#lineNotify設定
def lineNotifyMessage(msg, imgUrl):
    token = 'egUO1VmZrZOqbDwTY5QNpBqNgmOInreVkLC42tt087j'
    headers = {
      'Authorization': 'Bearer '+ token
    }

    message = {'message': msg}
    
    #透過 POST 傳送
    url = "https://notify-api.line.me/api/notify"
    response = requests.request("POST", url, headers=headers, data=message)


def print_rent(houses):
    for ul in houses:
        # 照片
        img_1 = ul.get("photo_list")[0]

        # 標題
        title = ul.get("title")

        # 詳細資訊的 URL
        detailUrl = 'https://rent.591.com.tw/home/' + str(ul.get("post_id"))

        # 價格
        price = ul.get("price")

        # 地理位置
        street = ul.get("location")

        # 更新時間點
        uptime = ul.get("refresh_time")

        if '小時' in uptime or '分鐘' in uptime:
            
            msg = emoji.emojize('\n💡  ') + title+ emoji.emojize('\n 📌  ')+street + emoji.emojize('\n 💰  ') + price + emoji.emojize('\n ⏰  ') + uptime + emoji.emojize('\n\n') + detailUrl
            lineNotifyMessage(msg, img_1)

print_rent(houses)