import argparse
import logging
import sys
import xml.etree.ElementTree as ET

import combine_labels
import combine_perms
import combine_workflows

LABEL_TYPE = ['CustomLabel']
WORKFLOW_TYPE = ['Workflow']
PERM_TYPE = ['PermissionSet']

logging.basicConfig(level=logging.DEBUG, format='%(message)s')
ns = {'sforce': 'http://soap.sforce.com/2006/04/metadata'}


def parse_args():
    """Function to parse required arguments."""
    parser = argparse.ArgumentParser(description='A script to scan the package for specific types.')
    parser.add_argument('-m', '--manifest', default='./manifest/package.xml')
    args = parser.parse_args()
    return args


def set_dictionary_members(package_members, package_dict):
    """Add metadata members in package to a dictionary."""
    for member in package_members:
        package_dict[member] = True
    return package_dict


def scan_package_metadata(package_path):
    """Scan the package and run the applicable scripts."""
    try:
        root = ET.parse(package_path).getroot()
    except ET.ParseError:
        logging.info('Unable to parse %s. Confirm XML is formatted correctly before re-trying.', package_path)
        sys.exit(1)

    package_labels = {}
    package_workflows = {}
    package_perms = {}

    for metadata_type in root.findall('sforce:types', ns):
        metadata_name = (metadata_type.find('sforce:name', ns)).text
        metadata_members = metadata_type.findall('sforce:members', ns)
        if metadata_name in LABEL_TYPE:
            members = [member.text for member in metadata_members]
            package_labels = set_dictionary_members(members, package_labels)
        if metadata_name in WORKFLOW_TYPE:
            members = [member.text for member in metadata_members]
            package_workflows = set_dictionary_members(members, package_workflows)
        if metadata_name in PERM_TYPE:
            members = [member.text for member in metadata_members]
            package_perms = set_dictionary_members(members, package_perms)

    if package_labels:
        combine_labels.combine_labels('force-app/main/default/labels',
                            'force-app/main/default/labels/CustomLabels.labels-meta.xml', True, package_labels)
    if package_workflows:
        combine_workflows.combine_workflows('force-app/main/default/workflows', True, package_workflows)
    if package_perms:
        combine_perms.combine_perms('force-app/main/default/permissionsets', True, package_perms)


def main(manifest):
    """Main function."""
    scan_package_metadata(manifest)


if __name__ == '__main__':
    inputs = parse_args()
    main(inputs.manifest)
