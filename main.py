import argparse
import pathlib
import os
import json
import subprocess
from funcx.sdk.client import FuncXClient
from globus_sdk import TransferClient

class UserOptions:
  def configure_ep(self):
    ''' Check that an endpoint name is provided.'''
    if self.configure is None:
      print ("Cannot create Xtract Endpoint -- no endpoint name provided.")
      return
    ''' Import the attributes from the json file. '''
    if os.path.isfile('~/{self.configure}/config.json'):
      data = None
      with open('~/{self.configure}/config.json') as f:
        data = json.loads(f.read())
        for key in data.keys():
          if hasattr (self, key):
            self.key = data[key]
    if not self.globus_eid:
      print("Cannot create Xtract Endpoint -- missing globus_eid")
      return
    if not self.local_metadata:
      print("Cannot create Xtract Endpoint -- missing local metadata")
      return
    if not self.metadata_write_dir:
      print("Cannot create Xtract Endpoint -- missing metadata write directory")
      return
    print ("Created Xtract Endpoint!")

  def __init__(self):
    self.configure = None
    self.globus_eid = None
    self.funcx_eid = None
    self.local_metadata = None
    self.metadata_write_dir = None

def is_online(ops:UserOptions):
  res = {}
  if ops.funcx_eid is None:
    res['funcx_eid'] = 'Funcx not present.'
  else:
    fxc = FuncXClient()
    data = fxc.run(endpoint_id=ops.funcx_eid)
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
print('vars(ops): ' + str(vars(ops)))

if args.is_online:
  res = is_online (ops)
  print ("is_online output: " + str(res))
if args.configure:
  ops.configure_ep()
if args.test_containers:
  print ('Call to test_containers happens here!')


# ops.configure_ep()

'''
Quick test.
'''
