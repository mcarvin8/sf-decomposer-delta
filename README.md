#  Salesforce Python Git (sfpygit) Delta - Custom Salesforce DX Structure

This is a python 3 script to build a manifest file for Salesforce deployments from the git diff.

This is dependent on the custom directory structures introduced by these repositories:
1. https://github.com/mcarvin8/labels-and-workflows-decomposer
2. https://github.com/mcarvin8/permission-sets-decomposer
3. https://github.com/mcarvin8/profiles-decomposer
4. https://github.com/mcarvin8/sfdx-decomposer (All above metadata types combined)

Depending on which metadata types you would like to implement, clone the applicable repository and copy the `sfpygit_delta.py` and `metadata.json` file from here.

The custom structure only affects custom labels, workflows, profiles and permission sets. All other metadata types follow the default structure.

If you are using the default Salesforce DX project structure for custom labels, workflows, profiles, and permission sets, do NOT use this script to build the delta package.

Use a tool such as the SFDX Git Delta plugin to build delta packages from a git diff with projects that complies with the default Salesforce DX structure.

## Initial Configuration

The running environment requires Python 3 and Git Bash.

## Building a Delta Manifest File for Deployments

The `sfpygit_delta.py` script supports the following arguments:

- `-f`/`--from` - commit sha from where the diff is done (example - HEAD^1 or HEAD~1 )
- `-t`/`--to` - commit sha to where the diff is done (example - HEAD)
- `-j`/`--json` - path to metadata json file [default - `metadata.json`]
- `-m`/`--manifest` - output delta manifest file [default - `package.xml`]
- `-d`/`--directory` - source directory for metadata  [default - `force-app/main/default`]

`python3 ./sfpygit_delta.py --from  "commit_sha" --to "commit_sha"`

The script will create the delta manifest file with the additions/changes to metadata and the delta destructive changes manifest files, if any files were deleted. 
- An empty package.xml for destructive deployments is required with the `destructiveChanges/destructiveChanges.xml`.

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
- Workflows updates to use `inFolder` and `useFoldername` keys due to the directory structure updates made by the custom directory structure
``` json
    {
      "directoryName": "workflows",
      "inFolder": true,
      "useFoldername": true,
      "metaFile": false,
      "suffix": "workflow",
      "xmlName": "Workflow"
    },
```
- Removed `parentXmlName` from custom labels (not needed). No updates needed to support the custom directory structure
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
- Permission set and profile updates to use `inFolder` and `useFoldername` keys due to the custom directory structure
``` json
    {
      "directoryName": "permissionsets",
      "inFolder": true,
      "useFoldername": true,
      "metaFile": false,
      "suffix": "permissionset",
      "xmlName": "PermissionSet"
    },
    {
      "directoryName": "profiles",
      "inFolder": true,
      "useFoldername": true,
      "metaFile": false,
      "suffix": "profile",
      "xmlName": "Profile",
      "pruneOnly": true
    },
```
