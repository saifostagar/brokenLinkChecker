# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class BrokenLinksPipeline:
    def process_item(self, item, spider):
        return item
    
# Import necessary modules
from scrapy.exceptions import DropItem
import csv
import datetime
# Define the custom pipeline class
class SeparateFilePipeline:
    def __init__(self, spider_name):
        self.spider_name = spider_name
        
        self.csv_writers = {}

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.spider.name)

    def open_spider(self, spider):
        pass

    def close_spider(self, spider):
        for csv_file in self.csv_writers.values():
            csv_file.close()

    def process_item(self, item, spider):

        # if spider.name != self.spider_name:
        #     raise DropItem("Item does not belong to this spider")

        site_name = item.get('Site Name')
        #if not site_name:
        #     raise DropItem("Item missing 'Site Name'")
        
                
        if spider.name == "find_broken_img":
            

            if site_name not in self.csv_writers:
                filename = f"{site_name}_Broken_Img_{datetime.datetime.now().strftime('%Y%m%d')}.csv"
                csv_file = open(filename, 'w', newline='', encoding='utf-8')
                fieldnames = ['Source_Page', 'Image_Link', 'HTTP_Code', 'Missing Alt', 'Alt Text']
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()
                self.csv_writers[site_name] = (csv_file, writer)

        if spider.name == "find_broken" or spider.name == "humphrey_brokenlink":
            
            if site_name not in self.csv_writers:
                filename = f"{site_name}_Broken_Links_{datetime.datetime.now().strftime('%Y%m%d')}.csv"
                csv_file = open(filename, 'w', newline='', encoding='utf-8')
                fieldnames = ['Source_Page', 'Link_Text', 'Broken_Page_Link', 'HTTP_Code', 'External']
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()
                self.csv_writers[site_name] = (csv_file, writer)

        csv_file, writer = self.csv_writers[site_name]
        item.pop('Site Name')
        writer.writerow(item)
        return item
