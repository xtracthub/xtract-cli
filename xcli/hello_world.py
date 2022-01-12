from funcx.sdk.client import (TaskPending, FuncXClient)

def hello_world():
    return 'Hello World!'

fxc = FuncXClient(timeout=60)
hello_world_uuid = fxc.register_function(hello_world)
print(hello_world_uuid)