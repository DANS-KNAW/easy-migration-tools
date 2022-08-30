import argparse
import csv
import logging
import re
import sys
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

from easymigration.config import init


def update_thematische_collecties(base_url):
    """
     Copies a Thematische-Collecties.csv from stdin to stdout.
     Assumed columns: -,EASY-dataset-id,-,-,members,jumpoff-id
     Empty members columns are filled by crawling jump of pages.
     jumpoff-id is for temporal testing purposes

        Example: update_thematische_collecties.py  < OldThemCol.csv > NewThemCol.csv
    """

    csv_reader = csv.reader(sys.stdin, delimiter=',')
    csv_writer = csv.writer(sys.stdout, delimiter=',')
    for row in csv_reader:
        # columns: name,EASY-dataset-id,type,comment,members
        row4 = row[4].strip()
        if not ("easy-dataset" in row4 or "members" in row4):
            # TODO replace row[5] by feeding row[1] to fedora risearch:
            #  PREFIX dans: <http://dans.knaw.nl/ontologies/relations#> SELECT ?s WHERE {?s dans:isJumpoffPageFor <info:fedora/easy-dataset:13> . }
            #  https://stackoverflow.com/questions/56727817/how-to-send-form-data-using-python-requests
            logging.debug("{} {} {}".format(row[1], row4, row[5]))
            try:
                row[4] = get_members(row[5], base_url)
            except Exception as e:
                logging.error("{} {}".format(row[1], e))
        csv_writer.writerow(row)


def get_members(jumpoff_id, base_url):
    mu = get_jumpoff(jumpoff_id, "HTML_MU", base_url)
    if mu.status_code == 404:
        mu = get_jumpoff(jumpoff_id, "TXT_MU", base_url)
    if 200 == mu.status_code:
        urls = parse_jumpoff(mu.text)
        return ",".join(urls).replace("[]", "\"")  # TODO replace each url with "easy-dataset:NNN"
    else:
        logging.error("jumpoff not found {} {}".format(jumpoff_id, mu.status_code))
        return ""


def get_jumpoff(jumpoff_id, response_format, base_url):
    req = "{}/fedora/objects/{}/datastreams/{}/content".format(base_url, jumpoff_id, response_format)
    response = requests.get(req)
    logging.debug("status code: {} req: {}".format(response.status_code, req))
    return response


def parse_jumpoff(jumpoff_page):
    # members: "easy-dataset:34099, easy-dataset:57698"
    soup = BeautifulSoup(jumpoff_page, "html.parser")
    urls = set()
    for a_tag in soup.findAll("a"):
        href = unquote(a_tag.attrs.get("href"))
        logging.debug("resolving {}".format(href))
        if "easy-dataset:" in href:
            urls.add(re.sub(r'.+/', '', href))
            continue
        if re.search("(?s).*(doi.org.*dans|urn:nbn:nl:ui:13-).*", href) is None:
            logging.debug("Not a dataset link {}".format(href))
            continue
        try:
            response = requests.get(href, allow_redirects=False, timeout=0.5)
        except Exception as e:
            logging.error("{} {}".format(href, e))
            continue
        if response.status_code != 302:
            logging.error("Not expected status code {} for {}".format(response.status_code, href))
            continue
        location = unquote(response.headers.get("location"))
        if not "easy-dataset:" in location:
            logging.error("Expecting 'easy-dataset:NNN' but {} resolved to {}".format(href, location))
            continue
        urls.add(re.sub(r'.+/', '', location))
    return urls


def main():
    config = init()
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Copies an easy-convert-bag-to-deposit/src/main/assembly/dist/cfg/ThemathischeCollecties.csv '
                    'from stdin to stdout. '
                    'Empty member fields will be updated by collecting links from the jumpoff page of the dataset. ',
        epilog='Example: update_thematische_collecties.py < OldThemCol.csv > NewThemCol.csv'
    )
    parser.add_argument('--host',
                        default='http://deasy.dans.knaw.nl:8080',
                        help='The host with a fedora DB, no trailing slash.')
    args = parser.parse_args()
    update_thematische_collecties(args.host)


if __name__ == '__main__':
    main()
