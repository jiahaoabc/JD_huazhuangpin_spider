# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Field
import scrapy


class GoodsItem(scrapy.Item):
    # define the fields for your item here like:
    GoodsPrice = Field()  # 商品价格
    GoodsComment = Field()  # 好评
    GeneralComment = Field()  # 中评
    PoorComment = Field()  # 差评
    SumComment = Field()  # 总评论数
    GoodsId = Field()  # 商品编号
    GoodsName = Field()  # 商品名称
    GoodsBrand = Field()  # 商品品牌
    classify = Field()  # 商品类型
    GoodsWeight = Field()  # 商品毛重
