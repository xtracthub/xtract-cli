import os, pathlib, json, click, mdf_toolbox
from funcx.sdk.client import (TaskPending, FuncXClient)
from globus_sdk import (TransferAPIError, TransferData)
from time import sleep


DEBUG = False
APP_NAME = "Xtract CLI"
CLIENT_ID = "7561d66f-3bd3-496d-9a29-ed9d7757d1f2"


def validate_config_file():
    pass


def wait_for_fxc_ep(fxc, funcx_response, name, timeout=60, increment=2):
    fxc_task = fxc.get_task(funcx_response)
    time_elapsed = 0
    click.echo(f"'{name}' pending...", nl=False)
    while time_elapsed < timeout:
        if fxc_task['pending'] is True:
            sleep(increment)
            click.echo(f"." * increment, nl=False)
            time_elapsed += increment
            fxc_task = fxc.get_task(funcx_response)
        else:
            click.echo(" complete.")
            return True
    click.echo(f" '{name}' timed out after {time_elapsed} seconds.")
    return False


# Acquire authentication via mdf_toolbox
click.echo("Authentication in progress...", nl=False)
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
click.echo(" complete.")

# TODO: Create a timeout decorator
# TODO: Create overarching context from CLI with funcx client initialization
# TODO: Separate functions into modules (inward facing, outward facing)

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
        "ep_name": ep_name,
        "globus_eid": globus_eid,
        "funcx_eid": funcx_eid,
        "local_download": os.path.expanduser(local_download), #expand user to make workable directories
        "mdata_write_dir": os.path.expanduser(mdata_write_dir),
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
    increment=1
    if not wait_for_fxc_ep(fxc, funcx_response, "test compute", timeout, increment):
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
        click.echo(f'Error: {error.code}, {error.message}')
        return
    if endpoint["is_globus_connect"]:
        return endpoint["gcp_connected"]
    else:
        return endpoint["DATA"][0]["is_connected"]


def check_read_fn(path, funcx_eid):
    fxc = FuncXClient()
    funcx_response = fxc.run(path, endpoint_id=funcx_eid, function_id="ab148dec-7f77-446f-81e4-934f58c3b472")
    timeout=10
    increment=1
    if not wait_for_fxc_ep(fxc, funcx_response, "check read permissions", timeout, increment):
        return (False, f'Error: Funcx timed out after {timeout} seconds')
    return fxc.get_result(funcx_response)


def check_write_fn(path, funcx_eid):
    fxc = FuncXClient()
    funcx_response = fxc.run(path, endpoint_id=funcx_eid, function_id="c1bcf355-fb42-4ad9-9f6c-994876d693e7")

    timeout=10
    increment=1

    if not wait_for_fxc_ep(fxc, funcx_response, "check write permissions", timeout, increment):
        return (False, f'Error: Funcx timed out after {timeout} seconds')
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

    try: 
        res = tc.operation_ls(endpoint_id=globus_eid, path=str(path_parent))
        array = res["DATA"]
    except Exception as e:
        click.echo(f'Error: {e.code}, {e.message}')
        return -1

    permissions = None
    for file in array:
        if file["name"] == folder:
            permissions = file["permissions"]
            break

    if not permissions:
        print(f"Directory {path} not found. Please run 'mkdir {path}' on the Globus Endpoint.")
        return -1
    
    def octal_to_string(octal):
        permission = ["---", "--x", "-w-", "-wx", "r--", "r-x", "rw-", "rwx"]
        result = []
        for idx, value in enumerate([int(n) for n in str(octal)]):
            if idx == 0: continue # skip the first value
            result.append({c for c in permission[value]})
        return result

    # TODO: experiment with permissions to see if this
    # strategy actually works the way we expect
    user, group, others = octal_to_string(permissions)
    if "r" in user or "r" in others:
        output['read'] = True
    if "w" in user or "w" in others:
        output['write'] = True
    if "x" in user or "x" in others:
        output['execute'] = True
    return output


# probably would be nice to inherit a context here! but not really necessary
@test.command()
@click.argument('ep_name')
def compute(ep_name):
    # Check whether configuration `ep_name` exists
    if not os.path.exists(os.path.expanduser(f"~/.xtract/{ep_name}/config.json")):
        click.echo(f"Endpoint {ep_name} does not exist! Run `xcli configure` first.")
        return

    f = open(os.path.expanduser(f"~/.xtract/{ep_name}/config.json"))
    config = json.loads(f.read())
    funcx_eid = config["funcx_eid"]
    func_uuid = "4b0b16ad-5570-4917-a531-9e8d73dbde56" # Hello World Function UUID

    click.echo({"funcx_online":compute_fn(funcx_eid, func_uuid)[0]})


