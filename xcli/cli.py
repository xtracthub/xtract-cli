import click
from funcx.utils.errors import FuncXUnreachable
import mdf_toolbox
import os
import json
from funcx.sdk.client import (TaskPending, FuncXClient)
from globus_sdk import (TransferAPIError)
from time import sleep

DEBUG = False
APP_NAME = "Xtract CLI"
CLIENT_ID = "7561d66f-3bd3-496d-9a29-ed9d7757d1f2"

def wait_for_ep(fxc, funcx_response, timeout=60, increment=2):
    fxc_task = fxc.get_task(funcx_response)
    time_elapsed = 0
    while time_elapsed < timeout:
        if fxc_task['pending'] is True:
            sleep(increment)
            time_elapsed += increment
            fxc_task = fxc.get_task(funcx_response)
        else:
            return True
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
    no_browser=False,
    no_local_server=False,
    clear_old_tokens=True # learn more about Globus' oauth system and improve this.
)

# TODO: Create a timeout decorator
# TODO: Create overarching context from CLI with funcx client initialization
# TODO: Separate functions into modules (inward facing, outward facing)

# Acquire the Globus TransferClient
tc = auths['transfer']
# click.echo(vars(tc))

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
        'local_download': local_download,
        'mdata_write_dir': mdata_write_dir,
    }
    config_json = json.dumps(config)
    with open(os.path.expanduser(f'~/{ep_name}/config.json'), 'w') as f:
        f.write(config_json)
    click.echo('Successfully configured Xtract endpoint!')

@cli.group()
def test():
    pass

def compute_fn(funcx_eid, func_uuid):
    fxc = FuncXClient()
    funcx_response = fxc.run(endpoint_id=funcx_eid, function_id=func_uuid)

    timeout=5
    increment=1

    if not wait_for_ep(fxc, funcx_response, timeout, increment):
        return (False, f'Error -- Funcx timed out after {timeout} seconds')

    fxc_result = fxc.get_result(funcx_response)
    if fxc_result is not None and fxc_result == 'Hello World!':
        return (True, "Task complete -- result: {fxc_result}")
    elif fxc_result != 'Hello World!':
        return (False, f"Error -- Expected: \'Hello World!\', but received: \'{fxc_result}\'")

def data_fn(globus_eid, stage_dir, mdata_dir):
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

    timeout=5
    increment=1

    if not wait_for_ep(fxc, funcx_response, timeout, increment):
        return (False, f'Error -- Funcx timed out after {timeout} seconds')
    # error checking here?
    return fxc.get_result(funcx_response)

def check_write_fn(path, funcx_eid):
    fxc = FuncXClient()
    funcx_response = fxc.run(path, endpoint_id=funcx_eid, function_id="c1bcf355-fb42-4ad9-9f6c-994876d693e7")

    timeout=5
    increment=1

    if not wait_for_ep(fxc, funcx_response, timeout, increment):
        return (False, f'Error -- Funcx timed out after {timeout} seconds')
    # error checking here?
    return fxc.get_result(funcx_response)

# probably would be nice to inherit a context here!
@test.command()
@click.option('--funcx_eid', default=None, required=True, help='Funcx Endpoint ID')
@click.option('--func_uuid', default=None, required=True, help='Function UUID')
def compute(funcx_eid, func_uuid):
    res = compute_fn(funcx_eid, func_uuid)
    click.echo(
        {"funcx_online":compute_fn(funcx_eid, func_uuid)[0]})

@test.command()
@click.option('--globus_eid', default=None, required=True, help='Globus Endpoint ID')
@click.option('--stage_dir', default=None, required=True)
@click.option('--mdata_dir', default=None, required=True)
def data(globus_eid, stage_dir, mdata_dir):
    click.echo(
        {"globus_online":data_fn(globus_eid, stage_dir, mdata_dir),
        "stage_dir":None,
        "mdata_dir":None})
    
@test.command()
@click.option('--funcx_eid', default=None, required=True, help='Funcx Endpoint ID')
@click.option('--func_uuid', default=None, required=True, help='Function UUID')
@click.option('--globus_eid', default=None, required=False, help='Globus Endpoint ID')
@click.option('--stage_dir', default=None, required=False)
@click.option('--mdata_dir', default=None, required=False)
def is_online(funcx_eid, func_uuid, globus_eid, stage_dir, mdata_dir):
    click.echo(
        {"funcx_online":compute_fn(funcx_eid, func_uuid)[0],
        "globus_online":data_fn(globus_eid, stage_dir, mdata_dir),
        "stage_dir":check_read_fn(stage_dir, funcx_eid),
        "mdata_dir":check_write_fn(mdata_dir, funcx_eid)})