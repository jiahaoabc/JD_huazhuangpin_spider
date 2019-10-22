# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymysql


class JingdongPipeline(object):
    def __init__(self):
        # 连接数据库
        self.connect = pymysql.connect(
            host='127.0.0.1',  # 数据库地址
            port=3306,  # 数据库端口
            db='jd',  # 数据库名
            user='root',  # 数据库用户名
            passwd='12345678',  # 数据库密码
            charset='utf8',  # 编码方式
            use_unicode=True)

        # 通过cursor执行增删查改
        self.cursor = self.connect.cursor()

    def process_item(self, item, spider):
        sql = """insert  ignore  into cosmetics(GoodsId, GoodsPrice, GoodsName, GoodsBrand ,classify,
                 GoodsWeight, SumComment,GoodsComment, GeneralComment, PoorComment)
                 value (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        self.cursor.execute(sql,  # python操作mysql知识
            (item['GoodsId'],  # item里面定义的字段和表字段对应
             item['GoodsPrice'],
             item['GoodsName'],
             item['GoodsBrand'],
             item['classify'],
             item['GoodsWeight'],
             item['SumComment'],
             item['GoodsComment'],
             item['GeneralComment'],
             item['PoorComment'])
        )

        # 提交sql语句
        self.connect.commit()

        return item
