import argparse
import csv
import logging
import re
import sys
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth

from easymigration.config import init


def update_thematische_collecties(fedora_config):
    """
     Copies a Thematische-Collecties.csv from stdin to stdout.
     Assumed columns: -,EASY-dataset-id,-,-,members
     Empty members columns are filled by crawling jump off pages.
     The first line is copied as is.

        Example: update_thematische_collecties.py  < OldThemCol.csv > NewThemCol.csv
    """

    auth = HTTPBasicAuth(fedora_config["user_name"], fedora_config["password"])
    base_url = fedora_config["base_url"]
    risearch_url = f"{base_url}/risearch"

    csv_reader = csv.DictReader(sys.stdin, delimiter=',')
    csv_writer = csv.DictWriter(sys.stdout, delimiter=',', fieldnames=csv_reader.fieldnames)
    csv_writer.writeheader()

    for row in csv_reader:
        if not row["members"]:
            logging.debug(row)
            for dataset_id in row["EASY-dataset-id"].split(","):
                try:
                    jumpoff_id = get_jumpoff_id(dataset_id, risearch_url, auth)
                    row["members"] += get_members(jumpoff_id, base_url)
                except Exception as e:
                    logging.error(f"{e} PROCESSING {row}")
        csv_writer.writerow(row)


def get_members(jumpoff_id, base_url):
    mu = get_jumpoff_content(jumpoff_id, "HTML_MU", base_url)
    logging.debug(f"{jumpoff_id}")
    if mu.status_code == 404:
        logging.debug(f"{jumpoff_id}")
        mu = get_jumpoff_content(jumpoff_id, "TXT_MU", base_url)
    if 200 == mu.status_code:
        dataset_ids = parse_jumpoff(mu.text, jumpoff_id)
        return ",".join(dataset_ids).replace("[]", "\"")
    else:
        logging.error(f"jumpoff not found {jumpoff_id} {mu.status_code}")
        return ""


def get_jumpoff_id(dataset_id, risearch_url, auth):
    params = dict()
    params["query"] = "PREFIX dans: <http://dans.knaw.nl/ontologies/relations#> " \
                      "SELECT ?s WHERE " \
                      "{?s dans:isJumpoffPageFor <info:fedora/" + dataset_id + "> . }"
    params["lang"] = "sparql"
    params["type"] = "tuples"
    params["format"] = "CSV"

    response = requests.get(risearch_url, params=params, auth=auth)
    if response.status_code != 200 or "dans-jumpoff" not in response.text:
        raise Exception(f"Could not find jumpoff-id for {dataset_id} response: {response}")
    return re.findall(r'dans-jumpoff:[0-9]+', response.text)[0]


def get_jumpoff_content(jumpoff_id, response_format, base_url):
    url = f"{base_url}/objects/{jumpoff_id}/datastreams/{response_format}/content"
    response = requests.get(url)
    logging.debug(f"status code: {response.status_code} url: {url}")
    return response


def parse_jumpoff(jumpoff_page, jumpoff_id):
    # members: "easy-dataset:34099, easy-dataset:57698"
    soup = BeautifulSoup(jumpoff_page, "html.parser")
    dataset_ids = set()
    for a_tag in soup.findAll("a"):
        href = unquote(a_tag.attrs.get("href"))
        logging.debug(f"resolving {href} in {jumpoff_id}")
        if "easy-dataset:" in href:
            dataset_ids.add(re.findall(r'easy-dataset:[0-9]+', href)[0])
            continue
        if re.search("(?s).*(doi.org.*dans|urn:nbn:nl:ui:13-).*", href) is None:
            logging.debug(f"Not a dataset link {href} in {jumpoff_id}")
            continue
        replaced_href = re.sub("http://dx.doi.org", "https://doi.org", href)
        try:
            response = requests.get(replaced_href, allow_redirects=False, timeout=0.5)
        except Exception as e:
            logging.error(f"Could not resolve {replaced_href} in {jumpoff_id}: {e}")
            continue
        if response.status_code != 302:
            logging.error(f"Expected status code 302 but got {response.status_code} for {replaced_href} in {jumpoff_id}")
            continue
        location = unquote(response.headers.get("location"))
        if "easy-dataset:" not in location:
            logging.error(f"Need 'easy-dataset:NNN' but {replaced_href} in {jumpoff_id} resolved to {location}")
            continue
        dataset_ids.add(re.findall(r'easy-dataset:[0-9]+', location)[0])
    return dataset_ids


def main():
    config = init()
    argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Copies an easy-convert-bag-to-deposit/src/main/assembly/dist/cfg/ThemathischeCollecties.csv '
                    'from stdin to stdout. '
                    'Empty member fields will be updated by collecting links from the jumpoff page of the dataset. '
                    'The first line of the CSV is assumed to be a header and is copied as-is.',
        epilog='Example: update_thematische_collecties.py < OldThemCol.csv > NewThemCol.csv'
    ).parse_args()
    update_thematische_collecties(config["fedora"])


if __name__ == '__main__':
    main()
