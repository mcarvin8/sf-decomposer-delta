#  Salesforce Python Git (sfpygit) Delta - Custom Salesforce DX Structure

This is a Python 3 script to build a manifest file for Salesforce deployments from the git diff. This is intended for users using my [Salesforce decomposer](https://github.com/mcarvin8/sf-decomposer) plugin.

This script requires you to create the `sfdecomposer.config.json` config file from the sf-decomposer plugin in the root of your repo which is used to run the sf decomposer plugin during Salesforce CLI comamnds.

``` json
{
  "metadataSuffixes": "labels,workflow,profile",
  "prePurge": true,
  "postPurge": true,
  "decomposedFormat": "xml"
}
```

In terms of this Python script to build a delta package.xml, the only entry in the JSON which will matter is the `metadataSuffixes` key. This will tell the package script which metadata types you are decomposing using my plugin.

If you are not using my sf-decomposer plugin, do not use this script. Use a tool such as the SFDX Git Delta plugin to build delta packages from a git diff with projects that complies with the default Salesforce DX structure.

## Initial Configuration

The running environment requires Python 3 and Git Bash.

## Building a Package.xml from the git diff for sf-decomposer users

The `sf_decomposer_delta.py` script supports the following arguments:

- `-f`/`--from` - commit sha from where the diff is done (example - HEAD^1 or HEAD~1 )
- `-t`/`--to` - commit sha to where the diff is done (example - HEAD)
- `-j`/`--json` - path to metadata json file [default - `metadata.json`]
- `-m`/`--manifest` - output delta manifest file [default - `package.xml`]

`python3 ./sf_decomposer_delta.py --from  "commit_sha" --to "commit_sha"`

The script will create the delta manifest file with the additions/changes to metadata and the delta destructive changes manifest files, if any files were deleted. 
- An empty package.xml for destructive deployments is required with the `destructiveChanges/destructiveChanges.xml`.
