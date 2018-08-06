# -*- coding: utf-8 -*-
import scrapy
import re
from ..items import NewHouseItem, ESFHouseItem
from traceback import format_exc
from scrapy_redis.spiders import RedisSpider


class SfwSpider(RedisSpider):
    name = 'sfw'
    allowed_domains = ['fang.com']
    # start_urls = ['http://www.fang.com/SoufunFamily.htm']
    redis_key = 'sfwSpider:start_urls'

    def parse(self, response):
        trs = response.xpath("//div[@class='outCont']//tr")
        # 开始将省份设置为None
        province = None
        for tr in trs:
            tds = tr.xpath(".//td[not(@class)]")
            province_td = tds[0]
            province_text = province_td.xpath(".//text()").extract_first()
            province_text = re.sub(r"\s", "", province_text)
            if province_text:
                province = province_text

            # 不爬取海外的城市的房源
            if province == "其它":
                continue

            city_td = tds[1]
            city_links = city_td.xpath(".//a")
            for city_link in city_links:
                city = city_link.xpath(".//text()").extract_first()
                city_url = city_link.xpath(".//@href").extract_first()
                print("省份:", province)
                print("城市:", city)
                print("城市链接:", city_url)
                # 构建新房的url链接
                url_module = city_url.split("//")
                scheme = url_module[0]
                domain = url_module[1]
                # 北京比较特别, "http://newhouse.fang.com/house/s"就代表北京新房, "http://esf.fang.com"就代表北京二手房
                if 'bj.' in domain:
                    newhouse_url = "http://newhouse.fang.com/house/s"
                    esf_url = "http://esf.fang.com"
                else:
                    newhouse_url = scheme + "//" + "newhouse." + domain + "house/s/"
                    # 构建二房子的url链接
                    esf_url = scheme + "//" + "esf." + domain
                print("城市:%s%s" % (province, city))
                print("新房链接:%s" % newhouse_url)
                print("二手房链接:%s" % esf_url)
                # 回调新房信息
                yield scrapy.Request(url=newhouse_url,
                                     callback=self.parse_newhouse,
                                     # meta间传值
                                     meta={"info": (province, city)},
                                     priority=20)
                # 回调二手房信息
                yield scrapy.Request(url=esf_url,
                                     callback=self.parse_esf,
                                     errback=self.error_back,
                                     meta={"info": (province, city)},
                                     priority=10)

    def parse_newhouse(self, response):
        """
        这个函数用来解析新房信息
        """
        # 拿到省份和城市
        province, city = response.meta.get("info")
        lis = response.xpath("//div[contains(@class, 'nl_con')]/ul/li")
        for li in lis:
            # 名字
            name = str(li.xpath(".//div[@class='nlcd_name']/a/text()").extract_first()).strip()
            house_type_list = li.xpath(".//div[contains(@class, 'house_type')]/a/text()").extract()
            house_type_list = list(map(lambda x: re.sub(r"\s", "", x), house_type_list))
            # 户型,　几室几厅
            rooms = list(filter(lambda x: x.endswith("居"), house_type_list))
            # 面积
            area = "".join(li.xpath(".//div[contains(@class, 'house_type')]/text()").extract())
            area = re.sub(r"\s|—|/|－", "", area)
            # 地址
            address = li.xpath(".//div[@class='address']/a/@title").extract_first()
            # 行政区
            district_text = "".join(li.xpath(".//div[@class='address']/a//text()").extract())
            district = re.findall(r".*\[(.+)\].*", district_text)
            if len(district) > 0:
                district = district[0]
            else:
                district = None
            # 是否在售
            sale = li.xpath(".//div[contains(@class, 'fangyuan')]/span/text()").extract_first()
            # 价格
            price = "".join(li.xpath(".//div[@class='nhouse_price']//text()").extract())
            price = re.sub(r"\s|广告", "", price)
            # 拿到详情页的url
            origin_url = li.xpath(".//div[@class='nlcd_name']/a/@href").extract_first()

            item = NewHouseItem(name=name, rooms=rooms, area=area,
                                address=address, district=district,
                                sale=sale, price=price, origin_url=origin_url,
                                province=province, city=city)
            print(item)
            yield item

        # 翻页代码
        next_url = response.xpath("//div[@class='page']//a[@class='next']/@href").extract_first()
        if next_url:
            yield scrapy.Request(url=response.urljoin(next_url),
                                 callback=self.parse_newhouse,
                                 errback=self.error_back,
                                 meta={"info": (province, city)},
                                 priority=20)

    def parse_esf(self, response):
        """
        这个函数用来解析二手房信息
        """
        province, city = response.meta.get("info")
        dls = response.xpath("//div[@class='shop_list shop_list_4']/dl")
        for dl in dls:
            item = ESFHouseItem(province=province, city=city)
            # 名字
            item["name"] = dl.xpath(".//p[@class='add_shop']/a/@title").extract_first()
            infos = dl.xpath(".//p[@class='tel_shop']/text()").extract()
            infos = list(map(lambda x: re.sub(r"\s", "", x), infos))
            for info in infos:
                if "厅" in info:
                    # 户型, 及室几厅
                    item["rooms"] = info
                elif "层" in info:
                    # 楼层
                    item["floor"] = info
                elif "向" in info:
                    # 朝向
                    item["toward"] = info
                elif "㎡" in info:
                    # 建筑面积
                    item["area"] = info
                elif "年" in info:
                    # 年代
                    item["year"] = info

            # 地址
            item["address"] = dl.xpath(".//p[@class='add_shop']/a/@title").extract_first()
            # 总价
            item["price"] = "".join(dl.xpath(".//dd[@class='price_right']/span[1]//text()").extract())
            # 单价
            item["unit"] = "".join(dl.xpath(".//dd[@class='price_right']/span[2]//text()").extract())
            detail_url = dl.xpath(".//dt[@class='floatl']/a/@href").extract_first()
            # 拿到详情页的url
            item["origin_url"] = response.urljoin(detail_url)
            print(item)
            yield item

        # 翻页代码
        next_url = re.findall(r'<a href="(.*?)">下一页</a>', response.text)
        if len(next_url) > 0:
            next_url = next_url[0]
            print(response.urljoin(next_url))
            yield scrapy.Request(url=response.urljoin(next_url),
                                 callback=self.parse_esf,
                                 errback=self.error_back,
                                 meta={"info": (province, city)},
                                 priority=20)

    def error_back(self, e):
        """
        报错机制
        """
        self.logger.error(format_exc())
