#  Salesforce Python Git (sfpygit) Delta - Custom Salesforce DX Structure

This is a python 3 script to build a manifest file for Salesforce deployments from the git diff.

This is dependent on the custom directory structures introduced by:
1. https://github.com/mcarvin8/labels-and-workflows
2. https://github.com/mcarvin8/permission-sets

The scripts from the above repos have been copied into this one. The custom structure only affects custom labels, workflows, and permission sets. All other metadata types follow the default structure.

If you are using the default Salesforce DX project structure for custom labels, workflows, permission sets, do NOT use this script to build the delta package.

Use a tool such as the SFDX Git Delta plugin to build delta packages from a git diff with projects that complies with the default Salesforce DX structure.

## Initial Configuration

The running environment requires Python 3 and the Git Bash.

1. Fork this repository, delete the example files, and seed the repository by retrieving all objects from the production org.
2. Run the separate scripts for custom labels, workflows, permission sets. 

```
    - python3 ./separate_labels.py
    - python3 ./separate_workflows.py
    - python3 ./separate_perms.py
```

3. Push this repo and allow developers to push changes. The above separate scripts will need to be run each time a developer retrieves labels, workflows, or perm sets.

## Building a Delta Manifest File for Deployments

The `sfpygit_delta.py` script supports the following arguments:

- `-f` - commit sha from where the diff is done (example - HEAD^1 or HEAD~1 )
- `-t` - commit sha to where the diff is done (example - HEAD)
- `-j` - path to metadata json file [default - `metadata.json`]
- `-m` - output delta manifest file [default - `package.xml`]
- `-d` - source directory for metadata  [default - `force-app/main/default`]

`python3 ./sfpygit_delta.py -f "commit_sha" -t "commit_sha"`

The script will create the delta manifest file with the additions/changes to metadata and the delta destructive changes manifest files, if any files were deleted. 
- An empty package.xml for destructive deployments is required with the `destructiveChanges/destructiveChanges.xml`.

After the delta package is created, the `parse_package.py` script can be used to parse the file and only compile labels, workflows, and permission sets listed in the package.

`python3 ./parse_package.py --manifest "package.xml"`

Otherwise, run the combine scripts directly before deployment to compile all labels, workflows, and permission sets.

```
    - python3 ./combine_labels.py
    - python3 ./combine_workflows.py
    - python3 ./combine_perms.py
```

## Metadata JSON

The JSON file was created from the SFDX git delta plugin (v59.json) and updated as such to account for the custom labels/workflow/permission sets structure and other updates noticed while testing other metadata types.

- `useFoldername` key added for several metadata types to ensure the package.xml uses the folder name for certain metadata types that are placed in sub-folders.
    - My current company's metadata directory had metadata such as `staticresources`, `aura`, and `lwc` in sub-folders and directly in the metadata root folder. The script has been made to work with either option. The `inFolder` key was changed from false to true for these types.
``` json
    {
      "directoryName": "staticresources",
      "inFolder": true,
      "useFoldername": true,
      "metaFile": true,
      "suffix": "resource",
      "xmlName": "StaticResource"
    },
   {
      "directoryName": "aura",
      "inFolder": true,
      "useFoldername": true,
      "metaFile": false,
      "xmlName": "AuraDefinitionBundle"
    },
    {
      "directoryName": "lwc",
      "inFolder": true,
      "useFoldername": true,
      "metaFile": false,
      "xmlName": "LightningComponentBundle"
    },
```
- Bots will only use the `Bot` metadata type and not `BotVersion` per previous Bot testing. Bot deployments always require the meta file to be deployed. Deploying with `BotVersion` alone will not deploy the overall meta file.
    - To avoid re-deploying the active or inactive bot versions, I suggest adding these versions to the `.forceignore` file.
    - `inFolder` changed from False to True
    - `useFolderName` key added and set to True to ensure it uses the sub-folder name the bot files are in
``` json
    {
      "directoryName": "bots",
      "xmlName": "Bot",
      "inFolder": true,
      "useFoldername": true,
      "metaFile": true
    },
```
- Children workflow types removed from `Workflow` due to an existing Salesforce CLI bug with deploying workflow children. Any workflow diffs will be added as `Workflow`.
    - Children workflow types can be retrieved in a manifest using the CLI and is the suggested path to retrieving just workflow children before running `separate_workflows.py` to add workflow updates to Git.
- Workflows updates to use `inFolder` and `useFoldername` keys due to the directory structure updates made by the workflow scripts (`separate_workflows.py` and `combine_workflows.py`)
``` json
    {
      "childXmlNames": false,
      "directoryName": "workflows",
      "inFolder": true,
      "useFoldername": true,
      "metaFile": false,
      "suffix": "workflow",
      "xmlName": "Workflow"
    },
```
- Removed `parentXmlName` from custom labels (not needed). No updates needed to support custom label directory structure changes.
``` json
     {
      "directoryName": "labels",
      "inFolder": false,
      "metaFile": false,
      "xmlName": "CustomLabel",
      "suffix": "labels",
      "xmlTag": "labels",
      "key": "fullName"
    },
```
- Permission set updates to use `inFolder` and `useFoldername` keys due to the directory structure updates made by the permission set scripts (`separate_perms.py` and `combine_perms.py`)
``` json
    {
      "directoryName": "permissionsets",
      "inFolder": true,
      "useFoldername": true,
      "metaFile": false,
      "suffix": "permissionset",
      "xmlName": "PermissionSet"
    },
```

## Reverting to the Default DX Structure for Workflows and Permission Sets

At a bare minimum, the Custom Labels updates could be applied to the directory structure, while retaining the default structure for Workflows and Permission Sets.

To only use the custom updates for Custom Labels:

- Delete `combine_workflows.py`, `combine_perms.py`, `separate_perms.py`, and `separate_workflows.py`
- Update `parse_package.py` to remove workflows and permission sets, if you wish to use this script.
- Remove these lines from the `.forceignore` file:
```
**/permissionsets/*.xml
**/workflows/*.xml

!**/permissionsets/*.permissionset-meta.xml
!**/workflows/*.workflow-meta.xml
```

- Remove these lines from the `.gitignore` file:
```
*.permissionset-meta.xml
*.workflow-meta.xml
```

- Update the Metadata JSON file as such to revert to the default attributes for Workflows and Permission Sets.
    - Workflows should still set `childXmlNames` to false as long as the Salesforce CLI bug is open.
``` json
  {
    "directoryName": "permissionsets",
    "inFolder": false,
    "metaFile": false,
    "suffix": "permissionset",
    "xmlName": "PermissionSet"
  },
```

``` json
    {
      "childXmlNames": false,
      "directoryName": "workflows",
      "inFolder": false,
      "metaFile": false,
      "suffix": "workflow",
      "xmlName": "Workflow"
    },
```



