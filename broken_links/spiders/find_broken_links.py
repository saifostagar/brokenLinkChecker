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

allowed_domains = set(urlparse(site_url).netloc for site_url in site_dict.values())

#print(allowed_domains)


def is_valid_url(url):
    try:
        result = urlparse(url.strip())
        return all([result.scheme, result.netloc])
    except:
        return False


def follow_this_domain(link):
    link_domain = urlparse(link.strip()).netloc
    return link_domain in allowed_domains

class FindBrokenSpider(scrapy.Spider):
    name = "find_broken_links"

    #handle_httpstatus_list = [i for i in range(400, 999)]

    def start_requests(self):

        for key in site_dict:
            self.logger.info("Start scraping: %s",site_dict[key] )

            yield scrapy.Request(site_dict[key], cb_kwargs={
            'source': 'NA',
            'text': 'NA',
            'site':key
        }, errback=self.handle_error)

    def parse(self, response, source, text, site):
        if response.status != 200:
            item = dict()
            item["Site Name"] = site
            item["Source_Page"] = source
            item["Link_Text"] = text
            item["Broken_Page_Link"] = response.url
            item["HTTP_Code"] = response.status
            item["External"] = not follow_this_domain(response.url)
            yield item
            return  # do not process further for non-200 status codes
        # else:
        #     item = dict()
        #     item["Site Name"] = site
        #     item["Source_Page"] = source
        #     item["Link_Text"] = text
        #     item["Broken_Page_Link"] = response.url
        #     item["HTTP_Code"] = response.status
        #     item["External"] = not follow_this_domain(response.url)
        #     yield item

        content_type = response.headers.get("content-type", "").lower()
        self.logger.debug(f'Content type of {response.url} is f{content_type}')
        if b'text' not in content_type:
            self.logger.info(f'{response.url} is NOT HTML')
            return  # do not process further if not HTML

        for a in response.xpath('//a'):
            link_text = a.xpath('./text()').get()
            link = response.urljoin(a.xpath('./@href').get())
            if not is_valid_url(link):
                if link.startswith('mailto:') or link.startswith('tel:') :
                    continue
                item = dict()
                item["Site Name"] = site
                item["Source_Page"] = response.url
                item["Link_Text"] = link_text
                item["Broken_Page_Link"] = link
                item["HTTP_Code"] = 'NA'
                item["External"] = 'invalid' #not follow_this_domain(response.url)
                yield item
                continue
            if follow_this_domain(link):
                yield scrapy.Request(link, cb_kwargs={
                    'source': response.url,
                    'text': link_text,
                    'site':site
                }, errback=self.handle_error)
            else:
                yield scrapy.Request(link, cb_kwargs={
                    'source': response.url,
                    'text': link_text,
                    'site':site
                }, callback=self.parse_external, errback=self.handle_error)

    def handle_error(self, failure):
        # log all failures
        self.logger.error(repr(failure))
        request = failure.request
        self.logger.error(f'Unhandled error on {request.url}')
        item = dict()
        item["Site Name"] = request.cb_kwargs.get('site')
        item["Source_Page"] = request.cb_kwargs.get('source')
        item["Link_Text"] = request.cb_kwargs.get('text')
        item["Broken_Page_Link"] = request.url
        item["HTTP_Code"] = 'DNSLookupError or other unhandled'
        item["External"] = not follow_this_domain(request.url)
        yield item

    def parse_external(self, response, source, text, site):

        if response.status != 200:
            item = dict()
            item["Site Name"] = site
            item["Source_Page"] = source
            item["Link_Text"] = text
            item["Broken_Page_Link"] = response.url
            item["HTTP_Code"] = response.status
            item["External"] = not follow_this_domain(response.url)

            yield item


if __name__ == '__main__':
    run_spider(FindBrokenSpider)
