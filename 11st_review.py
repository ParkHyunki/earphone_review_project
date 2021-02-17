import requests
from bs4 import BeautifulSoup
import re
import time
import csv
import random
from multiprocessing import Pool, Manager
import os
from urllib.parse import urlencode

class elevenst_review_crawler:

    def __init__(self, filepath=os.getcwd(), savepath=os.getcwd()):
        self.filepath = filepath
        self.savepath = savepath

    def list_to_csv(self, filepath, save_list):

        columns = ['item_id', 'review_id', 'login_id', 'score', 'content', 'item_option', 'date', 'likeCnt']
        with open(filepath, 'w',newline='', encoding='utf-8') as f:
            csv.register_dialect('dialect', delimiter='|',lineterminator='\n')
            writer = csv.writer(f, 'dialect')
            writer.writerow(columns)
            writer.writerows(save_list)

    def csv_to_list(self,filepath):

        item_list = []
        with open(filepath, 'r',encoding='utf-8') as f:
            csv.register_dialect('dialect', delimiter='|',lineterminator='\n')
            reader = csv.reader(f,'dialect')
            for line in reader:
                item_list.append(line[0])
        return item_list[1:]

    def check_res(self, prdNo, pageNo, pageSize, sortType):


        url = 'http://m.11st.co.kr/MW/api/app/elevenst/product/getProductReviewListArea.tmall?'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36'}
        params = {'prdNo': prdNo,'pageSize':pageSize}
        data = {'pageNo' : pageNo, 'sortType': sortType}
        res = requests.post(url + urlencode(params), headers=headers, data=data)
        print(res.status_code)
        print(res.url)
        print(pageNo,' 페이지')
        return res

    def get_review_info(self, res):

        review = res.json()['review']['list']
        review_info = []

        for i in range(10):

            try:
                item_id = review[i]['prdNo']
                review_id = review[i]['contMapNo']
                login_id = review[i]['memId'].replace('|','').replace('\"','')
                score = float(review[i]['evlPnt'])
                try:
                    content = re.sub('[\t\n\r"]','',review[i]['subject'])
                except KeyError:
                    content = None
                item_option = review[i]['optionNm']
                date = review[i]['createDt'].replace('.','-')
                likeCnt = int(review[i]['likeCnt'])

            except IndexError:

                print('해당 페이지 리뷰개수 : ',i)
                break

            pinfo = [item_id, review_id, login_id, score, content, item_option, date, likeCnt]
            review_info.append(pinfo)

        return review_info    


    def run_crawling(self):

        elevenst = []
        error_code = []
        prd_list = self.csv_to_list(self.filepath)
        print("크롤링할 상품 개수 : ", len(prd_list))
        for i,prdNo in enumerate(prd_list):
            print('--------------', i+1,'/', len(prd_list),'--------------')
            page = 1
            error_count = 0
            while True:
                res = self.check_res(prdNo, page, 10, '02')
                time.sleep(random.uniform(0,1))
                if res.status_code != 200:
                    error_count += 1
                    if error_count == 5:
                        print('에러로 인해 다음 진행')
                        error_code.append(prdNo)
                        time.sleep(random.uniform(20,30))
                        break
                    else:
                        time.sleep(random.uniform(20,30))
                        continue
                if res.json()['status']['code'] == 795:
                    print('판매자 요청에 의해 상품리뷰 노출이 제한된 상품입니다')
                    break

                if len(res.json()['review']['list']) == 0:
                    print('등록된 상품후기가 없습니다.')
                    break
                
                review_info = self.get_review_info(res)
                elevenst.extend(review_info)

                self.list_to_csv(self.savepath, elevenst)

                if res.json()['review']['nextYn'] != 'N':
                    page += 1

                    # if int(res.json()['review']['list'][0]['createDt'][:4]) >= 2020:
                    #     continue
                    # else:
                    #     break
                    # if page == 200:
                    #     break
                    # else:
                    #     continue
                else: 
                    break
        print('오류가 난 코드 목록 : ', error_code)

if __name__ == '__main__':
    start = time.time()
    elevenst = elevenst_review_crawler('../product_11st.csv','../review_11st.csv')
    elevenst.run_crawling()
    print("time :", time.time() - start)