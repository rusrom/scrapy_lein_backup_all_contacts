# -*- coding: utf-8 -*-
import scrapy
import re

from scrapy.utils.response import open_in_browser
from john_lien.items import JohnLienItem
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose
from w3lib.html import replace_escape_chars
from time import sleep


def get_string_with_data(val):
    res = ''
    data = val.get()
    if data:
        data = data.strip()
        if data:
            res = data + '\n'

    return res


def clear_row_contact_data(val):
    # strip all list elements
    val = list(map(lambda x: x.strip(), val))
    # remove empty elements from the list
    val = [el for el in val if el]
    # making result string
    return ' '.join(val)


def get_field(val, field):
    items = val.split('\n')
    name = [target for target in items if field in target]
    if name:
        res = re.sub(r'^{}[^\w]*'.format(field), '', name[0])
    else:
        # no field in val
        res = ''
    return res


class CheckLoginSpider(scrapy.Spider):
    name = 'check_login'
    allowed_domains = ['wcaworld.com']
    start_urls = ['https://www.wcaworld.com/directory']

    # Login to wcaworld site
    def parse(self, response):
        # open_in_browser(response)
        return scrapy.FormRequest.from_response(
            response,
            formxpath=('//form[@id="login-form"]'),
            formdata={'username': '**********', 'password': '**********'},
            callback=self.after_login
        )

    # # Search all USA companies
    def after_login(self, response):
        # open_in_browser(response)
        # for USA
        # search_url = 'http://www.wcaworld.com/Directory?networkId=24&pageNumber=1&pageSize=100&allnet=yes&networkIds=1&networkIds=2&networkIds=3&networkIds=4&networkIds=61&networkIds=98&networkIds=108&networkIds=6&networkIds=5&networkIds=22&networkIds=13&networkIds=18&networkIds=15&networkIds=16&networkIds=105&networkIds=38&licenseIds=0&licenseIds=0&licenseIds=0&licenseIds=0&searchby=CountryCode&orderby=CountryCity&country=US&statecity=&city=&keyword='
        # for China
        search_url = 'https://www.wcaworld.com/Directory?networkId=24&pageNumber=1&pageSize=100&allnet=yes&networkIds=1&networkIds=2&networkIds=3&networkIds=4&networkIds=61&networkIds=98&networkIds=108&networkIds=6&networkIds=5&networkIds=22&networkIds=13&networkIds=18&networkIds=15&networkIds=16&networkIds=105&networkIds=38&licenseIds=0&licenseIds=0&licenseIds=0&licenseIds=0&searchby=CountryCode&orderby=CountryCity&country=CN&city=&keyword='
        yield scrapy.Request(search_url, callback=self.parse_list_companies)

    # Parse list of companies
    def parse_list_companies(self, response):
        open_in_browser(response)
        links = response.xpath('//div[@id="directory_result"]//li/a[starts-with(@href, "/directory/member")]/@href')
        # links = response.xpath('//div[@id="directory_result"]//li/a/@href')
        for link in links:
            yield response.follow(link, callback=self.parse_company)

        # Infinite scrolling
        infinit_scroll = response.xpath('//a[@href="#" and contains(., "CLICK HERE")]/@onmouseover').extract_first()
        if infinit_scroll:
            url_get_parameters = re.search(r"\('([^']+)'\)", infinit_scroll)

            if url_get_parameters:
                # Pause between pages
                sleep(420)
                url_get_parameters = url_get_parameters.group(1)
                next_page = 'http://www.wcaworld.com/directory/next' + url_get_parameters
                yield scrapy.Request(next_page, callback=self.parse_list_companies)

    # Parse target company page
    def parse_company(self, response):
        # open_in_browser(response)
        l = ItemLoader(item=JohnLienItem(), response=response)
        l.default_input_processor = MapCompose(lambda x: x.strip(), replace_escape_chars)
        l.default_output_processor = TakeFirst()

        l.add_xpath('Company_ID', '//div[@class="member_name"]/following-sibling::div[@class="member_id"]/text()')
        l.add_xpath('Company_Name', '//div[@class="member_name"]/text()')
        l.add_xpath('Head_office_or_Branch_office', '//div[@class="member_name"]/span/text()')
        l.add_xpath('Network_Memberships', '//div[@class="member_of_mainbox"]//img/@alt')
        l.add_xpath('Company_description', '//div[@class="memberprofile_row memberprofile_detail"]/text()')

        table_with_data = response.xpath('//div[@class="memberprofile_row table-responsive"]/table')
        l.add_value('Company_address_line_1', table_with_data.xpath('./tr[contains(string(), "Address:")]/td[last()]/span/text()').getall())
        l.add_value('Company_address_line_2', 'NOT FOUND')
        l.add_value('Company_city', 'INSIDE Contacts_Array\nDifficult to find due to random data')
        l.add_value('Company_state_or_province', 'INSIDE Contacts_Array\nDifficult to find due to random data')
        l.add_value('Company_postal_code', 'INSIDE Contacts_Array\nDifficult to find due to random data')
        l.add_value('Company_phone', table_with_data.xpath('./tr[contains(string(), "Telephone:")]/td[last()]/text()').get())
        l.add_value('Company_fax', table_with_data.xpath('./tr[contains(string(), "Fax:")]/td[last()]/text()').get())
        l.add_value('Company_emergency', table_with_data.xpath('./tr[contains(string(), "Emergency")]/td[last()]//text()[normalize-space()]').getall())
        l.add_value('Website_URL', table_with_data.xpath('./tr[contains(string(), "Website:")]/td[last()]/a/@href').get())
        l.add_value('Company_email', table_with_data.xpath('./tr[contains(string(), "Email:")]/td[last()]//text()[normalize-space()]').getall())

        contacts_block = response.xpath(
            '//div[@class="memberprofile_row table-responsive"]/table//tr[contains(string(), "Contact:")]/following-sibling::tr[td[contains(text(), "Name")]] | '
            '//div[@class="memberprofile_row table-responsive"]/table//tr[contains(string(), "Contact:")]/following-sibling::tr[td[contains(text(), "Name")]]/following-sibling::tr'
        )
        contacts_array = []
        contact_data = []
        for contact in contacts_block:
            if len(contact.xpath('./td')) > 1:
                # scrape contact data
                tr_content = contact.xpath('./td//text()').getall()
                row_string = clear_row_contact_data(tr_content)
                contact_data.append(row_string)
            else:
                # add contact data to contact array
                contacts_array.append(contact_data)
                contact_data = []

        l.add_value('Contacts_Array', contacts_array)

        l.add_value('wcaworld_url', response.url)

        item = l.load_item()

        contacts_array = item.get('Contacts_Array')
        if contacts_array:
            print('-------------------')
            print(item.get('Company_Name'))
            print('-------------------')
            all_contacts = contacts_array.split('\n\n')
            for detail in all_contacts:
                item['Contact_Name'] = get_field(detail, 'Name:')
                item['Contact_Title'] = get_field(detail, 'Title')
                item['Contact_Direct_Line'] = get_field(detail, 'Direct Line')
                item['Contact_Mobile_Phone'] = get_field(detail, 'Mobile Phone')
                item['Contact_Email'] = get_field(detail, 'Email')
                item['Contact_Skype'] = get_field(detail, 'Skype')
                yield item
        else:
            yield item
