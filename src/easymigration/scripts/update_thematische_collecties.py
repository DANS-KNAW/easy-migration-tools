import argparse
import csv
import logging
import re
import sys
from urllib.parse import unquote
from xml.dom import minidom

import requests
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth

from easymigration.config import init


NS_EAS = "http://easy.dans.knaw.nl/easy/easymetadata/eas/"


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
                    if jumpoff_id == "":
                        row["members"] += members_from_relations(dataset_id, base_url)
                    else:
                        row["members"] += members_from_jumpoff(jumpoff_id, base_url)
                except Exception as e:
                    logging.error(f"{e} PROCESSING {row}")
        csv_writer.writerow(row)


def members_from_relations(dataset_id, base_url):
    logging.debug(f"no jumpoff, trying EMD of {dataset_id}")
    emd = get_data_stream(dataset_id, "EMD", base_url)
    members = []
    if emd.status_code != 200:
        logging.error(f"could not read EMD {dataset_id} {emd.status_code}")
    else:
        relations = minidom.parseString(emd.content).getElementsByTagNameNS(NS_EAS, "relation")
        members = resolve(map(extract_subject_link, filter(has_emphasis, relations)), dataset_id)
    return ",".join(members)


def extract_subject_link(relation):
    return relation.getElementsByTagNameNS(NS_EAS, "subject-link")[0].firstChild.nodeValue


def has_emphasis(relation):
    return relation.getAttributeNS(NS_EAS, "emphasis") == "true"


def members_from_jumpoff(jumpoff_id, base_url):
    logging.debug(f"reading HTML_MU {jumpoff_id}")
    mu = get_data_stream(jumpoff_id, "HTML_MU", base_url)
    if mu.status_code == 404:
        logging.debug(f"reading TXT_MU {jumpoff_id}")
        mu = get_data_stream(jumpoff_id, "TXT_MU", base_url)
    dataset_ids = []
    if 200 != mu.status_code:
        logging.error(f"could not read jumpoff {jumpoff_id} {mu.status_code}")
    else:
        soup = BeautifulSoup(mu.text, "html.parser")
        dataset_ids = resolve(map(extract_href, soup.findAll("a")), jumpoff_id)
    return ",".join(dataset_ids).replace("[]", "\"")


def extract_href(node):
    return unquote(node.attrs.get("href"))


def get_jumpoff_id(dataset_id, risearch_url, auth):
    params = dict()
    params["query"] = "PREFIX dans: <http://dans.knaw.nl/ontologies/relations#> " \
                      "SELECT ?s WHERE " \
                      "{?s dans:isJumpoffPageFor <info:fedora/" + dataset_id + "> . }"
    params["lang"] = "sparql"
    params["type"] = "tuples"
    params["format"] = "CSV"

    response = requests.get(risearch_url, params=params, auth=auth)
    if response.status_code != 200:
        raise Exception(f"Could not find jumpoff-id for {dataset_id} response: {response} {response.content}")
    elif "dans-jumpoff" not in response.text:
        return ""
    else:
        return re.findall(r'dans-jumpoff:[0-9]+', response.text)[0]


def get_data_stream(object_id, stream, base_url):
    url = f"{base_url}/objects/{object_id}/datastreams/{stream}/content"
    response = requests.get(url)
    logging.debug(f"status code: {response.status_code} url: {url}")
    return response


def resolve(urls, object_id):
    dataset_ids = set()
    for href in urls:
        logging.debug(f"resolving {href} in {object_id}")
        if "easy-dataset:" in href:
            dataset_ids.add(re.findall(r'easy-dataset:[0-9]+', href)[0])
            continue
        if re.search("(?s).*(doi.org.*dans|urn:nbn:nl:ui:13-).*", href) is None:
            logging.debug(f"Not a dataset link {href} in {object_id}")
            continue
        replaced_href = re.sub("http://dx.doi.org", "https://doi.org", href)
        try:
            response = requests.get(replaced_href, allow_redirects=False, timeout=0.5)
        except Exception as e:
            logging.error(f"Could not resolve {replaced_href} in {object_id}: {e}")
            continue
        if response.status_code != 302:
            logging.error(
                f"Expected status code 302 but got {response.status_code} for {replaced_href} in {object_id}")
            continue
        location = unquote(response.headers.get("location"))
        if "easy-dataset:" not in location:
            logging.error(f"Need 'easy-dataset:NNN' but {replaced_href} in {object_id} resolved to {location}")
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
                    'If the dataset has no jumpoff, relations with emphasis are collected from the EMD. '
                    'The first line of the CSV is assumed to be a header and is copied as-is.',
        epilog='Example: update_thematische_collecties.py < OldThemCol.csv > NewThemCol.csv'
    ).parse_args()
    update_thematische_collecties(config["fedora"])


if __name__ == '__main__':
    main()
