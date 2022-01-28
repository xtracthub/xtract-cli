# Xtract CLI ("xcli")

Xtract CLI makes it easy to configure Xtract instance by providing a CLI wrapper around  common Funcx and Globus functions.

## Prequisites:
Link to README.md describing other setup (funcx, globus)

## Commands

Name|Functionality|Arguments
-|-|-
configure|Configure Xtract with Funcx and Globus Endpoints|
|test compute|Checks that the specified FuncX Endpoint is online.
|test data|Checks that the specified Globus Endpoint is online. Also checks that file permissions are valid.
|test is-online|Checks whether FuncX and Globus Endpoints are online.
|||

## Install Instructions
Link to README.md describing other setup (funcx, globus)

## First Time Setup
Before using XCLI, users must configure their instance.
Users can run the command `xcli configure`, or perform configuration manually
(not recommended).

User configuration is stored in a JSON file. This file is accessed on
subsequent calls within `xcli`.


## https://funcx.readthedocs.io/en/latest/endpoints.html

## Example
Suppose a user has a funcx and globus deployed on a machine with Endpoint ID 
'AAAA' and 'BBBB', respectively. The user should select an easily identifiable
endpoint name.

The format of the configuration function is:
`xcli configure [OPTIONS] EP_NAME`

Add .xtract/ep_name/config.json

The options are as follows:
  --globus_eid TEXT       Globus Endpoint ID  [required]
  --funcx_eid TEXT        Funcx Endpoint ID  [required]
  --local_download TEXT   Local download  [required]
  --mdata_write_dir TEXT  Metadata write directory  [required]

Configuring xcli is the first step that a user should take:
```
xcli configure test_endpoint --funcx_eid='AAAA' --globus_eid='BBBB' --local_download='~/test_endpoint/download' --mdata_write_dir='~/test_endpoint/write_dir'
```

Xcli configuration creates a JSON file with the provided credentials. The file is configured by default to be stored at '~/EP_NAME/config.json', but it is easily configurable.

```
{
    "ep_name": "test", 
    "globus_eid": "71f9aca8-6929-11ec-b2c3-1b99bfd4976a", 
    "funcx_eid": "da42570c-9e84-4f1b-8a31-fda5a27ed020",
    "local_download": "~/Users/joaovictor/Desktop/local_download", 
    "mdata_write_dir": "~/Users/joaovictor/Desktop/metadata"
}
```

Subsequent calls to xcli will check config.json for Endpoint IDs and paths. 
The configuration file is what makes `xcli` persistent across calls, meaning 
that there is no requirement to use the function as long as `config.json` is
properly set up.

## Checking status
The CLI can be used to verify that Funcx and Globus endpoints are online and
functioning. In addition to checking online status, testing for Globus
liveness includes making sure that the user has sufficient privilege in the
provided directory paths.

Use `xcli test compute --funcx_eid=AAAA` to test Funcx Endpoint liveness.
Use `xcli test data --globus_eid=BBBB --stage_dir=CCCC --mdata_dir=DDDD`
to test Globus Endpoint liveness and proper configuration.

A user may wish to test both Funcx and Globus Endpoints at the same time,
which can be done by using is_online command instead.

`xcli test is_online --funcx_eid=AAAA --globus_eid=BBBB --stage_dir=CCCC --mdata_dir=DDDD`

## Cloning images
The CLI can be used to clone extractor images to a globus endpoint. The images
are cloned to the download 

`xcli fetch containers [ --alls | --materials | --general | --tika ]`

## 
