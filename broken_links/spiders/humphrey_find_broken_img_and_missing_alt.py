import requests
import scrapy
from scraper_helper import headers, run_spider
from urllib.parse import urlparse


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



class HumphreyBrokenImgSpider(scrapy.Spider):
    
    
    name = "humphrey_find_broken_img_and_missing_alt"


    skip_keywords = ['logout', 'edit', 'directory', 'wp-admin' , 'remove', 'delete', 'my-profile' ]

    

    #handle_httpstatus_list = [i for i in range(400, 999)]

    def start_requests(self):

        cookies= self.run_selenium()

        self.logger.info("Start scraping: %s",START_PAGE )

        yield scrapy.Request(START_PAGE, cb_kwargs={
            'source': 'NA',
            'site': site_name,
            'cookies' : cookies
        }, errback=self.handle_error,cookies=cookies)

    def run_selenium(self):
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from selenium_recaptcha_solver import RecaptchaSolver
        from time import sleep
        s = Service('/usr/local/bin/chromedriver')

        driver = webdriver.Chrome(service=s)

        login_page_link = START_PAGE+'login/'

        #print(login_page_link)

        driver.get(login_page_link)
        

        # username = '' #add user name here
        # password = '' #add password here
        

        # usernamebox= driver.find_element(by=By.ID, value="user") #user user_login
        # usernamebox.send_keys(username)

        # passwordbox= driver.find_element(by=By.ID, value="pass") #pass user_pass
        # passwordbox.send_keys(password)

        # # solver = RecaptchaSolver(driver=driver)
        # # recaptcha_iframe = driver.find_element(By.XPATH, '//iframe[@title="reCAPTCHA"]')
        # # solver.click_recaptcha_v2(iframe=recaptcha_iframe)


        sleep(30)

        login = driver.find_element(by=By.ID, value="wp-submit")
        login.click()
        sleep(5)


        my_account_element = driver.find_element(By.CSS_SELECTOR, "#wp-admin-bar-my-account")
   
        if my_account_element:
            print("Login Successful")
        else:
            print("Login Failed")

        cookies= driver.get_cookies()
        print(cookies)
        return cookies

    def parse(self, response, source, site, cookies):
        if response.status !=200:
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
            }, callback=self.parse_img, errback=self.handle_img_error, cookies=cookies)

        
        for a in response.xpath('//a'):
            link = response.urljoin(a.xpath('./@href').get())
            if not is_valid_url(link):
                continue
            if follow_this_domain(link):
                if not any(keyword in link.lower() for keyword in self.skip_keywords):
                    yield scrapy.Request(link, cb_kwargs={
                        'source': response.url,
                        'site':site,
                        'cookies' : cookies
                    }, errback=self.handle_error,cookies=cookies)
                else:
                    self.logger.info(f"Skipping link with one of the skip keywords: {link}") 

    
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
    run_spider(HumphreyBrokenImgSpider)