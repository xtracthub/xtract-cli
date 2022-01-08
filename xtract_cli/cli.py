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
@click.option('--globus_eid', default=None, help='Globus Endpoint ID')
@click.option('--funcx_eid', default=None, help='Funcx Endpoint ID')
@click.option('--local_download', default=None, help='Local download')
@click.option('--mdata_write_dir', default=None, help='Metadata write directory')
def configure(ep_name, globus_eid, funcx_eid, local_download, mdata_write_dir):
    missing = []
    if not globus_eid: 
        missing.append('globus_eid')
    if not local_download: 
        missing.append('local_download')
    if not mdata_write_dir: 
        missing.append('mdata_write_dir')
    if not funcx_eid: 
        missing.append('funcx_eid')

    if len(missing) > 0:
        print('Error - cannot configure Xtract endpoint. Missing config values: ')
        print(*missing, sep=', ')
        return

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

    print ("Successfully configured Xtract endpoint!")


@cli.group()
def test():
    pass

# probably would be nice to inherit a context here!
@test.command()
@click.option('--funcx_eid', default=None, required=True, help='Funcx Endpoint ID')
@click.option('--func_uuid', default=None, required=False, help='Function UUID')
def compute(funcx_eid, func_uuid):
    # Move to an inherited context!
    def hello_world():
        return 'Hello World!'
    def sleep_30():
        from time import sleep
        sleep(30)
        return 'Woke up after 30 seconds'
    fxc = FuncXClient(timeout=60)
    hello_world_uuid = fxc.register_function(hello_world)
    sleep_30_uuid = fxc.register_function(sleep_30)

    funcx_response = fxc.run(endpoint_id=funcx_eid, function_id=hello_world_uuid)
    fxc_result = None

    if not funcx_eid:
        return "Error - Funcx Endpoint ID not provided."
    if not func_uuid:
        func_uuid = hello_world_uuid

    # # A timeout functionality could be wrapped within a python
    # # decorator -- run this by Tyler, might be unecessary
    # timeout = 0
    # time_elapsed = 0
    # while time_elapsed < timeout:
    #     try:
    #         fxc_result = fxc.get_result(funcx_response)
    #     except TaskPending as error:
    #         # could inheret a debug context!!!
    #         if DEBUG: print(f"Task incomplete -- time elapsed: {time_elapsed}")
    #         sleep(5)
    #         time_elapsed += 5
    #         if DEBUG: print(f"About to continue to next!")
    #         continue
    #     if DEBUG: print(f"About to call break and get out!")
    #     break
    # if fxc_result is not None and fxc_result == 'Hello World!':
    #     if DEBUG: print (f"Task complete -- result: {fxc_result}")
    #     return "OK"
    # if fxc_result is None:
    #     return f"{error.reason}"
    # elif fxc_result != 'Hello World!':
    #     return f"Error -- Expected: \'Hello World!\', but received: \'{fxc_result}\'"

    click.echo('nice')