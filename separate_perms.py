import argparse
import logging
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom


ns = {'sforce': 'http://soap.sforce.com/2006/04/metadata'}
logging.basicConfig(format='%(message)s', level=logging.DEBUG)

# elements used to name the permission
NAME_TAGS = ['application', 'apexClass', 'name', 'externalDataSource', 'flow',
            'object', 'apexPage', 'recordType', 'tab', 'field']


def parse_args():
    """Function to parse command line arguments."""
    parser = argparse.ArgumentParser(description='A script to create permissionsets.')
    parser.add_argument('-o', '--output', default='force-app/main/default/permissionsets')
    args = parser.parse_args()
    return args


def write_xml(contents, file_name):
    """Write ElementTree to a file"""
    xml_header = '<?xml version="1.0" encoding="UTF-8"?>\n'
    formatted_xml = minidom.parseString(ET.tostring(contents.getroot())).toprettyxml(indent="    ")

    # Remove extra new lines
    formatted_xml = '\n'.join(line for line in formatted_xml.split('\n') if line.strip())

    # Remove existing XML declaration
    formatted_xml = '\n'.join(line for line in formatted_xml.split('\n') if not line.strip().startswith('<?xml'))

    with open(file_name, 'wb') as file:
        file.write(xml_header.encode('utf-8'))
        file.write(formatted_xml.encode('utf-8'))


def create_single_element_xml_file(tag_name, value, perm_directory, parent_perm_name):
    """Create a new XML file for a single element."""
    output_filename = f'{perm_directory}/{parent_perm_name}.{tag_name}.xml'
    # Create an ElementTree with a root element
    root = ET.Element(tag_name)

    # Set the text content for the element
    root.text = value

    # Create an ElementTree object
    tree = ET.ElementTree(root)

    write_xml(tree, output_filename)
    logging.info('Saved %s element content to %s', tag_name, output_filename)


def create_sub_element_xml_file(label, perm_directory, parent_perm_name, tag, full_name):
    """Create a new XML file for a element with sub-elements."""
    output_filename = f'{perm_directory}/{parent_perm_name}.{tag}_{full_name}.xml'

    # Remove the namespace prefix from the element tags
    for element in label.iter():
        if '}' in element.tag:
            element.tag = element.tag.split('}')[1]

    # Create a new XML ElementTree with the label as the root
    tree = ET.ElementTree(label)

    write_xml(tree, output_filename)
    logging.info('Saved %s element content to %s', tag, output_filename)


def process_perm_file(perm_directory, filename):
    """Process a single perm set file and extract elements."""
    # Extract the parent perm set name from the XML file name
    parent_perm_name = filename.split('.')[0]
    perm_file_path = os.path.join(perm_directory, filename)

    tree = ET.parse(perm_file_path)
    root = tree.getroot()

    # Extract values for invididual elements
    for element in root.findall('sforce:*', ns):
        if not element.text.isspace():
            create_single_element_xml_file(element.tag.split('}')[1], element.text, perm_directory, parent_perm_name)
        else:
            for _, label in enumerate(element):
                if label.tag.split('}')[1] in NAME_TAGS:
                    name_tag = label.text
                    break
            create_sub_element_xml_file(element, perm_directory, parent_perm_name, element.tag.split('}')[1], name_tag)


def separate_perms(perm_directory):
    """Separate perm sets into individual XML files."""
    # Iterate through the directory to process files
    for filename in os.listdir(perm_directory):
        if filename.endswith(".permissionset-meta.xml"):
            process_perm_file(perm_directory, filename)


def main(output_directory):
    """Main function."""
    separate_perms(output_directory)


if __name__ == '__main__':
    inputs = parse_args()
    main(inputs.output)
