import argparse
import logging
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom

logging.basicConfig(format='%(message)s', level=logging.DEBUG)


def parse_args():
    """Function to parse command line arguments."""
    parser = argparse.ArgumentParser(description='A script to combine labels.')
    parser.add_argument('-f', '--file',
                        default='force-app/main/default/labels/CustomLabels.labels-meta.xml')
    parser.add_argument('-d', '--directory', default='force-app/main/default/labels')
    parser.add_argument('-m', '--manifest', default=False, action='store_true')
    parser.add_argument('-l', '--labels')
    args = parser.parse_args()
    return args


def read_individual_xmls(label_directory, manifest, package_labels):
    """Read each XML file."""
    individual_xmls = []
    for file_path in os.listdir(label_directory):
        # Get file name without meta extension
        file_name, _ = os.path.splitext(os.path.basename(file_path))
        file_name = file_name.split('.')[0]
        if (not manifest or (manifest and file_name in package_labels)) and file_path.endswith('.xml') and not file_path.endswith('.labels-meta.xml'):
            tree = ET.parse(os.path.join(label_directory, file_path))
            root = tree.getroot()
            individual_xmls.append(root)

    return individual_xmls


def merge_xml_content(individual_roots):
    """Merge XMLs for all objects."""
    combined_root = ET.Element('CustomLabels', xmlns="http://soap.sforce.com/2006/04/metadata")

    for root in individual_roots:
        child_element = ET.Element(root.tag)
        combined_root.append(child_element)
        child_element.extend(root)

    return combined_root


def format_and_write_xml(combined_root, label_file):
    """Create the final XML."""
    xml_header = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_str = ET.tostring(combined_root, encoding='utf-8').decode('utf-8')
    formatted_xml = minidom.parseString(xml_str).toprettyxml(indent="    ")

    # Remove extra new lines
    formatted_xml = '\n'.join(line for line in formatted_xml.split('\n') if line.strip())

    # Remove existing XML declaration
    formatted_xml = '\n'.join(line for line in formatted_xml.split('\n') if not line.strip().startswith('<?xml'))

    with open(label_file, 'wb') as file:
        file.write(xml_header.encode('utf-8'))
        file.write(formatted_xml.encode('utf-8'))


def combine_labels(label_directory, label_file, manifest, package_labels):
    """Combine the labels for deployments."""
    individual_roots = read_individual_xmls(label_directory, manifest, package_labels)
    combined_root = merge_xml_content(individual_roots)
    format_and_write_xml(combined_root, label_file)

    if manifest:
        logging.info("The custom labels for %s have been compiled for deployments.",
                    ', '.join(map(str, package_labels)))
    else:
        logging.info('The custom labels have been compiled for deployments.')


def main(directory, label_file, manifest, labels):
    """Main function."""
    combine_labels(directory, label_file, manifest, labels)


if __name__ == '__main__':
    inputs = parse_args()
    main(inputs.directory, inputs.file,
         inputs.manifest, inputs.labels)
