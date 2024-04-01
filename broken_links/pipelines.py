# # Define your item pipelines here
# #
# # Don't forget to add your pipeline to the ITEM_PIPELINES setting
# # See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# # useful for handling different item types with a single interface
# from itemadapter import ItemAdapter


# class BrokenLinksPipeline:
#     def process_item(self, item, spider):
#         return item

from scrapy.exceptions import DropItem
import csv
import datetime
import smtplib
from email.message import EmailMessage
import config

class SeparateFilePipeline:
    def __init__(self, spider_name):
        self.spider_name = spider_name
        self.csv_writers = {}
        self.files_name = []

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.spider.name)

    def open_spider(self, spider):
        pass

    def close_spider(self, spider):
        for csv_file, _ in self.csv_writers.values():
            csv_file.close()
        self.send_mail()

    def send_mail(self):
        msg = EmailMessage()
        msg['From'] = config.EMAIL_USER
        msg['To'] = config.EMAIL_TO
        msg['Subject'] = "Report of Broken Links"
        msg.set_content("This is a Test Mail. This is Mail Body")

        for file_name in self.files_name:
            with open(file_name, 'r') as f:
                data = f.read()
            msg.add_attachment(data, filename=file_name)
        
        try:
            with smtplib.SMTP_SSL('smtp.roundcube.com', 290) as server:
                server.login(config.EMAIL_USER, config.EMAIL_PASS)
                server.send_message(msg)
                server.quit()
            print("Email sent successfully")
        except Exception as e:
            print(f"An error occurred while sending the email: {e}")

    def process_item(self, item, spider):
        site_name = item.get('Site Name')

        if spider.name == "find_broken_img_and_missing_alt" or spider.name == "humphrey_find_broken_img_and_missing_alt":
            if site_name not in self.csv_writers:
                filename = f"{site_name}_Broken_Img_{datetime.datetime.now().strftime('%Y%m%d')}.csv"
                self.files_name.append(filename)
                csv_file = open(filename, 'w', newline='', encoding='utf-8')
                fieldnames = ['Source_Page', 'Image_Link', 'HTTP_Code', 'Missing Alt', 'Alt Text']
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()
                self.csv_writers[site_name] = (csv_file, writer)

        if spider.name == "find_broken_links" or spider.name == "humphrey_find_broken_links":
            if site_name not in self.csv_writers:
                filename = f"{site_name}_Broken_Links_{datetime.datetime.now().strftime('%Y%m%d')}.csv"
                self.files_name.append(filename)
                csv_file = open(filename, 'w', newline='', encoding='utf-8')
                fieldnames = ['Source_Page', 'Link_Text', 'Broken_Page_Link', 'HTTP_Code', 'External']
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()
                self.csv_writers[site_name] = (csv_file, writer)

        csv_file, writer = self.csv_writers[site_name]
        item.pop('Site Name')
        writer.writerow(item)
        return item
