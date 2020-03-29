#!/usr/bin/env python3
import os
import singer
import requests
from datetime import datetime
from singer import utils, metadata
from singer.catalog import Catalog, CatalogEntry
from singer.schema import Schema
from tap_bold.schema import get_schemas, STREAMS


BASE_URL = 'https://ro.boldapps.net/api/'
REQUIRED_CONFIG_KEYS = ["BOLD_API_KEY", "BOLD_APP_HANDLE", "BOLD_SHOP_DOMAIN", "START_DATE"]
LOGGER = singer.get_logger()


def get_abs_path(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


def discover():
    schemas, field_metadata = get_schemas()
    catalog = Catalog([])

    for stream_name, schema_dict in schemas.items():
        schema = Schema.from_dict(schema_dict)
        mdata = field_metadata[stream_name]

        catalog.streams.append(CatalogEntry(
            stream=stream_name,
            tap_stream_id=stream_name,
            key_properties=STREAMS[stream_name]['key_properties'],
            schema=schema,
            metadata=mdata
        ))

    return catalog


def get_third_party_token(api_key, app_handle, shop_domain):
    response = requests.get(
        BASE_URL + 'auth/third_party_token',
        params={'shop': shop_domain, 'handle': app_handle},
        headers={'Content-Type': 'application/json', 'BOLD-Authorization': api_key},
    )
    return response.json()


def tap_data(config, stream):
    """ Throw if it's not subscriptions stream """
    if stream.tap_stream_id != 'subscriptions':
        raise Exception('This tap only works with subscriptions stream')

    tokenResponse = get_third_party_token(
        api_key=config['BOLD_API_KEY'],
        app_handle=config['BOLD_APP_HANDLE'],
        shop_domain=config['BOLD_SHOP_DOMAIN']
    )
    s = requests.Session()
    s.headers.update({
        'Content-Type': 'application/json',
        'BOLD-Authorization': 'Bearer ' + tokenResponse['token']
    })

    page = 1
    rows = []
    while True:
        subRes = s.get(BASE_URL + 'third_party/subscriptions?shop=' + config['BOLD_SHOP_DOMAIN'] +
              '&purchase_date_min=' + config['START_DATE'] + '&page=' + str(page) + '&limit=50')
        subJson = subRes.json()
        newSubs = subJson['subscriptions']
        page += 1
        rows.extend(newSubs)
        if len(newSubs) < 50:
            break
    return rows


BOLD_DATE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
BOLD_DATE_FORMAT = '%Y-%m-%d'
ISO_DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


def bold_strptime(date_str, fmt):
    return datetime.strptime(date_str, fmt)

def transform_product(product):
    """
    #/order_products/0/last_updated: #: no subschema matched out of the total 2 subschemas
    #/order_products/0/last_updated: expected: null, found: String
    #/order_products/0/last_updated: [2020-03-11 08:11:30] is not a valid date-time. Expected [yyyy-MM-dd'T'HH:mm:ssZ, yyyy-MM-dd'T'HH:mm:ss.[0-9]{1,9}Z]
    """
    product['last_updated'] = bold_strptime(product['last_updated'], BOLD_DATE_TIME_FORMAT).strftime(ISO_DATE_TIME_FORMAT)
    """    
    #/order_products/0/shopify_new_price: #: no subschema matched out of the total 2 subschemas
    #/order_products/0/shopify_new_price: expected: null, found: String
    #/order_products/0/shopify_new_price: expected type: Number, found: String
    """
    if product['shopify_new_price'] is not None:
        product['shopify_new_price'] = float(product['shopify_new_price'])
    """
    #/order_products/0/price: #: no subschema matched out of the total 2 subschemas
    #/order_products/0/price: expected: null, found: String
    #/order_products/0/price: expected type: Number, found: String
    """
    product['price'] = float(product['price'])
    """
    #/order_products/0/shopify_price: #: no subschema matched out of the total 2 subschemas
    #/order_products/0/shopify_price: expected: null, found: String
    #/order_products/0/shopify_price: expected type: Number, found: String
    """
    if product['shopify_price'] is not None:
        product['shopify_price'] = float(product['shopify_price'])

    return product


def transform_order_log_failed_transaction(transaction):
    transaction['transaction_date'] = bold_strptime(
        transaction['transaction_date'],
        BOLD_DATE_FORMAT
    ).strftime(ISO_DATE_TIME_FORMAT)

    if transaction['shipping'] is not None:
        transaction['shipping'] = float(transaction['shipping'])

    if transaction['price'] is not None:
        transaction['price'] = float(transaction['price'])

    if transaction['tax'] is not None:
        transaction['tax'] = float(transaction['tax'])

    del transaction['shop_app_id']
    del transaction['param']
    del transaction['error']
    del transaction['email_sent']
    del transaction['archived']
    del transaction['share_shipping']

    return transaction


def transform(row):
    if row['delete_date'] is not None:
        row['delete_date'] = bold_strptime(row['delete_date'], BOLD_DATE_FORMAT).strftime(ISO_DATE_TIME_FORMAT)

    row['last_updated'] = bold_strptime(row['last_updated'], BOLD_DATE_TIME_FORMAT).strftime(ISO_DATE_TIME_FORMAT)
    row['currency_exchange_rate'] = float(row['currency_exchange_rate'])
    row['purchase_date'] = bold_strptime(row['purchase_date'], BOLD_DATE_FORMAT).strftime(ISO_DATE_TIME_FORMAT)

    if row['next_ship_date'] is not None:
        row['next_ship_date'] = bold_strptime(row['next_ship_date'], BOLD_DATE_FORMAT).strftime(ISO_DATE_TIME_FORMAT)

    if row['order_products'] is not None:
        row['order_products'] = list(map(transform_product, row['order_products']))

    if row['next_active_ship_date'] is not None:
        row['next_active_ship_date'] = bold_strptime(
            row['next_active_ship_date'],
            BOLD_DATE_FORMAT
        ).strftime(ISO_DATE_TIME_FORMAT)

    if row['last_ship_date'] is not None:
        row['last_ship_date'] = bold_strptime(row['last_ship_date'], BOLD_DATE_FORMAT).strftime(ISO_DATE_TIME_FORMAT)

    if row['order_fixed_recurrences'] is not None:
        row['total_recurrences'] = row['order_fixed_recurrences']['total_recurrences']
        row['recurrence_count'] = row['order_fixed_recurrences']['recurrence_count']
        row['one_charge_only'] = row['order_fixed_recurrences']['one_charge_only']
        row['recurr_after_limit'] = row['order_fixed_recurrences']['recurr_after_limit']

    if row['order_log_failed_transactions'] is not None:
        row['order_log_failed_transactions'] = list(map(transform_order_log_failed_transaction, row['order_log_failed_transactions']))

    del row['order_fixed_recurrences']
    del row['order_shipping_rate_exceptions']
    del row['order_exceptions']
    return row


def sync(config, state, catalog):
    """ Sync data from tap source """
    # Loop over selected streams in catalog
    for stream in catalog.get_selected_streams(state):
        LOGGER.info("Syncing stream:" + stream.tap_stream_id)

        bookmark_column = stream.replication_key
        is_sorted = False

        singer.write_schema(
            stream_name=stream.tap_stream_id,
            schema=stream.schema.to_dict(),
            key_properties=stream.key_properties,
        )

        max_bookmark = None
        for row in tap_data(config=config, stream=stream):
            transformed = transform(row)
            singer.write_records(stream.tap_stream_id, [transformed])
            if bookmark_column:
                if is_sorted:
                    # update bookmark to latest value
                    singer.write_state({stream.tap_stream_id: row[bookmark_column]})
                else:
                    # if data unsorted, save max value until end of writes
                    max_bookmark = max(max_bookmark, row[bookmark_column])
        if bookmark_column and not is_sorted:
            singer.write_state({stream.tap_stream_id: max_bookmark})
    return


@utils.handle_top_exception(LOGGER)
def main():
    # Parse command line arguments
    args = utils.parse_args(REQUIRED_CONFIG_KEYS)

    # If discover flag was passed, run discovery mode and dump output to stdout
    if args.discover:
        catalog = discover()
        catalog.dump()
    # Otherwise run in sync mode
    else:
        if args.catalog:
            catalog = args.catalog
        else:
            catalog = discover()
        sync(args.config, args.state, catalog)


if __name__ == "__main__":
    main()
