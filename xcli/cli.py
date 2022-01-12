import click
import mdf_toolbox
import os
import json
from funcx.sdk.client import (TaskPending, FuncXClient)
from time import sleep

DEBUG = False

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
)

# TODO: Create a timeout decorator
# TODO: Create overarching context from CLI with funcx client initialization

# Acquire the Globus TransferClient
tc = auths['transfer']

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

# probably would be nice to inherit a context here!
@test.command()
@click.option('--funcx_eid', default=None, required=True, help='Funcx Endpoint ID')
@click.option('--func_uuid', default=None, required=False, help='Function UUID')
def compute(funcx_eid, func_uuid):
    if not funcx_eid:
        click.echo('Error - Funcx Endpoint ID not provided.')
        return
    if not func_uuid:
        click.echo('Error - Function UUID not provided.')
        return

    funcx_response = fxc.run(endpoint_id=funcx_eid, function_id=func_uuid)
    click.echo(f'funcx_response: {funcx_response}')
    click.echo('sleeping for 5 seconds...')
    sleep(5)

    try:
        fxc_result = fxc.get_result(funcx_response)
    except TaskPending as error:
        click.echo(error)
    click.echo(f'fxc_result: {fxc_result}')
    

    # # # A timeout functionality could be wrapped within a python
    # # # decorator -- run this by Tyler, might be unecessary
    # timeout = 0
    # time_elapsed = 0
    # while time_elapsed < timeout:
    #     try:
    #         fxc_result = fxc.get_result(funcx_response)
    #     except TaskPending as error:
    #         click.echo(f"Task incomplete -- time elapsed: {time_elapsed}")
    #         sleep(5)
    #         time_elapsed += 5
    #         continue
    #     break

    # if fxc_result is not None and fxc_result == 'Hello World!':
    #     click.echo(f"Task complete -- result: {fxc_result}")
    #     return "OK"
    # elif fxc_result != 'Hello World!':
    #     click.echo(f"Error -- Expected: \'Hello World!\', but received: \'{fxc_result}\'")
    #     return "Failure"

