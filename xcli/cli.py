from ctypes import get_errno
from distutils.command.config import config
from distutils.util import execute
from importlib.resources import path
from multiprocessing.sharedctypes import Value
import click
from funcx.utils.errors import FuncXUnreachable
import mdf_toolbox
import os
import json
from funcx.sdk.client import (TaskPending, FuncXClient)
from globus_sdk import (TransferAPIError, TransferData)
from time import sleep
import pathlib

DEBUG = False
APP_NAME = "Xtract CLI"
CLIENT_ID = "7561d66f-3bd3-496d-9a29-ed9d7757d1f2"

def validate_config_file():
    pass

def wait_for_ep(fxc, funcx_response, name, timeout=60, increment=2):
    fxc_task = fxc.get_task(funcx_response)
    time_elapsed = 0
    while time_elapsed < timeout:
        if fxc_task['pending'] is True:
            click.echo(f"{name} pending... {time_elapsed} seconds elapsed.")
            sleep(increment)
            time_elapsed += increment
            fxc_task = fxc.get_task(funcx_response)
        else:
            return True
    click.echo(f"{name} timed out after {time_elapsed} seconds.")
    return False

# Acquire authentication via mdf_toolbox
auths = mdf_toolbox.login(
    services=[
        "openid",
        "data_mdf",
        "search",
        "petrel",
        "transfer",
        "dlhub",
        "https://auth.globus.org/scopes/facd7ccc-c5f4-42aa-916b-a0e270e2c2a9/all",
    ],
    app_name="Foundry",
    make_clients=True,
    no_browser=True,
    no_local_server=False,
    # TODO: clear old tokens may need to be set to true initially
    # clear_old_tokens=True # learn more about Globus' oauth system and improve this.
)

# TODO: Create a timeout decorator
# TODO: Create overarching context from CLI with funcx client initialization
# TODO: Separate functions into modules (inward facing, outward facing)

# Acquire the Globus TransferClient
tc = auths['transfer']
# click.echo(vars(tc)) # Debug

@click.group()
def cli():
    pass

@cli.command()
@click.argument('ep_name')
@click.option('--globus_eid', default=None, required=True, help='Globus Endpoint ID')
@click.option('--funcx_eid', default=None, required=True, help='Funcx Endpoint ID')
@click.option('--local_download', default=None, required=True, help='Local download')
@click.option('--mdata_write_dir', default=None, required=True, help='Metadata write directory')
def configure(ep_name, globus_eid, funcx_eid, local_download, mdata_write_dir):
    config = {
        'ep_name': ep_name,
        'globus_eid': globus_eid,
        'funcx_eid': funcx_eid,
        'local_download': os.path.expanduser(local_download), #expand user to make workable directories
        'mdata_write_dir': os.path.expanduser(mdata_write_dir),
    }
    config_json = json.dumps(config)

    if os.path.exists(os.path.expanduser(f"~/.xtract/{ep_name}/config.json")):
        print("Configuration already exists. Overwriting current settings.")

    os.makedirs(os.path.dirname(os.path.expanduser(f"~/.xtract/{ep_name}/config.json")), exist_ok=True)
    with open(os.path.expanduser(f"~/.xtract/{ep_name}/config.json"), "w") as f:
        f.write(config_json)
    click.echo(f"Successfully configured {ep_name} Xtract Endpoint!")

@cli.group()
def test():
    pass

def compute_fn(funcx_eid, func_uuid):
    fxc = FuncXClient()
    funcx_response = fxc.run(endpoint_id=funcx_eid, function_id=func_uuid)

    timeout=10
    increment=2

    if not wait_for_ep(fxc, funcx_response, "Test compute", timeout, increment):
        return (False, f'Error -- Funcx timed out after {timeout} seconds')

    fxc_result = fxc.get_result(funcx_response)
    if fxc_result is not None and fxc_result == 'Hello World!':
        return (True, "Task complete -- result: {fxc_result}")
    elif fxc_result != 'Hello World!':
        return (False, f"Error -- Expected: \'Hello World!\', but received: \'{fxc_result}\'")

def data_fn(globus_eid):
    try:
        endpoint = tc.get_endpoint(globus_eid)
    except TransferAPIError as error:
        click.echo(f'Error -- Code: {error.code}, Message: {error.message}')
        return
    # print(endpoint)
    if endpoint["is_globus_connect"]:
        return endpoint["gcp_connected"]
    elif endpoint["DATA"][0]["is_connected"]:
        return True
    else:
        return False

