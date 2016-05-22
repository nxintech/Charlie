# -*- coding:utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import jenkins
from scrapy.utils.log import configure_logging
from scrapy.crawler import Crawler
from scrapy import signals, Spider, Item, Field
from scrapy.loader import ItemLoader
from scrapy.loader.processors import Compose, MapCompose, TakeFirst
from scrapy.settings import Settings
from twisted.internet import reactor

from job_transform import transform
from config_parser import parse_section

From = parse_section("from")  # original jenkins config
To = parse_section("to")  # target jenkins config
url = From[0]


class JenkinsJobItem(Item):
    status = Field()  # job status: enabled or disabled
    name = Field()  # job name


class JenkinsJobItemLoader(ItemLoader):
    default_input_processor = MapCompose(unicode.strip)
    default_output_processor = TakeFirst()

    name_out = Compose(lambda name: name[0])
    status_out = Compose(lambda status: True if status == ["4"] else False)


class JenkinsJobSpider(Spider):
    name = "jenkins_spider"
    start_urls = [url]

    def parse(self, response):
        for sel in response.xpath('//tr[@class!="header"]'):
            loader = JenkinsJobItemLoader(
                JenkinsJobItem(), selector=sel, response=response)
            loader.add_xpath('status', 'td[1]/@data')
            loader.add_xpath('name', 'td[3]/a/text()')
            yield loader.load_item()


class JsonWriterPipeline(object):
    def __init__(self):
        self.original = jenkins.Jenkins(*From)
        self.target = jenkins.Jenkins(*To)

    def process_item(self, item, spider):
        if item["status"]:
            transform(self.original, self.target, item["name"].encode("utf-8"))
        return item


# callback fired when the spider is closed
def callback(spider, reason):
    stats = spider.crawler.stats.get_stats()
    reactor.stop()  # stop the reactor
    print("Done!")
    print(stats)


def run_spider():
    settings = Settings()
    settings.set('ITEM_PIPELINES', {
        '__main__.JsonWriterPipeline': 100
    })

    # enable remote sever certificate verification
    # see http://doc.scrapy.org/en/latest/topics/settings.html#downloader-clientcontextfactory
    settings.set('DOWNLOADER_CLIENTCONTEXTFACTORY',
                 'scrapy.core.downloader.contextfactory.BrowserLikeContextFactory'
                 )

    # uncomment below line to enable the logging for debug
    # configure_logging()

    crawler = Crawler(JenkinsJobSpider, settings)
    crawler.signals.connect(callback, signal=signals.spider_closed)
    crawler.crawl()
    reactor.run()


if __name__ == '__main__':
    run_spider()
