# given a doi, retrieve the uuid and subsequently the files from the bag-store

import argparse
import csv
import logging
import sys

import requests
from xml.dom import minidom
from easymigration.batch_processing import batch_process
from easymigration.config import init
from easymigration.pids_handling import load_pids


def find_files(doi, dark_url, csv_writer):
    uuid = find_uuid(doi, dark_url)
    files_xml = get_files_xml(uuid, dark_url)
    parse_files_xml(doi, files_xml, csv_writer)


def find_uuid(doi, bag_index_url):
    #locate in bag-index
    try:
        params = {'doi': doi}
        response = requests.put(
            bag_index_url + '/bag-index/search',
            params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException as re:
        print("RequestException: ", re)
        raise
    resp_data = response.json()['result'][0]["bag-info"]["urn"]
    return resp_data


def get_files_xml(urn, bag_store_url):
    try:
        url = "{}/bag-store/bags/{}/metadata/files.xml".format(bag_store_url, urn)
        logging.debug(url)
        response = requests.put(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as re:
        print("RequestException: ", re)
        raise
    return response


def parse_files_xml(doi, files_xml, csv_writer):
    mydoc = minidom.parse(files_xml)

    file_items = mydoc.getElementsByTagName('file')
    for elem in file_items:
        access = elem.getElementsByTagName('accessibleToRights')
        access_text = ''
        if access is not None and len(access) == 1:
            access_text = access[0].firstChild.nodeValue
        row = {"doi": doi, "path": elem.attributes['filepath'].value, "accessCategory": access_text}
        csv_writer.writerow(row)


def main():
    config = init()
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='For each doi, list the files in the bag-store'
    )
    pid_or_file = parser.add_mutually_exclusive_group()
    pid_or_file.add_argument('-p', '--pid', dest='pid', help='Pid of a single dataset for which to find the files')
    pid_or_file.add_argument('-d', '--datasets', dest='pid_file', help='The input file with the dataset pids')
    args = parser.parse_args()

    dark_url = config['dark_archive']['base_url']

    fieldnames = {"doi", "path", "accessCategory"}
    csv_writer = csv.DictWriter(sys.stdout, delimiter=',', fieldnames=fieldnames)
    csv_writer.writeheader()

    if args.pid is not None:
        find_files(args.pid, dark_url, csv_writer)

    if args.pid_file is not None:
        pids = load_pids(args.pid_file)
        batch_process(pids,
                      lambda pid: find_files(pid, dark_url, csv_writer))


if __name__ == '__main__':
    main()