def check_read_fn(path, funcx_eid):
    fxc = FuncXClient()
    funcx_response = fxc.run(path, endpoint_id=funcx_eid, function_id="ab148dec-7f77-446f-81e4-934f58c3b472")

    timeout=10
    increment=2

    if not wait_for_ep(fxc, funcx_response, "Check read permissions", timeout, increment):
        return (False, f'Error -- Funcx timed out after {timeout} seconds')
    # error checking here?
    return fxc.get_result(funcx_response)

def check_write_fn(path, funcx_eid):
    fxc = FuncXClient()
    funcx_response = fxc.run(path, endpoint_id=funcx_eid, function_id="c1bcf355-fb42-4ad9-9f6c-994876d693e7")

    timeout=10
    increment=2

    if not wait_for_ep(fxc, funcx_response, "Check write permissions", timeout, increment):
        return (False, f'Error -- Funcx timed out after {timeout} seconds')
    # error checking here?
    return fxc.get_result(funcx_response)

def get_permissions(globus_eid, path):
    pure_path = pathlib.PurePath(path)
    path_parent = pure_path.parents[0]
    folder = pure_path.name
    output = {
        "read": False, 
        "write": False,
        "execute": False
        }

    # print(path)
    # print(pure_path)
    # print(path_parent)
    # print(folder)

    res = tc.operation_ls(endpoint_id=globus_eid, path=str(path_parent))
    array = res["DATA"]

    # print(array)

    permissions = None
    for file in array:
        if file["name"] == folder:
            permissions = file["permissions"]
            break

    if not permissions:
        print(f"Directory {path} not found. Please make sure it is created.")
        return -1
    
    def octal_to_string(octal):
        permission = ["---", "--x", "-w-", "-wx", "r--", "r-x", "rw-", "rwx"]
        result = []
        for idx, value in enumerate([int(n) for n in str(octal)]):
            if idx == 0: continue # skip the first value
            result.append({c for c in permission[value]})
        return result

    # TODO: experiment with permissions to see how it works
    user, group, others = octal_to_string(permissions)
    if "r" in user or "r" in others:
        output['read'] = True
    if "w" in user or "w" in others:
        output['write'] = True
    if "x" in user or "x" in others:
        output['execute'] = True
    return output

# probably would be nice to inherit a context here!
@test.command()
@click.argument('ep_name')
# @click.option('--funcx_eid', default=None, required=False, help='Funcx Endpoint ID')
# @click.option('--func_uuid', default=None, required=False, help='Function UUID')
def compute(ep_name): #, funcx_eid, func_uuid):
    # check whether the config exists
    if not os.path.exists(os.path.expanduser(f"~/.xtract/{ep_name}/config.json")):
        click.echo(f"Endpoint {ep_name} does not exist! Run `xcli configure` first.")
        return

    f = open(os.path.expanduser(f"~/.xtract/{ep_name}/config.json"))
    config = json.loads(f.read())
    funcx_eid = config["funcx_eid"]
    func_uuid = "4b0b16ad-5570-4917-a531-9e8d73dbde56" # Hello World Function UUID

    # res = compute_fn(funcx_eid, func_uuid)
    click.echo(
        {"funcx_online":compute_fn(funcx_eid, func_uuid)[0]})

@test.command()
# @click.option('--globus_eid', default=None, required=True, help='Globus Endpoint ID')
# @click.option('--stage_dir', default=None, required=True)
# @click.option('--mdata_dir', default=None, required=True)
@click.argument('ep_name')
def data(ep_name):
    # check whether the config exists
    if not os.path.exists(os.path.expanduser(f"~/.xtract/{ep_name}/config.json")):
        click.echo(f"Endpoint {ep_name} does not exist! Run `xcli configure` first.")
        return

    f = open(os.path.expanduser(f"~/.xtract/{ep_name}/config.json"))
    config = json.loads(f.read())
    globus_eid = config["globus_eid"]
    stage_dir = config["local_download"] #TODO: make sure this is right with Tyler
    mdata_dir = config["mdata_write_dir"]

    res = {
        "globus_online":data_fn(globus_eid)
    }

    stage_dir_permissions = get_permissions(globus_eid, stage_dir)
    mdata_dir_permissions = get_permissions(globus_eid, mdata_dir)

    if stage_dir_permissions == -1: 
        res["stage_dir"] = False
    else:
        res["stage_dir"] = stage_dir_permissions['read']
    
    if mdata_dir_permissions == -1:
        res["mdata_dir"] = False
    else:
        res["data_dir"] = mdata_dir_permissions['write']

    click.echo(res)
    
