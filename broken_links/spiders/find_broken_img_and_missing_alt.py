import scrapy
from scraper_helper import headers, run_spider
from urllib.parse import urlparse
import csv

csv_file = 'sites.csv'

site_dict = {}

with open(csv_file, newline='') as csvfile:
    csv_reader = csv.reader(csvfile)
    
    # Skip the header row
    next(csv_reader)
    
    # Iterate through each row in the CSV file
    for row in csv_reader:
        site_name = row[0]
        website_url = row[1]
        
        # Append the site name and website URL to their respective lists
        site_dict[site_name] = website_url
        #print(site_dict)


def is_valid_url(url):
    try:
        result = urlparse(url.strip())
        return all([result.scheme, result.netloc])
    except:
        return False


def follow_this_domain(link):
    link_domain = urlparse(link.strip()).netloc
    for key in site_dict:
        if urlparse(site_dict[key]).netloc == link_domain:
            return True
    return False

class FindBrokenImgSpider(scrapy.Spider):
    name = "find_broken_img"

    handle_httpstatus_list = [i for i in range(400, 999)]

    def start_requests(self):

        for key in site_dict:
            self.logger.info("Start scraping: %s",site_dict[key] )

            yield scrapy.Request(site_dict[key], cb_kwargs={
            'source': 'NA',
            'site':key
        }, errback=self.handle_error)

    def parse(self, response, source, site):
        if response.status in self.handle_httpstatus_list:
            return  # do not process further for non-200 status codes

        content_type = response.headers.get("content-type", "").lower()
        #self.logger.debug(f'Content type of {response.url} is f{content_type}')
        if b'text' not in content_type:
            self.logger.info(f'{response.url} is NOT HTML')
            return  # do not process further if not HTML
        
        for img in response.xpath('//img'):
            alt_text = img.xpath('./@alt').get()
            img_src = response.urljoin(img.xpath('./@src').get())

            yield scrapy.Request(img_src, cb_kwargs={
                'source': response.url,
                'alt_text': alt_text,
                'site' : site
            }, callback=self.parse_img, errback=self.handle_img_error)


        for a in response.xpath('//a'):
            link = response.urljoin(a.xpath('./@href').get())
            if not is_valid_url(link):
                return
            if follow_this_domain(link):
                yield scrapy.Request(link, cb_kwargs={
                    'source': response.url,
                    'site':site
                }, errback=self.handle_error)
            

    def handle_error(self, failure):
        # log all failures
        self.logger.error(repr(failure))
        request = failure.request
        self.logger.error(f'Unhandled error on {request.url}')

    def handle_img_error(self, failure):
        # log all failures
        self.logger.error(repr(failure))
        request = failure.request
        self.logger.error(f'Unhandled error on {request.url}')
        item = dict()
        item["Site Name"] = request.cb_kwargs.get('site')
        item["Source_Page"] = request.cb_kwargs.get('source')
        item["Image_Link"] = request.url
        item["HTTP_Code"] = 'DNSLookupError or other unhandled'
        item["Missing Alt"]= 'NA'
        item["Alt Text"] = 'NA'
        
        yield item


    def parse_img(self, response, source, alt_text, site):

        if response.status != 200:
            item = dict()
            item["Site Name"] = site
            item["Source_Page"] = source
            item["Image_Link"] = response.url
            item["HTTP_Code"] = response.status
            item["Missing Alt"]= 'NA'
            item["Alt Text"] = 'NA'

            yield item
        
        else:
            item = dict()
            item["Site Name"] = site
            item["Source_Page"] = source
            item["Image_Link"] = response.url
            item["HTTP_Code"] = response.status
            item["Missing Alt"]= not alt_text
            item["Alt Text"] = alt_text

            yield item


if __name__ == '__main__':
    run_spider(FindBrokenImgSpider)
