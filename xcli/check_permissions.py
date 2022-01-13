from funcx.sdk.client import (TaskPending, FuncXClient)

def check_read(path):
    import os
    return os.access(path, os.R_OK)

def check_write(path):
    import os
    return os.access(path, os.W_OK)

def check_execute(path):
    import os
    return os.access(path, os.X_OK)

fxc = FuncXClient(timeout=60)
check_read_uuid = fxc.register_function(check_read)
check_write_uuid = fxc.register_function(check_write)
check_execute_uuid = fxc.register_function(check_execute)

print(f'check_read_uuid: {check_read_uuid}')
print(f'check_write_uuid: {check_write_uuid}')
print(f'check_execute_uuid: {check_execute_uuid}')
