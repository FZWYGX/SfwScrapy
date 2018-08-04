# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from traceback import format_exc
from .items import NewHouseItem, ESFHouseItem


class FangPipeline(object):

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.client = None
        self.db = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGODB_URI'),
            mongo_db=crawler.settings.get('MONGODB_DATABASE')
        )

    def open_spider(self, spider):
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        self.db['NewHouse'].ensure_index('origin_url', unique=True)
        self.db['EsfHouse'].ensure_index('origin_url', unique=True)

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        try:
            if isinstance(item, NewHouseItem):
                self.db['NewHouse'].update({'origin_url': item['origin_url']}, {'$set': item}, upsert=True)
            elif isinstance(item, ESFHouseItem):
                self.db['EsfHouse'].update({'origin_url': item['origin_url']}, {'$set': item}, upsert=True)
        except DuplicateKeyError:
            spider.logger.debug('duplicate key error collection')
        except Exception as e:
            spider.logger.error(format_exc())
        return item
