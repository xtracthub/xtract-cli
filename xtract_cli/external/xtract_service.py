import requests

def config_containers(payload):
    """
    Function to handle interfacing with Xtract Service
    and register an Xtract container deployment
    """
    return requests.post('http://127.0.0.1:5000/config_containers', json=payload)
