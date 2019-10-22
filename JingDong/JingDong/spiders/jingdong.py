# -*- coding: utf-8 -*-
import scrapy
from bs4 import BeautifulSoup
from scrapy import Request
from JingDong.items import GoodsItem
from urllib.parse import quote
import re
import json
import copy
import time

class JingdongSpider(scrapy.Spider):
    name = 'jingdong'
    allowed_domains = ['jd.com']
    start_urls = ['https://search.jd.com/Search?keyword=化妆品&enc=utf-8&pvid=4d651b81d9d64e9aad90c4ec5ce87f08']
    start_url = 'https://search.jd.com/Search?keyword=化妆品&enc=utf-8&pvid=4d651b81d9d64e9aad90c4ec5ce87f08'
    index_url = 'https://search.jd.com/search?keyword=%E5%8C%96%E5%A6%86%E5%93%81&enc=utf-8&qrst=1&rt=1&stop=1&vt=2&ev=exbrand_{GoodsBrand}%5E&stock=1&page={page}&click=0'
    next_url = 'https://search.jd.com/s_new.php?keyword=%E5%8C%96%E5%A6%86%E5%93%81&enc=utf-8&qrst=1&rt=1&stop=1&vt=2&ev=exbrand_{GoodsBrand}%5E&stock=1&page={page}&scrolling=y&show_items={ids}'
    comment_url = 'https://club.jd.com/comment/productCommentSummaries.action?referenceIds={GoodsId}'
    page = 1
    count_page = 200  # 最大爬取页面

    def start_requests(self):  # 化妆品起始页面获取
        yield Request(self.start_url, callback=self.parse_start_page)

    def parse_start_page(self, response):
        """
        获得起始页的内容之后，取得化妆品各品牌的链接
        :param response:
        :return:
        """
        content = response.text
        item = GoodsItem()
        soup = BeautifulSoup(content, "lxml")
        li_s = soup.find('div', class_='sl-v-logos').find_all('li')
        for li in li_s:
            title = li.find("a").get('title')  # 品牌名
            item['GoodsBrand'] = title
            title = quote(title)
            yield Request(self.index_url.format(GoodsBrand=title, page=self.page), callback=self.parse_index_page, \
                          meta={"item": copy.deepcopy(item)})

    def parse_index_page(self, response):
        """
        获得各品牌页面的内容，并获取商品的详情页面链接并访问
        获得各品牌的页面，每次只加载前面30条信息，后面的30条信息在你下拉浏览的时候才会加载
        :param response:
        :return:
        """
        time.sleep(1)
        item = response.meta['item']
        content = response.text
        soup = BeautifulSoup(content, "lxml")
        li_s = soup.find_all('li', class_='gl-item')
        ids = []
        for li in li_s:
            id = li.get('data-sku')
            ids.append(id)  # 记录前30条商品的所有ID
            price = li.find('div', class_='p-price').find('i').text
            detail_url = li.find('div', class_='p-img').find('a').get('href')
            if not detail_url.startswith("https"):
                detail_url = "https:" + detail_url
            yield Request(detail_url, callback=self.parse_detail_page, meta={'item': copy.deepcopy(item), 'price': price})
        self.page += 1
        if not self.page % 2:
            print(self.next_url.format(GoodsBrand=item['GoodsBrand'], page=self.page, ids=",".join(ids)), "??????????")
            headers = {'referer': response.url,
                       "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3710.0 Safari/537.36"
                       }
            # 拼接并访问后30条信息的url
            yield Request(self.next_url.format(GoodsBrand=item['GoodsBrand'], page=self.page, ids=",".join(ids)), \
                          callback=self.parse_index_page, headers=headers, meta={'item': copy.deepcopy(item)})
        else:
            if self.page <= self.count_page:
                yield Request(self.index_url.format(GoodsBrand=item['GoodsBrand'], page=self.page), \
                              callback=self.parse_index_page, meta={'item': copy.deepcopy(item)})

    def parse_detail_page(self, response):
        """
        解析详情并获取相关商品信息并存储到item，最后访问评论api，获得评论信息
        :param response:
        :return:
        """
        item = response.meta['item']
        item["GoodsPrice"] = float(response.meta['price'])
        content = response.text
        soup = BeautifulSoup(content, 'lxml')
        data = soup.find('div', class_='p-parameter')
        item['GoodsId'] = data.find(text=re.compile("商品编号：(.*?)")).split('：')[1].strip()
        item['GoodsName'] = data.find(text=re.compile("商品名称：(.*?)")).split('：')[1].strip()
        GoodsWeight = data.find(text=re.compile("商品毛重：(.*?)"))
        if GoodsWeight:
            GoodsWeight = GoodsWeight.split('：')[1].strip()
            weigth = float(re.match(r'\d+\.\d+', GoodsWeight).group())
            if 'kg' in GoodsWeight:
                weigth = weigth * 1000
            item['GoodsWeight'] = weigth
        classify = data.find(text=re.compile("分类：(.*?)"))
        item['classify'] = ""
        if classify:
            item['classify'] = classify.split('：')[1].strip()
        yield Request(self.comment_url.format(GoodsId=item['GoodsId']), callback=self.parse_comments, \
                      meta={'item': copy.deepcopy(item)})

    def parse_comments(self, response):
        """
        获得api内容并json转换，最后把数据存储到item
        :param response:
        :return:
        """
        item = response.meta['item']
        content = response.text
        try:
            content = content.decode('gbk')
        except Exception:
            pass
        data = json.loads(content)

        GoodsComment = data['CommentsCount'][0].get('GoodCountStr')
        item['GoodsComment'] = int(re.match(r'\d+', GoodsComment).group())
        if '万' in GoodsComment:
            item['GoodsComment'] = item['GoodsComment'] * 10000

        GeneralComment = data['CommentsCount'][0].get('GeneralCountStr')
        item['GeneralComment'] = int(re.match(r'\d+', GeneralComment).group())
        if '万' in GeneralComment:
            item['GeneralComment'] = item['GeneralComment'] * 10000

        PoorComment = data['CommentsCount'][0].get('PoorCountStr')
        item['PoorComment'] = int(re.match(r'\d+', PoorComment).group())
        if '万' in PoorComment:
            item['PoorComment'] = item['PoorComment'] * 10000

        SumComment = data['CommentsCount'][0].get('CommentCountStr')
        item['SumComment'] = int(re.match(r'\d+', SumComment).group())
        if '万' in SumComment:
            item['SumComment'] = item['SumComment'] * 10000

        yield item

