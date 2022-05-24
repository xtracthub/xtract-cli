from sys import stdout
from time import sleep
import click

def wait_for_fxc_ep(fxc, funcx_response, name, timeout=60, increment=2):
    fxc_task = fxc.get_task(funcx_response)
    time_elapsed = 0

    idx, iter_val = 0, [i for i in range(0, 6)]
    while time_elapsed < timeout:
        if fxc_task['pending'] is True:
            sleep(increment)
            print(f"Job '{name}' pending" + "." * iter_val[idx], end="\r")
            stdout.write("\033[K")
            idx = (idx + 1) % len(iter_val)
            time_elapsed += increment
            fxc_task = fxc.get_task(funcx_response)
        else:
            click.echo(" complete.")
            return True
    click.echo(f"Job '{name}' timed out after {time_elapsed} seconds.")
    return False

def user_loading_screen(tc, tdata):
    response = tc.submit_transfer(tdata)
    task_id = response["task_id"]
    task = tc.get_task(task_id)

    if task["completion_time"]:
        click.echo("Task complete.")
        transferred = task["bytes_transferred"]
        rate = task["effective_bytes_per_second"]
        click.echo(f"Transferred {transferred} bytes at {rate} bytes/second.")
        return

    increment = 0.5
    cur_val, iter_val = 0, [i for i in range(0, 6)]
    while task["files"] == 0:
        sleep(increment)
        cur_val = (cur_val + 1) % len(iter_val)
        stdout.write("\033[K")
        print(f"Task pending" + "." * iter_val[cur_val], end="\r")
        task = tc.get_task(task_id)
    stdout.write("\033[K")
    print("Task is now ready.")

    total = task["files"]
    succeeded = task["files_transferred"]

    print(f"Transferring {total} file(s).")

    cur_val, iter_val = 0, [i for i in range(0, 6)]
    while not task["completion_time"]:
        """ Update the number of files that have been
            transferred so far. """
        if succeeded < task["files_transferred"]:
            total = task["files"]
            succeeded = task["files_transferred"]
            print(f"Transferred {succeeded} out of {total}", end="\r")
            stdout.write("\033[K")
            sleep(5)

        """ Main loop: update task by making call to
            Globus API, print nice progress dots to
            let user know program hasn't crashed.
        """
        sleep(increment)
        cur_val = (cur_val + 1) % len(iter_val)
        print(f"Transferring" + "." * iter_val[cur_val], end="\r")
        stdout.write("\033[K")
        task = tc.get_task(task_id)
        total = task["files"]
        succeeded = task["files_transferred"]
    click.echo("Transfer complete.")
    if task["status"] != "SUCCEEDED":
        click.echo("Task failed.")
        return False
    transferred = task["bytes_transferred"]
    rate = task["effective_bytes_per_second"]
    click.echo(f"Transfer Rate: {rate} bytes/second ({total} byte(s)).")
    return