@test.command()
@click.argument('ep_name')
# @click.option('--funcx_eid', default=None, required=True, help='Funcx Endpoint ID')
# @click.option('--func_uuid', default=None, required=True, help='Function UUID')
# @click.option('--globus_eid', default=None, required=False, help='Globus Endpoint ID')
# @click.option('--stage_dir', default=None, required=False)
# @click.option('--mdata_dir', default=None, required=False)
def is_online(ep_name): # funcx_eid, func_uuid, globus_eid, stage_dir, mdata_dir):
    # check whether the config exists
    if not os.path.exists(os.path.expanduser(f"~/.xtract/{ep_name}/config.json")):
        click.echo(f"Endpoint {ep_name} does not exist! Run `xcli configure` first.")
        return

    f = open(os.path.expanduser(f"~/.xtract/{ep_name}/config.json"))
    config = json.loads(f.read())

    funcx_eid = config["funcx_eid"]
    func_uuid = "4b0b16ad-5570-4917-a531-9e8d73dbde56" # Hello World Function UUID
    globus_eid = config["globus_eid"]
    stage_dir = config["local_download"] #TODO: make sure this is right with Tyler
    mdata_dir = config["mdata_write_dir"]

    click.echo(
        {"funcx_online":compute_fn(funcx_eid, func_uuid)[0],
        "globus_online":data_fn(globus_eid), #, stage_dir, mdata_dir),
        "stage_dir":check_read_fn(stage_dir, funcx_eid),
        "mdata_dir":check_write_fn(mdata_dir, funcx_eid)})

# xtract-cli fetch containers --all (or –materials or –general)
@cli.group()
def fetch():
    pass

@fetch.command()
@click.option('--alls', is_flag=True)
@click.option('--materials', is_flag=True)
@click.option('--general', is_flag=True)
@click.option('--tika', is_flag=True)
@click.option('--name', required=True)
def containers(alls, materials, general, tika, name):
    if not (alls or materials or general or tika):
        click.echo("You must provide a container to fetch. Please select one of alls, materials, general, tika.")
        return

    # TODO: check endpoint is online before going through with the transfer
    # TODO: how do we get the endpoint name?
    try:
        # TODO: Remove hard coded lists
        f = open("/Users/joaovictor/test/config.json")
    except FileNotFoundError as error:
        click.echo("Configuration file not found.")
        return

    required = ["globus_eid", "funcx_eid", "local_download", "mdata_write_dir"]
    config = json.loads(f.read())
    for key in required:
        if key not in config:
            click.echo("required attribute not present")
            return

    # Hello World Function UUID
    func_uuid = "4b0b16ad-5570-4917-a531-9e8d73dbde56"

    # TODO: add stage_dir to config.json configuration?
    status = {
        "funcx_online":compute_fn(config["funcx_eid"], func_uuid)[0],
        "globus_online":data_fn(config["globus_eid"]), #, config["local_download"], config["mdata_write_dir"]),
        "stage_dir":check_read_fn(config["local_download"], config["funcx_eid"]),
        "mdata_dir":check_write_fn(config["local_download"], config["funcx_eid"])
        }

    for key, value in status.items():
        if not value:
            click.echo(f"{key} is not properly configured. Please try again.")
            return

    click.echo("Configuration is valid.")

    # Containers Endpoint ID
    source_endpoint_id = '4f99675c-ac1f-11ea-bee8-0e716405a293'
    destination_endpoint_id = config["globus_eid"]
    
    tdata = TransferData(tc, source_endpoint_id,
        destination_endpoint_id, label="SDK example", sync_level="checksum")

    all_list = ["xtract-c-code.img", "xtract-hdf.img", "xtract-images.img", "xtract-jsonxml.img",
    "xtract-keyword.img", "xtract-matio.img", "xtract-netcdf.img", "xtract-python.img", 
    "xtract-tabular.img", "xtract-tika.img", "xtract-xpcs.img"]
    tika_list = ["xtract-tika.img"]
    materials_list = ["xtract-matio.img"]
    general_list = [a for a in all_list if a != "xtract-matio.img"]

    chosen_list = None
    if materials: chosen_list = materials_list
    if general: chosen_list = general_list
    if materials and general: chosen_list = alls
    if alls: chosen_list = alls
    if tika: chosen_list = tika_list

    for filename in chosen_list:
        source = f"/XtractContainerLibrary/{filename}"
        destination = f"~/.xtract/.containers/{filename}" #TODO: change this to home/.xtract/.containers/name
        tdata.add_item(source, destination, recursive=False)

    transfer_result = tc.submit_transfer(tdata)
    click.echo(transfer_result)