@test.command()
@click.argument('ep_name')
def data(ep_name):
    # Check whether configuration `ep_name` exists
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
def is_online(ep_name):
    # Check whether configuration `ep_name` exists
    if not os.path.exists(os.path.expanduser(f"~/.xtract/{ep_name}/config.json")):
        click.echo(f"Endpoint {ep_name} does not exist! Run `xcli configure` first.")
        return

    f = open(os.path.expanduser(f"~/.xtract/{ep_name}/config.json"))
    config = json.loads(f.read())

    funcx_eid = config["funcx_eid"]
    func_uuid = "4b0b16ad-5570-4917-a531-9e8d73dbde56" # Hello World Function UUID
    globus_eid = config["globus_eid"]
    stage_dir = config["local_download"]
    mdata_dir = config["mdata_write_dir"]

    res = {"funcx_online":compute_fn(funcx_eid, func_uuid)[0],
        "globus_online":data_fn(globus_eid),
        "stage_dir":check_read_fn(stage_dir, funcx_eid),
        "mdata_dir":check_write_fn(mdata_dir, funcx_eid)}

    click.echo(res)
    if not res["stage_dir"] or not res["mdata_dir"]: 
        click.echo(f"Check read or write permissions failed. Please run `xcli test data {ep_name}` for more information.")


@cli.group()
def fetch():
    pass


@fetch.command()
@click.argument('ep_name')
@click.option('--alls', is_flag=True)
@click.option('--materials', is_flag=True)
@click.option('--general', is_flag=True)
@click.option('--tika', is_flag=True)
def containers(ep_name, alls, materials, general, tika):
    if not (alls or materials or general or tika):
        click.echo("You must provide a container to fetch. Please select one of alls, materials, general, tika.")
        return

    if not os.path.exists(os.path.expanduser(f"~/.xtract/{ep_name}/config.json")):
        click.echo(f"Endpoint {ep_name} does not exist! Run `xcli configure` first.")
        return
    f = open(os.path.expanduser(f"~/.xtract/{ep_name}/config.json"))
    config = json.loads(f.read())

    # Hello World Function UUID
    func_uuid = "4b0b16ad-5570-4917-a531-9e8d73dbde56"
    required = ["globus_eid", "funcx_eid", "local_download", "mdata_write_dir"]
    for key in required:
        if key not in config:
            click.echo("required attribute not present")
            return

    click.echo("Testing Xtract configuration.")

    status = {
        "funcx_online":compute_fn(config["funcx_eid"], func_uuid)[0],
        "globus_online":data_fn(config["globus_eid"]),
        "stage_dir":check_read_fn(config["local_download"], config["funcx_eid"]),
        "mdata_dir":check_write_fn(config["local_download"], config["funcx_eid"])}
    for key, value in status.items():
        if not value:
            click.echo(f"Faulty set up detected. Please run `xtract is-online {ep_name}` to diagnose.")
            return

    click.echo("Configuration is valid. Proceeding with Transfer.")

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
    if materials and general: chosen_list = all_list
    if alls: chosen_list = all_list
    if tika: chosen_list = tika_list

    for filename in chosen_list:
        source = f"/XtractContainerLibrary/{filename}"
        os.makedirs(os.path.dirname(os.path.expanduser(f"~/.xtract/.containers/")), exist_ok=True)
        destination = os.path.expanduser(f"~/.xtract/.containers/{filename}")
        tdata.add_item(source, destination, recursive=False)

    response = tc.submit_transfer(tdata)
    task_id = response["task_id"]
    task = tc.get_task(task_id)

    # Weird case? Just got the new task but it already exists and is complete? Could happen
    # for very small tasks I suppose,
    if task["completion_time"]:
        click.echo("Task complete.")
        transferred = task["bytes_transferred"]
        rate = task["effective_bytes_per_second"]
        click.echo(f"Transferred {transferred} bytes at {rate} bytes/second.")
        return

    increment = 1


    click.echo("Task pending...", nl=False)
    while task["files"] == 0:
        sleep(increment)
        click.echo(f"." * increment, nl=False)
        task = tc.get_task(task_id)
        
    total = task["files"]
    succeeded = task["files_transferred"] 

    click.echo()
    click.echo(f"Transferred {succeeded} out of {total}...", nl=False)
    while not task["completion_time"]:
        if succeeded < task["files_transferred"]:
            total = task["files"]
            succeeded = task["files_transferred"] 
            click.echo()
            click.echo(f"Transferred {succeeded} out of {total}...", nl=False)
        sleep(increment)
        click.echo(f"." * increment, nl=False)
        task = tc.get_task(task_id)
        total = task["files"]
        succeeded = task["files_transferred"] 
    click.echo(" transfer complete.")

    if task["status"] != "SUCCEEDED":
        click.echo("Task failed.")
        return False

    transferred = task["bytes_transferred"]
    rate = task["effective_bytes_per_second"]
    click.echo(f"Transferred {transferred} bytes at {rate} bytes/second.")
    return True
