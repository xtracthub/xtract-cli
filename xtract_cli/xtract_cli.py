import json
import os, pathlib
import click
import psycopg2, psycopg2.errorcodes

from fileinput import filename
from time import sleep

import mdf_toolbox
from funcx.sdk.client import FuncXClient
from globus_sdk import TransferAPIError, TransferData
from xtract_cli.external.xtract_service import config_containers

# DEBUG
DEBUG = False
APP_NAME = "Xtract CLI"
CLIENT_ID = "7561d66f-3bd3-496d-9a29-ed9d7757d1f2"

# UUID
HELLO_WORLD_UUID = "91e5a8db-e7b3-4d28-a3ea-81f44d1d75bf"
HELLO_WORLD_EXPECTED = "Hello World!"
CHECK_READ_UUID = "80b17dc9-e0bd-439c-9bd4-741a1b6839f0"
CHECK_WRITE_UUID = "18e44258-1356-4f35-9713-aa3de2b2abaa"
CHECK_EXEC_UUID = "22513088-840a-426e-83f4-fd4a70c7199c"
PETREL_XTRACT_EID = "4f99675c-ac1f-11ea-bee8-0e716405a293"
CONTAINER_STORE_EID = "939cc587-f18d-4209-8676-3173bb7b9321"

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

def user_loading_screen(tdata):
    response = tc.submit_transfer(tdata)
    task_id = response["task_id"]
    task = tc.get_task(task_id)
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
    return

def db_insert_entry(file_name, dest_globus_eid, file_path, source_globus_eid, source_ep_name):
    sql = """INSERT INTO container_to_endpoint(container_name, globus_eid, path, source_eid, source_name) VALUES (%s, %s, %s, %s, %s);"""
    db_pass = os.getenv("xtractdb_pass")
    db_conn = psycopg2.connect(f"dbname='xtractdb' user='xtract' host='xtractdb.c80kmwegdwta.us-east-1.rds.amazonaws.com' password='{db_pass}'")
    cur = db_conn.cursor()
    try:
        cur.execute(sql, (file_name, dest_globus_eid, file_path, source_globus_eid, source_ep_name))
    except psycopg2.errors.lookup(psycopg2.errorcodes.UNIQUE_VIOLATION) as e:
        print("Image already exists. Please provide a new image.")
        return False
    return True

def db_get_entry():
    sql = """SELECT container_name, path FROM container_to_endpoint;"""
    db_pass = os.getenv("xtractdb_pass")
    db_conn = psycopg2.connect(f"dbname='xtractdb' user='xtract' host='xtractdb.c80kmwegdwta.us-east-1.rds.amazonaws.com' password='{db_pass}'")
    cur = db_conn.cursor()
    cur.execute(sql)
    res = cur.fetchall()
    cur.close()
    db_conn.close()
    return res

def authenticate():
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
    )
    click.echo(" complete.")

    # TODO: Create overarching context from CLI with funcx client initialization
    # TODO: Separate functions into modules (inward facing, outward facing)
    # print(auths['openid'].get_authorization_header())
    # Acquire the Globus TransferClient
    # print(auths)
    # tc = auths['transfer']
    # exit()
    # return tc
    return auths


