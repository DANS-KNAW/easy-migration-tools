# given a doi, retrieve the uuid and subsequently the files from the bag-store

import argparse
import csv
import logging
import sys

import requests
from xml.dom import minidom
from easymigration.batch_processing import batch_process
from easymigration.config import init
from easymigration.pids_handling import non_empty_lines


def find_files(doi, dark_archive, csv_writer):
    # TODO continue batch if not found
    uuid = find_uuid(doi, dark_archive["index_url"])
    logging.debug(f"DOI = {doi}; UUID={uuid}")
    if uuid:
        files_xml = get_files_xml(uuid, dark_archive["store_url"])
        if (files_xml):
            parse_files_xml(doi, files_xml, csv_writer)


def find_uuid(doi, bag_index_url):
    # locate in bag-index
    response = requests.get(f"{bag_index_url}/search", params={"doi": doi})
    if response.status_code == 404:
        logging.error(f"${doi} not available: {response.status_code}")
        return ""
    elif response.status_code != 200:
        raise Exception(f"${doi}: ${response.status_code}")
    return response.json()["result"][0]["bag-info"]["bag-id"]


def get_files_xml(uuid, bag_store_url):
    response = requests.get(f"{bag_store_url}/bags/{uuid}/metadata/files.xml")
    if response.status_code == 410:
        logging.error(f"Files for {uuid} not available: {response.status_code}")
        return ""
    elif response.status_code != 200:
        raise Exception(f"${uuid}: ${response.status_code}")
    else:
        return response.text


def parse_files_xml(doi, files_xml, csv_writer):
    file_items = minidom.parseString(files_xml).getElementsByTagName("file")
    for elem in file_items:
        access = elem.getElementsByTagName("accessibleToRights")
        access_text = ""
        if access is not None and len(access) == 1:
            access_text = access[0].firstChild.nodeValue
        row = {"doi": doi, "path": elem.attributes["filepath"].value, "accessCategory": access_text}
        csv_writer.writerow(row)


def main():
    config = init()
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="For each doi, list the files in the bag-store"
    )
    parser.add_argument("-d", "--doi", dest="doi",
                        help="Pid of a single dataset for which to find the files. "
                             "When omitted, DOIs are read from stdin.")
    args = parser.parse_args()

    dark_archive = config["dark_archive"]

    fieldnames = {"doi", "path", "accessCategory"}
    csv_writer = csv.DictWriter(sys.stdout, delimiter=",", fieldnames=fieldnames)
    csv_writer.writeheader()

    if args.doi is not None:
        find_files(args.doi, dark_archive, csv_writer)
    else:
        dois = non_empty_lines(sys.stdin.read())
        batch_process(dois,
                      lambda doi: find_files(doi, dark_archive, csv_writer))


if __name__ == "__main__":
    main()
