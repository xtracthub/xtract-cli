import argparse
import pathlib
import os
import json
import subprocess
import uuid
from funcx.sdk.client import FuncXClient
from globus_sdk import TransferClient
import globus_sdk

DEBUG = False

class UserOptions:
  def configure_ep(self):
    if self.configure is None:
      print ("Cannot create Xtract Endpoint -- no endpoint name provided.")
      return False
    if os.path.isfile("/Users/joaovictor/" + self.configure +  "/config.json"):
      print ("Found config file in /Users/joaovictor/" + self.configure +  "/config.json") 
      data = None
      with open("/Users/joaovictor/" + self.configure +  "/config.json") as f:
        data = json.loads(f.read())
        for key in data.keys():
          if DEBUG: print (key, data[key])
          if hasattr (self, key):
            self.key = data[key]
    else:
      print ("No config file found or provided.")
    if not self.globus_eid:
      print("Cannot create Xtract Endpoint -- missing globus_eid")
      return False
    if not self.local_metadata:
      print("Cannot create Xtract Endpoint -- missing local metadata")
      return False
    if not self.metadata_write_dir:
      print("Cannot create Xtract Endpoint -- missing metadata write directory")
      return False
    print ("Created Xtract Endpoint!")
    return True

  def authenticate(self):
    CLIENT_ID = "3b1925c0-a87b-452b-a492-2c9921d3bd14"
    SCOPES = "openid profile email urn:globus:auth:scope:transfer.api.globus.org:all urn:globus:auth:scope:auth.globus.org:view_identities"
    native_auth_client = globus_sdk.NativeAppAuthClient(CLIENT_ID)
    native_auth_client.oauth2_start_flow(requested_scopes=SCOPES)
    print(f"Login Here:\n\n{native_auth_client.oauth2_get_authorize_url()}")
    auth_code = "yJfE8dI2Z5Skv5u9dDLEpiHuRjzoSk"
    token_response = native_auth_client.oauth2_exchange_code_for_tokens(auth_code)
    transfer_access_token = token_response.by_resource_server['transfer.api.globus.org']['access_token']
    transfer_authorizer = globus_sdk.AccessTokenAuthorizer(transfer_access_token)
    tc = globus_sdk.TransferClient(authorizer=transfer_authorizer)
    return

  def __init__(self):
    self.configure = None
    self.globus_eid = None
    self.funcx_eid = None
    self.local_metadata = None
    self.metadata_write_dir = None
    self.authenticate()

def is_online(ops:UserOptions):
  res = {}
  if ops.funcx_eid is None:
    res['funcx_eid'] = 'Funcx not present.'
  else:
    fxc = FuncXClient()
    data = fxc.run(endpoint_id=ops.funcx_eid, )
    res['funcx_eid'] = data
    
  if ops.globus_eid is None:
    res['globus_eid'] = 'Globus not present.'
  else:
    tc = TransferClient(authorizer=None)
    endpoint = tc.get_endpoint(ops.globus_eid)
    if endpoint is not None:
      res['globus_eid'] = 'Globus endpoint is present.'
  return res




def test_containers(ops):
  pass

'''
Initialize.
'''
ops = UserOptions()
parser = argparse.ArgumentParser(prog='parser', 
                                 description='CLI tester for Xtract metadata extractors',
                                 epilog='Contact jvsr1 \{at\} uchicago \{dot\} edu for support')

'''
Parse options to setup test environment. Currently only a few options are
implemented: configure, globus_eid, funcx_eid, local_metadata, and metadata_write_dir.
'''
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--is_online', action='store', type=str)
group.add_argument('--test_containers', action='store', type=str)
group.add_argument('--configure', action='store', type=str)

'''
Additional arguments for the configure argument.
'''
parser.add_argument("-g", "--globus_eid", 
                    action="store", dest='globus_eid', type=str)
parser.add_argument("-f", "--funcx_eid", 
                    action="store", dest='funcx_eid', type=str)                 
parser.add_argument("-l", "--local_metadata",
                    action="store", dest='local_metadata', type=str)
parser.add_argument("-m", "--metadata_write_dir", 
                    action="store", dest='metadata_write_dir', type=str)

'''
Call the configuration function after user options are loaded.
'''
args = parser.parse_args(namespace=ops)
if DEBUG: print('vars(ops): ' + str(vars(ops)))

if args.is_online:
  res = is_online (ops)
  print ("is_online output: " + str(res))
if args.configure:
  ops.configure_ep()
if args.test_containers:
  print ('Call to test_containers happens here!')