auths = authenticate()
tc = auths["transfer"]

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
    """Configures Xtract instance by storing endpoing IDs and directories to
    save files to on the current machine. The configuration file is stored as
    a json file in the directory '~/.xtract/{ep_name}/config.json'.

    Args:
        ep_name (str): endpoint configuration name
        globus_eid (str): Globus Endpoint ID (for data transfers)
        funcx_eid (str): Funcx Endpoint ID (for computing)
        local_download (str): directory where downloads are stored
        mdata_write_dir (str): directory metadata gets written to
    """
    config = {
        "ep_name": ep_name,
        "globus_eid": globus_eid,
        "funcx_eid": funcx_eid,
        "local_download": os.path.expanduser(local_download),
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


def compute_fn(funcx_eid, func_uuid, expected, timeout=10, increment=1):
    """Test whether a Funcx endpoint with Endpoint ID `funcx_eid` is online.

    Args:
        funcx_eid (str): Funcx Endpoint ID (for computing).

    Returns:
        (bool, str): The boolean in the tuple is True if the Funcx endpoint is
        online, otherwise False. The string contains simple debugging
        information.
    """
    fxc = FuncXClient()
    funcx_response = fxc.run(endpoint_id=funcx_eid, function_id=func_uuid)

    if not wait_for_fxc_ep(fxc, funcx_response, "test compute", timeout, increment):
        return (False, f'Funcx timed out after {timeout} seconds')
    fxc_result = fxc.get_result(funcx_response)
    if fxc_result is not None and fxc_result == expected:
        return (True, f"Task returned correct result.")
    elif fxc_result != expected:
        return (False, f"Task returned incorrect result. Expected: \'{expected}\', but received: \'{fxc_result}\'")


def data_fn(globus_eid):
    """Test whether a Globus endpoint with Endpoint ID `globus_eid` is online.

    Args:
        globus_eid (str): Endpoint ID associated with a Globus endpoint.

    Returns:
        bool: True if Globus endpoint is online, False otherwise.
    """
    try:
        endpoint = tc.get_endpoint(globus_eid)
    except TransferAPIError as error:
        click.echo(f"Transfer API Error: {error.code}, {error.message}")
        return
    except Exception as error:
        click.echo(f"Unexpected Error: {error}")



    if endpoint["is_globus_connect"]:
        return endpoint["gcp_connected"]
    else:
        return endpoint["DATA"][0]["is_connected"]


def check_read_fn(path, funcx_eid):
    """Check read permissions at `path` on a Funcx endpoint.

    Args:
        path (str): relative path to be checked on endpoint.
        funcx_eid (str): endpoint ID associated with a Funcx endpoint

    Returns:
        (bool, str): True if successful, False otherwise. Debugging message is
        contained in the string.
    """
    fxc = FuncXClient()
    funcx_response = fxc.run(path, endpoint_id=funcx_eid, function_id="80b17dc9-e0bd-439c-9bd4-741a1b6839f0")
    timeout=10
    increment=1
    if not wait_for_fxc_ep(fxc, funcx_response, "check read permissions", timeout, increment):
        return (False, f'Error: Funcx timed out after {timeout} seconds')
    return fxc.get_result(funcx_response)


def check_write_fn(path, funcx_eid):
    """Check write permissions at `path` on a Funcx endpoint.

    Args:
        path (str): relative path to be checked on endpoint.
        funcx_eid (str): endpoint ID associated with a Funcx endpoint

    Returns:
        (bool, str): True if successful, False otherwise. Debugging message is
        contained in the string.
    """
    fxc = FuncXClient()
    funcx_response = fxc.run(path, endpoint_id=funcx_eid, function_id="18e44258-1356-4f35-9713-aa3de2b2abaa")

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
    func_uuid = HELLO_WORLD_UUID
    expected = HELLO_WORLD_EXPECTED

    click.echo({"funcx_online":compute_fn(funcx_eid, func_uuid, func_uuid)[0]})


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
    stage_dir = config["local_download"]
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
def all(ep_name):
    # Check whether configuration `ep_name` exists
    if not os.path.exists(os.path.expanduser(f"~/.xtract/{ep_name}/config.json")):
        click.echo(f"Endpoint {ep_name} does not exist! Run `xcli configure` first.")
        return

    f = open(os.path.expanduser(f"~/.xtract/{ep_name}/config.json"))
    config = json.loads(f.read())

    funcx_eid = config["funcx_eid"]
    func_uuid = HELLO_WORLD_UUID
    expected = HELLO_WORLD_EXPECTED
    globus_eid = config["globus_eid"]
    stage_dir = config["local_download"]
    mdata_dir = config["mdata_write_dir"]

    res = {"funcx_online":compute_fn(funcx_eid, func_uuid, expected)[0],
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
    """Fetch containers from Globus endpoint and store on Funcx endpoint.
    Endpoint IDs are fetched from the configuration file.

    Args:
        ep_name (str): Endpoint to receive fetched containers
        alls (bool): True if all containers to be fetched.
        materials (bool): True if material containers to be fetched.
        general (bool): True if general containers to be fetched.
        tika (bool): True if tika containers to be fetched.

    Returns:
        bool: True if task succesful, False otherwise.
    """
    if not (alls or materials or general or tika):
        click.echo("You must provide a container to fetch. Please select one of alls, materials, general, tika.")
        return

    if not os.path.exists(os.path.expanduser(f"~/.xtract/{ep_name}/config.json")):
        click.echo(f"Endpoint {ep_name} does not exist! Run `xcli configure` first.")
        return
    f = open(os.path.expanduser(f"~/.xtract/{ep_name}/config.json"))
    config = json.loads(f.read())

    func_uuid = HELLO_WORLD_UUID
    expected = HELLO_WORLD_EXPECTED
    required = ["globus_eid", "funcx_eid", "local_download", "mdata_write_dir"]
    for key in required:
        if key not in config:
            click.echo("required attribute not present")
            return

    click.echo("Testing Xtract configuration.")

    status = {
        "funcx_online":compute_fn(config["funcx_eid"], func_uuid, expected)[0],
        "globus_online":data_fn(config["globus_eid"]),
        "stage_dir":check_read_fn(config["local_download"], config["funcx_eid"]),
        "mdata_dir":check_write_fn(config["local_download"], config["funcx_eid"])}
    for key, value in status.items():
        if not value:
            click.echo(f"Faulty set up detected. Please run `xtract all {ep_name}` to diagnose.")
            return

    click.echo("Configuration is valid. Proceeding with Transfer.")

    source_endpoint_id = PETREL_XTRACT_EID
    destination_endpoint_id = config["globus_eid"]

    tdata = TransferData(tc, source_endpoint_id,
        destination_endpoint_id, label="SDK example", sync_level="checksum")

    all_list = ["xtract-c-code.img", "xtract-hdf.img", "xtract-images.img", "xtract-jsonxml.img",
    "xtract-keyword.img", "xtract-matio.img", "xtract-netcdf.img", "xtract-python.img", 
    "xtract-tabular.img", "xtract-tika.img", "xtract-xpcs.img"]
    tika_list = ["xtract-tika.img",]
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
        print(task)
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


@cli.group()
def transfer():
    pass

@transfer.command()
@click.argument('ep_name')
@click.argument('file_path')
def upload(ep_name, file_path):
    file_name = (file_path.split("/")[-1]).split(".")[0]

    """ os.getcwd() is actually the location of the setup.py script, which
    tells the interpreter where the program actually starts. """
    with open(os.path.join(os.getcwd(), "xtract_cli/endpoint_config/eagle_container.json")) as f:
        dest = json.loads(f.read())
    with open(os.path.expanduser(f"~/.xtract/{ep_name}/config.json")) as f:
        source = json.loads(f.read())

    # check for liveness
    _ = {"globus_online":data_fn(dest["globus_eid"])}

    funcx_scope = "https://auth.globus.org/scopes/facd7ccc-c5f4-42aa-916b-a0e270e2c2a9/all"
    fx_headers = {'Authorization': auths[funcx_scope].access_token,
                'Search': auths['search'].authorizer.access_token,
                'Openid': auths['openid'].access_token}

    payload = {
            "ep_name": source["ep_name"],
            "fx_eid": source["funcx_eid"],
            "globus_eid": source["globus_eid"],
            "container_path": os.path.dirname(file_path),
            "headers": fx_headers,
            }

    import pprint
    pprint.pp(payload)

    config_res = config_containers(payload)
    db_res = db_insert_entry(file_name, dest["globus_eid"], file_path, source["globus_eid"], source["ep_name"])
    if not db_res:
        exit()
    
    source_fp = file_path
    dest_fp = f"/containers/{filename}.img"
    tdata = TransferData(tc, source["globus_eid"], dest["globus_eid"], label="SDK example", sync_level="checksum")
    tdata.add_item(source_fp, dest_fp)
    user_loading_screen(tdata)
    return True

@transfer.command()
def get_images():
    with open(os.path.join(os.getcwd(), "endpoint_config/eagle_container.json")) as f:
        dest = json.loads(f.read())
    _ = {"globus_online":data_fn(dest["globus_eid"])}
    res = db_get_entry()
    print("Available Images:")
    for idx, r in enumerate(res):
        print("\t" + str(idx) + ", " + str(r[0]))

@transfer.command()
@click.argument('ep_name')
@click.argument('image_name')
def download(ep_name, image_name):
    with open(os.path.join(os.getcwd(), "xtract_cli/endpoint_config/eagle_container.json")) as f:
        dest = json.loads(f.read())
    with open(os.path.expanduser(f"~/.xtract/{ep_name}/config.json")) as f:
        source = json.loads(f.read())
    status = {"globus_online":data_fn(dest["globus_eid"])}
    tdata = TransferData(tc, dest["globus_eid"], source["globus_eid"], label="SDK example", sync_level="checksum")

    source = f"/containers/{image_name}.img"
    os.makedirs(os.path.dirname(os.path.expanduser(f"~/.xtract/.containers/")), exist_ok=True)
    dest = os.path.expanduser(f"~/.xtract/.containers/{filename}")
    tdata.add_item(source, dest, recursive=False)

    response = tc.submit_transfer(tdata)
    task_id = response["task_id"]
    task = tc.get_task(task_id)
    if task["completion_time"]:
        click.echo("Task complete.")
        transferred = task["bytes_transferred"]
        rate = task["effective_bytes_per_second"]
        click.echo(f"Transferred {transferred} bytes at {rate} bytes/second.")
        return

    user_loading_screen(tdata)
    return True
