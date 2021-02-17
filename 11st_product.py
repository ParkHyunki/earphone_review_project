import requests
import time
import random
import csv
from bs4 import BeautifulSoup
import os
import re
import json
from urllib.parse import urlencode

class crawler_elest_pinfo:

    def __init__(self, savepath=os.getcwd()):
        self.savepath = savepath

    def list_to_csv(self, savepath, save_list):
        ''' 리스트를 지정된 Path에 csv파일로 저장합니다.
        '''

        columns = ['code', 'title', 'price', 'rating', 'volumn', 'imgurl']
        with open(savepath, 'w', newline='', encoding='utf-8') as f:
            csv.register_dialect('dialect', delimiter='|',lineterminator='\n')
            writer = csv.writer(f, 'dialect')
            writer.writerow(columns)
            writer.writerows(save_list)

    def check_product_res(self, dispCtgrNo, page, sortCd):
        ''' 상품목록 페이지에 GET 방식으로 요청을 보내 받은 response 를 return 합니다.
        Args:
            dispCtgrNo : 카테고리 코드
            page : 페이지 번호
            sortCd : 정렬 방법
        '''

        url = 'http://www.11st.co.kr/category/DisplayCategory.tmall?'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36'}
        params = {
            'pageNo': page,
            'method': 'getDisplayCategory2Depth',
            'dispCtgrNo': dispCtgrNo,
            'sortCd': sortCd,
            'pageSize': 40}
        res = requests.get(url+urlencode(params), headers=headers)

        print(res.status_code)
        print(res.url)
        print(page,'페이지')

        return res

    def product_info(self, soup):
        tags = soup.find_all('div',attrs={'id':'product_listing'})[0].find_all('li',attrs={'id':re.compile('^thisClick_')})
        info = []
        for tag in tags:
            pjson = json.loads(tag.find_all('a',attrs={'data-log-actionid-label':'product'})[0].attrs['data-log-body'].replace("'","\""))
            
            code = pjson['content_no']
            title = pjson['content_name']
            price = pjson['product_price']
            if tag.find_all('span',attrs={'class':re.compile('^selr_star selr_star')}) != []:
                rating = float(tag.find_all('span',attrs={'class':re.compile('^selr_star selr_star')})[0].text.replace('판매자 평점 별5개 중 ','').replace('개',''))
            else:
                rating = None
            if tag.find_all('a',attrs={'class':'review'}) != []:
                volumn = int(tag.find_all('a',attrs={'class':'review'})[0].text.replace('\n','').replace('리뷰 ','').replace('건','').replace(',',''))
            else:
                volumn = None
            imgurl = tag.find_all('img')[0].attrs['src']
            pinfo = [code, title, price, rating, volumn, imgurl]
            info.append(pinfo)
        return info

    def run_product_crawling(self):
        dispCtgrNo = [1006408]
        elest = []
        error_code = []
        
        for category in dispCtgrNo:
            page = 1
            error_count = 0
            while True:
                res = self.check_product_res(category, page, 'G')
                time.sleep(random.uniform(0,2))
                if res.status_code != 200:
                    error_count += 1
                    if error_count == 5:
                        print("에러로 인해 다음 진행")
                        error_code.append(category)
                        time.sleep(random.uniform(20,30))
                        break
                    else:
                        time.sleep(random.uniform(20,30))
                        continue

                soup = BeautifulSoup(res.text,'html.parser')

                product_info = self.product_info(soup)
                elest.extend(product_info)
                self.list_to_csv(self.savepath, elest)
                total_count = int(soup.find_all('span',attrs={'id':'listTotalCount'})[0].text.replace(',',''))

                now_count = 40 * page
                if now_count < total_count:
                    page += 1
                    if page > 3:
                        break
                    else:
                        continue
                else:
                    print('다음 카테고리로 넘어갑니다.')
                    break
        print('오류가 난 코드 목록 :', error_code)

if __name__ == '__main__':

    start = time.time()
    elest = crawler_elest_pinfo('../product_11st.csv')
    elest.run_product_crawling()
    print("time :", time.time() - start)