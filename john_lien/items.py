# -*- coding: utf-8 -*-

import scrapy
import re
from w3lib.html import replace_escape_chars
from scrapy.loader.processors import Compose, MapCompose, TakeFirst, Identity


def clear_whitespaces(val):
    return replace_escape_chars(val.strip())


def get_name(val):
    items = val.split('\n')
    name = [target for target in items if 'Name:' in target]
    if name:
        res = re.sub(r'^Name:[^\w]+', '', name[0])
    else:
        # no field in val
        res = ''
    return res


def get_title(val):
    items = val.split('\n')
    name = [target for target in items if 'Title' in target]
    if name:
        res = re.sub(r'^Title[^\w]+', '', name[0])
    else:
        # no field in val
        res = ''
    return res


def get_email(val):
    items = val.split('\n')
    name = [target for target in items if 'Email' in target]
    if name:
        res = re.sub(r'^Email[^\w]+', '', name[0])
    else:
        # no field in val
        res = ''
    return res


def get_direct_line(val):
    items = val.split('\n')
    name = [target for target in items if 'Direct Line' in target]
    if name:
        res = re.sub(r'^Direct Line[^\w]+', '', name[0])
    else:
        # no field in val
        res = ''
    return res


def get_skype(val):
    items = val.split('\n')
    name = [target for target in items if 'Skype' in target]
    if name:
        res = re.sub(r'^Skype[^\w]+', '', name[0])
    else:
        # no field in val
        res = ''
    return res


class JohnLienItem(scrapy.Item):
    Company_ID = scrapy.Field(
        input_processor=MapCompose(clear_whitespaces, lambda x: x.replace('ID: ', ''))
    )
    Company_Name = scrapy.Field()
    Head_office_or_Branch_office = scrapy.Field(
        input_processor=MapCompose(clear_whitespaces, lambda x: x.lstrip('(').rstrip(')'))
    )
    Network_Memberships = scrapy.Field(
        input_processor=Compose(
            MapCompose(lambda x: x.replace('to View ', '')),
            lambda x: ', '.join(x),
        )
    )
    Company_description = scrapy.Field(
        input_processor=MapCompose(lambda x: x.strip())
    )
    Company_address_line_1 = scrapy.Field(
        input_processor=Compose(
            MapCompose(lambda x: x.strip()),
            lambda x: '\n'.join(x),
        )
    )
    Company_address_line_2 = scrapy.Field()
    Company_city = scrapy.Field()
    Company_state_or_province = scrapy.Field()
    Company_postal_code = scrapy.Field()
    Company_phone = scrapy.Field(
        input_processor=Compose(
            MapCompose(
                lambda x: x.replace('Toll Free: ', '').replace('(Main Line)', ''),
                lambda x: x.split(' / ') if '/' in x else x.split(', '),
            ),
            lambda x: '\n'.join(x),
        )
    )
    Company_fax = scrapy.Field(
        input_processor=Compose(
            MapCompose(
                # lambda x: x.replace('Toll Free: ', '').replace('(Main Line)', ''),
                lambda x: x.split(' / ') if '/' in x else x.split(', '),
            ),
            lambda x: '\n'.join(x),
        )
    )
    Company_emergency = scrapy.Field(
        input_processor=MapCompose(
            lambda x: x.replace(',', ''),
            lambda x: x.strip(),
        ),
        output_processor=Compose(
            lambda x: '\n'.join(x)
        )
    )
    Website_URL = scrapy.Field()
    Company_email = scrapy.Field(
        input_processor=MapCompose(
            lambda x: x.replace(',', ''),
            lambda x: x.strip(),
        ),
        output_processor=Compose(
            lambda x: '\n'.join(x)
        )
    )
    Contacts_Array = scrapy.Field(
        input_processor=Compose(
            MapCompose(
                lambda x: '\n'.join(x),
            ),
            lambda x: '\n\n'.join(x),
        )
    )
    Contact_Name = scrapy.Field(
        input_processor=Compose(
            lambda x: x[0].split('\n\n')[0],
            get_name,
            # lambda x: x.split('\n')[0],
        ),
    )
    Contact_Title = scrapy.Field(
        input_processor=Compose(
            lambda x: x[0].split('\n\n')[0],
            get_title,
        ),
    )
    Contact_Direct_Line = scrapy.Field(
        input_processor=Compose(
            lambda x: x[0].split('\n\n')[0],
            get_direct_line,
        ),
    )
    Contact_Mobile_Phone = scrapy.Field()
    Contact_Email = scrapy.Field(
        input_processor=Compose(
            lambda x: x[0].split('\n\n')[0],
            get_email,
        ),
    )
    Contact_Skype = scrapy.Field(
        input_processor=Compose(
            lambda x: x[0].split('\n\n')[0],
            get_skype,
        ),
    )
    wcaworld_url = scrapy.Field()
