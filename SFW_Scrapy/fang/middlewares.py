# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

from twisted.internet.defer import DeferredLock
import random
from datetime import datetime, timedelta
from .Utils_Model.UserAgent import USER_AGENT


class UAMiddleware(object):
    def __init__(self):
        self.lock = DeferredLock()
        self.update_time = datetime.now()
        self.UA_List = USER_AGENT

    def process_request(self, request, spider):
        self.lock.acquire()
        if self.is_expiring:
            ua = random.choices(self.UA_List)
            request.headers['User-Agent'] = ua
            print(request.headers['User-Agent'])
        self.lock.release()

    def process_response(self, request, response, spider):
        return response

    def process_exception(self, request, exception, spider):
        pass

    @property
    def is_expiring(self):
        now = datetime.now()
        if (now - self.update_time) > timedelta(seconds=30):
            self.update_time = datetime.now()
            print("跟换USER_AGENT")
            return True
        else:
            return False