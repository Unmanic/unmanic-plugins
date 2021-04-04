#!/usr/bin/env python3
import glob
import json
import os
import shutil
import zipfile

import pip

project_root = os.path.dirname(os.path.realpath(__file__))
repo_source_path = os.path.join(project_root, 'source')
repo_dest_path = os.path.join(project_root, 'repo')
repo_json_file = os.path.join(repo_dest_path, 'repo.json')


def zipdir(path, zip):
    for root, dirs, files in os.walk(path):
        for file in files:
            zip.write(os.path.join(root, file))


def install_requirements(package):
    requirements_file = os.path.join(item_path, 'requirements.txt')
    install_target = os.path.join(item_path, 'site-packages')
    if not os.path.exists(requirements_file):
        print('      - no requirements.txt file found')
        return

    pip.main(['install', '--upgrade', '-r', requirements_file, '--target={}'.format(install_target)])


print("-----------------------------------------------------------------------------")
print("------------------------------------START------------------------------------")
print("-----------------------------------------------------------------------------")
print()

# Ensure the repo directory exists
if not os.path.exists(repo_dest_path):
    os.makedirs(repo_dest_path)

# Build repo based on files in source directory
print(">> Processing Plugins <<")
for item in os.listdir(repo_source_path):
    item_path = os.path.join(repo_source_path, item)
    # Ignore files in the root directory of the source path
    # Ignore git configuration files
    if (os.path.isdir(item_path)) and ('.git' not in item):
        # Read plugin info
        info_file = os.path.join(item_path, 'info.json')
        with open(info_file) as f:
            plugin_info = json.load(f)

        # Set destination data
        dest_dir = os.path.join(repo_dest_path, item)
        plugin_zip_file = "{}-{}.zip".format(item, plugin_info.get('version'))
        plugin_zip = os.path.join(dest_dir, plugin_zip_file)

        # Ensure all required data is present
        for value in ['id', 'name', 'author', 'version', 'tags', 'description']:
            if value not in plugin_info:
                msg = "Plugin '{}' is missing required information '{}' in it's info.json file.".format(item, value)
                raise Exception(msg)

        # Print data variables for info
        print("  ------------------------------->")
        print("  > Process plugin:  '{}'".format(plugin_info.get('name')))
        print("    ID:               {}".format(plugin_info.get('id')))
        print("    Author:           {}".format(plugin_info.get('author')))
        print("    Version:          {}".format(plugin_info.get('version')))
        print("    Tags:             {}".format(plugin_info.get('tags')))
        print("    Description:      {}".format(plugin_info.get('description')))
        print()

        # Ensure that we are not overwriting a plugin that already exists with this version
        if os.path.exists(plugin_zip):
            print("")
            print("  !WARNING! Repository already contains {}.".format(plugin_zip_file))
            print("  You will need to either:")
            print("      - Remove the current file '{}'".format(plugin_zip))
            print("      OR")
            print("      - increase the plugin's version number if you wish to overwrite the current version.")
            print("  Will not process plugin: '{}'".format(plugin_info.get('name')))
            print()
            continue

        # Ensure repo destination directory exists
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        # Copy plugin info.json to dest
        print('    Installing plugin metadata to repo...')
        print('      - Copying: {} >>>> {}/info.json'.format(info_file, dest_dir))
        shutil.copy(info_file, dest_dir)

        # Add additional files (optional files)
        for file in glob.glob(os.path.join(item_path, '*changelog.txt')):
            print('      - Copying: {} >>>> {}/changelog.txt'.format(file, dest_dir, plugin_info.get('version')))
            shutil.copy(file, dest_dir)
        for file in glob.glob(os.path.join(item_path, '*icon.*')):
            print('      - Copying: {} >>>> {}/icon.png'.format(file, dest_dir))
            shutil.copy(file, dest_dir)
        for file in glob.glob(os.path.join(item_path, '*fanart.*')):
            print('      - Copying: {} >>>> {}/fanart.jpg'.format(file, dest_dir))
            shutil.copy(file, dest_dir)
        print()

        # Install any package requirements
        print("    Installing Python package requirements...")
        install_requirements(item_path)

        # Generate a zip file from the plugin contents
        print("    Compressing {}...".format(plugin_zip))
        zip_file = zipfile.ZipFile(plugin_zip, 'w', zipfile.ZIP_DEFLATED)
        for root, dirs, files in os.walk(item_path):
            for file in files:
                absname = os.path.abspath(os.path.join(root, file))
                arcname = absname[len(item_path) + 1:]
                print('      - Zipping: {} >>> {} | ({})'.format(os.path.join(root, file), arcname, plugin_zip))
                zip_file.write(os.path.join(root, file), arcname)
        zip_file.close()

        print()

# Write Repo data based on what is now in the repo directory
print("-----------------------------------------------------------------------------")
print(">> Processing Repo <<")
repo_data = {
    "repo":    {},
    "plugins": [],
}
for item in os.listdir(repo_dest_path):
    item_path = os.path.join(repo_dest_path, item)
    # Ignore files in the root directory of the source path
    # Ignore git configuration files
    if (os.path.isdir(item_path)) and ('.git' not in item):
        # Read plugin info
        info_file = os.path.join(item_path, 'info.json')
        with open(info_file) as f:
            plugin_info = json.load(f)
        # Append plugin info to repo data
        repo_data['plugins'].append(plugin_info)
        continue

# Add main repo info to repo data
with open(os.path.join(repo_source_path, 'repo.json')) as f:
    repo_info = json.load(f)
    repo_data['repo'] = repo_info.get('repo')

# Install repo_data to repo's plugins.json file
print("  ------------------------------->")
print("  > Writing repo plugin list to '{}'...".format(repo_json_file))
with open(repo_json_file, 'w') as json_file:
    json.dump(repo_data, json_file, indent=4)

# TODO: add checksum to plugins_json_file file

print()
print("-----------------------------------------------------------------------------")
print("-------------------------------------END-------------------------------------")
print("-----------------------------------------------------------------------------")
