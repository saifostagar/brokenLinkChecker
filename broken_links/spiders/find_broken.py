import scrapy
from scraper_helper import headers, run_spider
from urllib.parse import urlparse
import csv

site_names = []
website_urls = []

csv_file = 'sites.csv'

with open(csv_file, newline='') as csvfile:
    csv_reader = csv.reader(csvfile)
    
    # Skip the header row
    next(csv_reader)
    
    # Iterate through each row in the CSV file
    for row in csv_reader:
        site_name = row[0]
        website_url = row[1]
        
        # Append the site name and website URL to their respective lists
        site_names.append(site_name)
        website_urls.append(website_url)


def is_valid_url(url):
    try:
        result = urlparse(url.strip())
        return all([result.scheme, result.netloc])
    except:
        return False


def follow_this_domain(link):
    link_domain = urlparse(link.strip()).netloc
    for website_url in website_urls:
        if urlparse(website_url).netloc == link_domain:
            return True
    return False

class FindBrokenSpider(scrapy.Spider):
    name = "find_broken"

    custom_settings = {
        'FEEDS': {
            'output.csv': {'format': 'csv', 'overwrite': True},
        }
    }

    

    handle_httpstatus_list = [i for i in range(400, 600)]

    def start_requests(self):

        for website_url in website_urls:
            print("Start Scraping"+website_url)

            yield scrapy.Request(website_url, cb_kwargs={
            'source': 'NA',
            'text': 'NA'
        }, errback=self.handle_error)

    def parse(self, response, source, text):
        if response.status in self.handle_httpstatus_list:
            item = dict()
            item["Source_Page"] = source
            item["Link_Text"] = text
            item["Broken_Page_Link"] = response.url
            item["HTTP_Code"] = response.status
            item["External"] = not follow_this_domain(response.url)
            yield item
            return  # do not process further for non-200 status codes

        content_type = response.headers.get("content-type", "").lower()
        self.logger.debug(f'Content type of {response.url} is f{content_type}')
        if b'text' not in content_type:
            self.logger.info(f'{response.url} is NOT HTML')
            return  # do not process further if not HTML

        for a in response.xpath('//a'):
            text = a.xpath('./text()').get()
            link = response.urljoin(a.xpath('./@href').get())
            if not is_valid_url(link):
                return
            if follow_this_domain(link):
                yield scrapy.Request(link, cb_kwargs={
                    'source': response.url,
                    'text': text
                }, errback=self.handle_error)
            else:
                yield scrapy.Request(link, cb_kwargs={
                    'source': response.url,
                    'text': text
                }, callback=self.parse_external, errback=self.handle_error)

    def handle_error(self, failure):
        # log all failures
        self.logger.error(repr(failure))
        request = failure.request
        self.logger.error(f'Unhandled error on {request.url}')
        item = dict()
        item["Source_Page"] = 'Unknown'
        item["Link_Text"] = None
        item["Broken_Page_Link"] = request.url
        item["HTTP_Code"] = 'DNSLookupError or other unhandled'
        item["External"] = not follow_this_domain(request.url)
        yield item

    def parse_external(self, response, source, text):

        if response.status != 200:
            item = dict()

            item["Source_Page"] = source
            item["Link_Text"] = text.strip()
            item["Broken_Page_Link"] = response.url
            item["HTTP_Code"] = response.status
            item["External"] = not follow_this_domain(response.url)

            yield item


if __name__ == '__main__':
    run_spider(FindBrokenSpider)
