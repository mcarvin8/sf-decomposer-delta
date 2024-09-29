import argparse
import json
import logging
import os
import subprocess

import get_package_directories

# format logger
logging.basicConfig(format='%(message)s', level=logging.DEBUG)


def parse_args():
    """Function to pass required arguments."""
    parser = argparse.ArgumentParser(description='A script to build a manifest from the git diff.')
    parser.add_argument('-f', '--from', dest='from_value')
    parser.add_argument('-t', '--to', dest='to_value')
    parser.add_argument('-j', '--json', default='metadata.json')
    parser.add_argument('-m', '--manifest', default='package.xml')
    args = parser.parse_args()
    return args


def get_git_diff_changes(commit1, commit2, source_folders):
    """Run the git diff and find changes in any Salesforce DX directory."""
    git_diff_command = f'git diff {commit1} {commit2} --name-status'
    result = subprocess.run(git_diff_command, shell=True,
                            capture_output=True, text=True, check=True)

    changes = []
    destructive_changes = []
    for line in result.stdout.splitlines():
        status, filepath = line.split('\t', 1)
        # Check if the file is in any of the source folders (package directories)
        if any(filepath.startswith(source_folder) for source_folder in source_folders):
            if status.startswith(('A', 'M')):
                changes.append(filepath)
            elif status.startswith('D'):
                destructive_changes.append(filepath)

    return changes, destructive_changes

def determine_metadata_name(metadata_mapping, first_directory, filepath):
    """Determine the metadata name based on metadata type information."""
    # Get the parent and child objects from the file path
    parent_path = os.path.basename(os.path.dirname(filepath))
    child_path = os.path.splitext(os.path.basename(filepath))[0].split('.')[0]

    metadata_info = metadata_mapping[first_directory]
    metadata_type = metadata_info['xmlName']

    # Check if the metadata type has children
    if 'childXmlNames' in metadata_info and parent_path != child_path:
        metadata_name = f'{os.path.basename(os.path.split(os.path.dirname(filepath))[0])}.{child_path}'
        child_metadata_info = metadata_mapping[parent_path]
        metadata_type = child_metadata_info['xmlName']
    else:
        metadata_name = os.path.splitext(os.path.basename(filepath))[0]

    filtered_parts = [part for part in metadata_name.split('.') if all(substring not in part for substring in ('meta', 'xml', 'svg'))]
    metadata_name = '.'.join(filtered_parts)

    # Include folder name in the metadata member name for items with 'InFolder' set to true
    if metadata_info.get('inFolder', False):
        folder_name = os.path.basename(os.path.dirname(filepath))
        # Just use folder name immediately after the metadata type folder for certain types
        if metadata_info.get('useFoldername', False):
            metadata_name = filepath.split(first_directory)[1].split('/')[1]
            # split by period in case it's a file not in a folder
            metadata_name = metadata_name.split('.')[0]
        else:
            metadata_name = f'{folder_name}/{metadata_name}'

    return metadata_name, metadata_type


def determine_metadata_type(git_diffs, metadata_json_file, source_folders):
    """Determine the applicable Salesforce metadata type."""
    with open(metadata_json_file, 'r', encoding='utf-8') as metadata_json:
        metadata_types = json.load(metadata_json)

    metadata_mapping = {metadata['directoryName']: metadata for metadata in metadata_types}

    changes = {}

    for filepath in git_diffs:
        # Identify the relevant source folder for each file
        matching_folder = None
        for folder in source_folders:
            if filepath.startswith(folder):
                matching_folder = folder
                break

        if matching_folder:
            relative_path = os.path.relpath(filepath, matching_folder)
            first_directory = relative_path.split(os.path.sep)[0]

            if first_directory in metadata_mapping:
                metadata_name, metadata_type = determine_metadata_name(metadata_mapping, first_directory, filepath)

                if metadata_type not in changes:
                    changes[metadata_type] = set()

                if metadata_name not in changes[metadata_type]:
                    changes[metadata_type].add(metadata_name)
            else:
                logging.info('WARNING: No matching directory found for `%s` in metadata JSON file.', filepath)

    return changes


def create_package_file(items, output_file):
    """Create the final deployment package."""
    pkg_header = '<?xml version="1.0" encoding="UTF-8"?>\n'
    pkg_header += '<Package xmlns="http://soap.sforce.com/2006/04/metadata">\n'

    # Sort the keys in items alphabetically (case-insensitive)
    sorted_items = {key: sorted(items[key], key=str.lower) for key in sorted(items, key=str.lower)}

    # Initialize the package contents with the header
    package_contents = pkg_header

    # Append each item to the package
    for metadata_type, metadata_list in sorted_items.items():
        package_contents += '\t<types>\n'
        for member_name in metadata_list:
            package_contents += f'\t\t<members>{member_name}</members>\n'
        package_contents += f'\t\t<name>{metadata_type}</name>\n'
        package_contents += '\t</types>\n'

    # Append the footer to the package
    pkg_footer = '</Package>\n'
    package_contents += pkg_footer

    # Write the package contents to the output file
    with open(output_file, 'w', encoding='utf-8') as package_file:
        package_file.write(package_contents)


def main(from_commit_sha, to_commit_sha, metadata_json, manifest):
    """Main function."""
    source_folders = get_package_directories.main('sfdx-project.json')
    metadata_changes, destructive_changes = get_git_diff_changes(from_commit_sha, to_commit_sha, source_folders)

    metadata_changes = determine_metadata_type(metadata_changes, metadata_json, source_folders)

    if metadata_changes:
        create_package_file(metadata_changes, manifest)
        logging.info('Manifest file with additions/changes created at: %s', manifest)
    else:
        logging.info('No metadata additions/changes found.')

    if destructive_changes:
        destructive_directory = 'destructiveChanges'
        try:
            os.mkdir(destructive_directory)
        except FileExistsError:
            pass
        destructive_metadata_changes = determine_metadata_type(destructive_changes, metadata_json, source_folders)
        create_package_file(destructive_metadata_changes, f'{destructive_directory}/destructiveChanges.xml')
        # empty package.xml required for destructive deployments
        create_package_file({}, f'{destructive_directory}/package.xml')
        logging.info('Destructive manifest file created at: %s', 'destructiveChanges.xml')
    else:
        logging.info('No destructive metadata changes found.')


if __name__ == '__main__':
    inputs = parse_args()
    main(inputs.from_value, inputs.to_value,
         inputs.json, inputs.manifest)
