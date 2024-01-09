import argparse
import logging
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom


ns = {'sforce': 'http://soap.sforce.com/2006/04/metadata'}
logging.basicConfig(format='%(message)s', level=logging.DEBUG)


def parse_args():
    """ Function to parse command line arguments."""
    parser = argparse.ArgumentParser(description='A script to create custom labels files.')
    parser.add_argument('-f', '--file',
                        default='force-app/main/default/labels/CustomLabels.labels-meta.xml')
    args = parser.parse_args()
    return args


def create_xml_file(label, parent_directory, tag, full_name):
    """Create a new XML file for a given element."""
    output_filename = f'{parent_directory}/{full_name}.label-meta.xml'

    # Remove the namespace prefix from the element tags
    for element in label.iter():
        if '}' in element.tag:
            element.tag = element.tag.split('}')[1]

    xml_header = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content = ET.tostring(label, encoding='utf-8').decode('utf-8')
    dom = minidom.parseString(xml_content)
    formatted_xml = dom.toprettyxml(indent='    ')

    # Remove extra new lines
    formatted_xml = '\n'.join(line for line in formatted_xml.split('\n') if line.strip())

    # Remove existing XML declaration
    formatted_xml = '\n'.join(line for line in formatted_xml.split('\n') if not line.strip().startswith('<?xml'))

    with open(output_filename, 'wb') as file:
        file.write(xml_header.encode('utf-8'))
        file.write(formatted_xml.encode('utf-8'))

    logging.info('Saved %s element content to %s', tag, output_filename)


def extract_full_name(label):
    """Extract the 'fullName' attribute from a label."""
    full_name_element = label.find('sforce:fullName', ns)
    if full_name_element is not None:
        return full_name_element.text
    return None


def separate_labels(xml_file_path):
    """Separate labels into their own files."""
    parent_directory = os.path.dirname(xml_file_path)

    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
    except FileNotFoundError:
        logging.info("Error: XML file '%s' not found.", xml_file_path)
        return
    except ET.ParseError:
        logging.info("Error: Unable to parse the XML file.")
        return

    # Extract all unique XML tags dynamically
    xml_tags = {elem.tag for elem in root.iter() if '}' in elem.tag}

    # Iterate through the dynamically extracted XML tags
    for tag in xml_tags:
        for label in root.findall(tag):
            full_name = extract_full_name(label)
            if full_name:
                create_xml_file(label, parent_directory, tag, full_name)
            else:
                logging.info('Skipping %s element without fullName', tag)


def main(label_file):
    """Main function."""
    separate_labels(label_file)


if __name__ == '__main__':
    inputs = parse_args()
    main(inputs.file)
