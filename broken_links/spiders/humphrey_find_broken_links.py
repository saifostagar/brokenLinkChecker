import requests
import scrapy
from scraper_helper import headers, run_spider
from urllib.parse import urlparse
import os


START_PAGE = 'https://www.humphreyfellowship.org/'

site_name = 'Humphrey'
     

def is_valid_url(url):
    try:
        result = urlparse(url.strip())
        return all([result.scheme, result.netloc])
    except:
        return False


def follow_this_domain(link):
    return urlparse(link.strip()).netloc == urlparse(START_PAGE).netloc



class HumphreyBrokenLinkSpider(scrapy.Spider):
    
    
    name = "humphrey_find_broken_links"


    skip_keywords = ['logout', 'edit', 'directory', 'wp-admin' , 'remove', 'delete', 'my-profile' ]

    

    handle_httpstatus_list = [i for i in range(400, 999)]

    def start_requests(self):

        cookies={}

        cookies['wordpress_logged_in_3cd690aa3c8cf1a5ec4558652b9842b6']= 'md_saif%7C1712734566%7C9gW9Nql6terZXcJQX7AWTDZFTHtNegtt4ZTIZyYfZEV%7C76cc0b3cf90d8b2a52d266396168749ed73f83aebb4540cd6040882fb7b3ad37'

        self.logger.info("Start scraping: %s",START_PAGE )

        yield scrapy.Request(START_PAGE, cb_kwargs={
            'source': 'NA',
            'text': 'NA',
            'site': site_name,
            'cookies' : self.cookies
        }, errback=self.handle_error,cookies=self.cookies)

    # def run_selenium(self):
    #     from selenium import webdriver
    #     from selenium.webdriver.common.by import By
    #     from selenium.webdriver.chrome.service import Service
    #     from selenium.webdriver.chrome.options import Options
    #     from selenium_recaptcha_solver import RecaptchaSolver
    #     from time import sleep
    #     s = Service('/usr/local/bin/chromedriver')

    #     driver = webdriver.Chrome(service=s)

    #     login_page_link = START_PAGE+'login/'

    #     #print(login_page_link)

    #     driver.get(login_page_link)
        

    #     # username = '' #add user name here
    #     # password = '' #add password here
        

    #     # usernamebox= driver.find_element(by=By.ID, value="user") #user user_login
    #     # usernamebox.send_keys(username)

    #     # passwordbox= driver.find_element(by=By.ID, value="pass") #pass user_pass
    #     # passwordbox.send_keys(password)

    #     # # solver = RecaptchaSolver(driver=driver)
    #     # # recaptcha_iframe = driver.find_element(By.XPATH, '//iframe[@title="reCAPTCHA"]')
    #     # # solver.click_recaptcha_v2(iframe=recaptcha_iframe)


    #     sleep(30)

    #     login = driver.find_element(by=By.ID, value="wp-submit")
    #     login.click()
    #     sleep(5)


    #     my_account_element = driver.find_element(By.CSS_SELECTOR, "#wp-admin-bar-my-account")
   
    #     if my_account_element:
    #         print("Login Successful")
    #     else:
    #         print("Login Failed")

    #     cookies= driver.get_cookies()
    #     print(cookies)
    #     return cookies

    def parse(self, response, source, text, site, cookies):
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
                if not any(keyword in link.lower() for keyword in self.skip_keywords):
                    yield scrapy.Request(link, cb_kwargs={
                        'source': response.url,
                        'text': link_text,
                        'site':site,
                        'cookies' : cookies
                    }, errback=self.handle_error,cookies=cookies)
                else:
                    self.logger.info(f"Skipping link with one of the skip keywords: {link}") 
            
            else:
                yield scrapy.Request(link, cb_kwargs={
                    'source': response.url,
                    'text': link_text,
                    'site':site
                }, callback=self.parse_external, errback=self.handle_error)

        for a in response.xpath('//*[@data-column-clickable]'):
            link_text = a.xpath('./text()').get()
            link = response.urljoin(a.xpath('./@data-column-clickable').get())
            if not is_valid_url(link):
                if link.startswith('mailto:') or link.startswith('tel:') :
                    continue
                item = dict()
                item["Site Name"] = site
                item["Source_Page"] = response.url
                item["Link_Text"] = link_text
                item["Broken_Page_Link"] = link
                item["HTTP_Code"] = 'NA'
                item["External"] = 'NA' #not follow_this_domain(response.url)
                yield item
                continue
            if follow_this_domain(link):
                if not any(keyword in link.lower() for keyword in self.skip_keywords):
                    yield scrapy.Request(link, cb_kwargs={
                        'source': response.url,
                        'text': link_text,
                        'site':site,
                        'cookies' : cookies
                    }, errback=self.handle_error,cookies=cookies)
                else:
                    self.logger.info(f"Skipping link with one of the skip keywords: {link}") 
            
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
    run_spider(HumphreyBrokenLinkSpider)