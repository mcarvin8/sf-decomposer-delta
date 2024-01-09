import argparse
import logging
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom


ns = {'sforce': 'http://soap.sforce.com/2006/04/metadata'}
logging.basicConfig(format='%(message)s', level=logging.DEBUG)


def parse_args():
    """Function to parse command line arguments."""
    parser = argparse.ArgumentParser(description='A script to create workflows.')
    parser.add_argument('-d', '--directory', default='force-app/main/default/workflows')
    args = parser.parse_args()
    return args


def extract_full_name(element, namespace):
    """Extract the full name from a given XML element."""
    full_name_element = element.find('sforce:fullName', namespace)
    return full_name_element.text if full_name_element is not None else None


def create_xml_file(label, workflow_directory, parent_workflow_name, tag, full_name):
    """Create a new XML file for a given element."""
    # Remove the namespace prefix from the tag
    tag_without_namespace = tag.split('}')[-1] if '}' in tag else tag

    subfolder = os.path.join(workflow_directory, parent_workflow_name, tag_without_namespace)
    os.makedirs(subfolder, exist_ok=True)  # Ensure the subfolder exists

    output_filename = f'{subfolder}/{full_name}.{tag_without_namespace}-meta.xml'

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


def process_workflow_file(workflow_directory, filename):
    """Process a single workflow file and extract elements."""
    # Extract the parent workflow name from the XML file name
    parent_workflow_name = filename.split('.')[0]
    workflow_file_path = os.path.join(workflow_directory, filename)

    try:
        tree = ET.parse(workflow_file_path)
        root = tree.getroot()
    except FileNotFoundError:
        logging.info("Error: XML file '%s' not found.", workflow_file_path)
        return
    except ET.ParseError:
        logging.info("Error: Unable to parse the XML file.")
        return


    # Extract all unique XML tags dynamically
    xml_tags = {elem.tag for elem in root.iter() if '}' in elem.tag}

    # Iterate through the dynamically extracted XML tags
    for tag in xml_tags:
        for _, label in enumerate(root.findall(tag, ns)):
            full_name = extract_full_name(label, ns)

            if full_name:
                create_xml_file(label, workflow_directory, parent_workflow_name, tag, full_name)
            else:
                logging.info('Skipping %s element without fullName', tag)


def separate_workflows(workflow_directory):
    """Separate workflows into individual XML files."""
    # Iterate through the directory to process files
    for filename in os.listdir(workflow_directory):
        if filename.endswith(".workflow-meta.xml"):
            process_workflow_file(workflow_directory, filename)


def main(workflow_directory):
    """Main function."""
    separate_workflows(workflow_directory)


if __name__ == '__main__':
    inputs = parse_args()
    main(inputs.directory)
