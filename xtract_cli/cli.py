import click
import mdf_toolbox
import os
import json

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
    