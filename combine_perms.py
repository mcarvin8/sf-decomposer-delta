import argparse
import logging
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom


logging.basicConfig(format='%(message)s', level=logging.DEBUG)


def parse_args():
    """Function to parse command line arguments."""
    parser = argparse.ArgumentParser(description='A script to create permission sets.')
    parser.add_argument('-o', '--output', default='force-app/main/default/permissionsets')
    parser.add_argument('-m', '--manifest', default=False, action='store_true')
    parser.add_argument('-p', '--perms')
    args = parser.parse_args()
    return args


def read_individual_xmls(perm_directory, manifest, package_perms):
    """Read each XML file."""
    individual_xmls = {}

    for filename in os.listdir(perm_directory):
        if filename.endswith('.xml') and not filename.endswith('.permissionset-meta.xml'):
            parent_perm_name = filename.split('.')[0]
            if not manifest or (manifest and parent_perm_name in package_perms):
                individual_xmls.setdefault(parent_perm_name, [])
                tree = ET.parse(os.path.join(perm_directory, filename))
                root = tree.getroot()
                individual_xmls[parent_perm_name].append(root)

    return individual_xmls


def has_subelements(element):
    """Check if an XML element has sub-elements."""
    return any(element.iter())


def merge_xml_content(individual_xmls):
    """Merge XMLs for each object."""
    merged_xmls = {}
    for parent_perm_name, individual_roots in individual_xmls.items():
        parent_perm_root = ET.Element('PermissionSet', xmlns="http://soap.sforce.com/2006/04/metadata")

        for matching_root in individual_roots:
            tag = matching_root.tag
            # Check if the root has sub-elements
            if has_subelements(matching_root):
                # Create a new XML element for each sub-element
                child_element = ET.Element(tag)
                parent_perm_root.append(child_element)
                child_element.extend(matching_root)
            else:
                # Extract text content from single-element XML and append to the parent
                text_content = matching_root.text
                if text_content:
                    child_element = ET.Element(tag)
                    child_element.text = text_content
                    parent_perm_root.append(child_element)

        merged_xmls[parent_perm_name] = parent_perm_root

    return merged_xmls


def format_and_write_xmls(merged_xmls, perm_directory):
    """Create the final XMLs."""
    for parent_perm_name, parent_perm_root in merged_xmls.items():
        parent_xml_str = ET.tostring(parent_perm_root, encoding='utf-8').decode('utf-8')
        formatted_xml = minidom.parseString(parent_xml_str).toprettyxml(indent="    ")

        # Remove extra new lines
        formatted_xml = '\n'.join(line for line in formatted_xml.split('\n') if line.strip())

        # Remove existing XML declaration
        formatted_xml = '\n'.join(line for line in formatted_xml.split('\n') if not line.strip().startswith('<?xml'))

        parent_perm_filename = os.path.join(perm_directory, f'{parent_perm_name}.permissionset-meta.xml')
        with open(parent_perm_filename, 'wb') as file:
            # Include encoding information in the XML header
            file.write(f'<?xml version="1.0" encoding="UTF-8"?>\n{formatted_xml}'.encode('utf-8'))


def combine_perms(perm_directory, manifest, package_perms):
    """Combine the perm sets for deployments."""
    individual_xmls = read_individual_xmls(perm_directory, manifest, package_perms)
    merged_xmls = merge_xml_content(individual_xmls)
    format_and_write_xmls(merged_xmls, perm_directory)

    if manifest:
        logging.info("The permission sets for %s have been compiled for deployments.",
                    ', '.join(map(str, package_perms)))
    else:
        logging.info('The permission sets have been compiled for deployments.')


def main(output_directory, manifest, perms):
    """Main function."""
    combine_perms(output_directory, manifest, perms)


if __name__ == '__main__':
    inputs = parse_args()
    main(inputs.output, inputs.manifest,
         inputs.perms)
