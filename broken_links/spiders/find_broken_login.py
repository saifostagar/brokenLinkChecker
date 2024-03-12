import requests
import scrapy
from scraper_helper import headers, run_spider
from urllib.parse import urlparse
import csv



START_PAGE = 'https://www.humphreyfellowship.org'

def run_selenium():
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium_recaptcha_solver import RecaptchaSolver
    from time import sleep
    s = Service('/usr/local/bin/chromedriver')

    driver = webdriver.Chrome(service=s)

    driver.get("https://www.humphreyfellowship.org/login/")

    password = 'ENTER YOUR PASSWORD HERE'
    username = 'ENTER YOUR USER NAME HERE'

    usernamebox= driver.find_element(by=By.ID, value="user") #user user_login
    usernamebox.send_keys(username)

    passwordbox= driver.find_element(by=By.ID, value="pass") #pass user_pass
    passwordbox.send_keys(password)

    # solver = RecaptchaSolver(driver=driver)
    # recaptcha_iframe = driver.find_element(By.XPATH, '//iframe[@title="reCAPTCHA"]')
    # solver.click_recaptcha_v2(iframe=recaptcha_iframe)

    sleep(30)

    login = driver.find_element(by=By.ID, value="wp-submit")
    login.click()
    sleep(5)

    # try:
    #     display_name = driver.find_element(By.CLASS_NAME, "display-name").text
    #     if display_name == "Md Saif Ostagar":
    #         print("Login successful")
    #     else:
    #         print("Login failed")
    # except Exception as e:
    #     print("Login failed")

    cookies= driver.get_cookies()
    print(cookies)
    return cookies


def is_valid_url(url):
    try:
        result = urlparse(url.strip())
        return all([result.scheme, result.netloc])
    except:
        return False


def follow_this_domain(link):
    return urlparse(link.strip()).netloc == urlparse(START_PAGE).netloc



class FindBrokenLoginSpider(scrapy.Spider):
    name = "find_broken_login"

    if START_PAGE=='https://www.humphreyfellowship.org':
        cookies=run_selenium()

    custom_settings = {
        'FEEDS': {
            'humphrey_output.csv': {'format': 'csv', 'overwrite': True},
        }
    }

    skip_keywords = ['logout', 'edit', 'directory', 'wp-admin' , 'remove', 'delete']

    

    handle_httpstatus_list = [i for i in range(400, 999)]

    def start_requests(self):

        
        self.logger.info("Start scraping: %s",START_PAGE )

        yield scrapy.Request(START_PAGE, cb_kwargs={
            'source': 'NA',
            'text': 'NA',
            'site': START_PAGE
        }, errback=self.handle_error,cookies=self.cookies)

    def parse(self, response, source, text, site):
        if response.status in self.handle_httpstatus_list:
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
            text = a.xpath('./text()').get()
            link = response.urljoin(a.xpath('./@href').get())
            if not is_valid_url(link):
                return
            if follow_this_domain(link):
                if not any(keyword in link.lower() for keyword in self.skip_keywords):
                    yield scrapy.Request(link, cb_kwargs={
                        'source': response.url,
                        'text': text,
                        'site':site
                    }, errback=self.handle_error,cookies=self.cookies)
                else:
                    self.logger.info(f"******************Skipping link with one of the skip keywords: {link}") 
            
            else:
                yield scrapy.Request(link, cb_kwargs={
                    'source': response.url,
                    'text': text,
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
            item["Link_Text"] = text.strip()
            item["Broken_Page_Link"] = response.url
            item["HTTP_Code"] = response.status
            item["External"] = not follow_this_domain(response.url)

            yield item


if __name__ == '__main__':
    run_spider(FindBrokenLoginSpider)
