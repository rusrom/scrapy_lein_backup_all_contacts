# -*- coding: utf-8 -*-
import scrapy
import re

from john_lien.items import JohnLienItem
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose
from w3lib.html import replace_escape_chars


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
        res = re.sub(r'^{}[^\w]+'.format(field), '', name[0])
    else:
        # no field in val
        res = ''
    return res


class WcaworldSpider(scrapy.Spider):
    name = 'wcaworld'
    allowed_domains = ['wcaworld.com']
    start_urls = ['http://www.wcaworld.com/Directory?networkId=24&pageNumber=1&pageSize=100&allnet=yes&networkIds=1&networkIds=2&networkIds=3&networkIds=4&networkIds=61&networkIds=98&networkIds=108&networkIds=6&networkIds=5&networkIds=22&networkIds=13&networkIds=18&networkIds=15&networkIds=16&networkIds=105&networkIds=38&licenseIds=0&licenseIds=0&licenseIds=0&licenseIds=0&searchby=CountryCode&orderby=CountryCity&country=US&statecity=&city=&keyword=']

    def parse(self, response):
        links = response.xpath('//div[@id="directory_result"]//li/a[starts-with(@href, "/directory/member")]/@href')
        for link in links:
            yield response.follow(link, callback=self.parse_company)

        # Infinite scrolling
        infinit_scroll = response.xpath('//a[@href="#" and contains(., "CLICK HERE")]/@onmouseover').extract_first()
        if infinit_scroll:
            url_get_parameters = re.search(r"\('([^']+)'\)", infinit_scroll)

            if url_get_parameters:
                url_get_parameters = url_get_parameters.group(1)
                next_page = 'http://www.wcaworld.com/directory/next' + url_get_parameters
                yield scrapy.Request(next_page, callback=self.parse)

    def parse_company(self, response):
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
        l.add_value('Company_emergency', 'Need to login')
        l.add_value('Website_URL', table_with_data.xpath('./tr[contains(string(), "Website:")]/td[last()]/a/@href').get())
        l.add_value('Company_email', 'Need to login')

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

        # l.add_value('Contact_Name', l.get_collected_values('Contacts_Array'))
        # l.add_value('Contact_Title', l.get_collected_values('Contacts_Array'))
        # l.add_value('Contact_Direct_Line', l.get_collected_values('Contacts_Array'))
        # l.add_value('Contact_Email', l.get_collected_values('Contacts_Array'))
        # l.add_value('Contact_Skype', l.get_collected_values('Contacts_Array'))
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
                item['Contact_Email'] = get_field(detail, 'Email')
                item['Contact_Skype'] = get_field(detail, 'Skype')
                yield item
        else:
            yield item
