#!/usr/bin/env bash
###
# File: create_plugin_pr_branch copy.sh
# Project: workflow_scripts
# File Created: Friday, 26th August 2022 8:17:10 pm
# Author: Josh.5 (jsunnex@gmail.com)
# -----
# Last Modified: Tuesday, 30th August 2022 6:57:36 pm
# Modified By: Josh.5 (jsunnex@gmail.com)
###
#
# Generate a plugin PR for the official repo
#
###

plugin_id="${@}"
repo_root_path=$(readlink -e $(dirname "${BASH_SOURCE[0]}")/../../)
plugin_location="${repo_root_path}/build/plugin.${plugin_id}"
mkdir -p "${repo_root_path}/build"
default_branch="official"

if [[ -z ${plugin_id} ]]; then
    echo "You forgot to provide the ID of one of your plugins..."
    exit 1
fi


# DEBUGGING - Only required for running script locally
if [[ ! -z ${script_debugging} ]]; then
    # Ensure the default branch is checked out
    git checkout "${default_branch}"
    # Clone plugin to directory if it does not exist
    if [[ ! -d ${plugin_location} ]]; then
        echo -e "\n*** Cloning plugin git repo to '${tmp_dir}/${plugin_id}'"
        git clone --depth=1 --branch master --single-branch "git@github.com:Unmanic/plugin.${plugin_id}" "${plugin_location}"
        [[ $? -gt 0 ]] && echo "Failed to fetch the plugin git repository. Exit!" && exit 1;
    fi
fi


########################################################################
### CREATE PR BRANCH
pushd "${repo_root_path}" &> /dev/null
# Create clean PR branch 
echo -e "\n*** Checkout clean PR branch for plugin"
git branch -D "pr-${plugin_id}" 2> /dev/null
git checkout -b "pr-${plugin_id}"
popd &> /dev/null


########################################################################
### UPDATE SUBMODULES
pushd "${plugin_location}" &> /dev/null
# Update any submodules
echo -e "\n*** Pulling plugin submodules"
git submodule update --init --recursive 
popd &> /dev/null


########################################################################
### PATCH PROJECT
pushd "${plugin_location}" &> /dev/null
# Apply any patches
if [[ -d ./patches ]]; then
    echo -e "\n*** Patching project"
    find ./patches -type f -name "*.patch" -exec patch -p1 --input="{}" --forward --verbose \;
fi
popd &> /dev/null


########################################################################
### BUILD/INSTALL
pushd "${repo_root_path}" &> /dev/null
# Install/update plugin files
echo -e "\n*** Installing files from plugin git repo to this repository's source directory"
mkdir -p "${repo_root_path}/source/${plugin_id}"
rsync -avh --delete \
    --exclude='.git/' \
    --exclude='.github/' \
    --exclude='.gitmodules' \
    --exclude='.idea/' \
    "${plugin_location}/" "${repo_root_path}/source/${plugin_id}"
# Read plugin version
plugin_version=$(cat ${plugin_location}/info.json | jq -rc '.version')
[[ ${plugin_version} == "null" ]] && echo "Failed to fetch the plugin's version from the info.json file. Exit!" && exit 1;
popd &> /dev/null


########################################################################
### COMMIT
pushd "${repo_root_path}" &> /dev/null
echo -e "\n*** Commit changes in unmanic-plugins repository"
commit_message="[${plugin_id}] v${plugin_version}"
echo ${commit_message}
git add "source/${plugin_id}"
git commit -m "${commit_message}"
if [[ $? -gt 0 ]]; then
    echo
    echo "No commit created. Possibly because there was nothing to commit!"
    echo "PR branch will not be pushed." 
    # export result
    echo "failed" > result.txt
    # Fail without an exit 1 in actions so the pipeline can faile silently 
    exit
fi
echo "success" > result.txt
popd &> /dev/null


# ########################################################################
# ### PUBLISH
# # NOTE: Disabled publishing here. This will be handled by another job in the workflow
# pushd "${repo_root_path}" &> /dev/null
# echo -e "\n*** Publish changes to origin unmanic-plugins repository"
# git push  https://$GH_TOKEN@github.com/${CLOUDYR_REPO}.git -f "pr-${plugin_id}"
# popd &> /dev/null
