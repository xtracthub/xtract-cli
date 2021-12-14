import argparse
import pathlib
import os
import json
import subprocess

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

def is_online():
  pass

def test_containers():
  pass

'''
Initialize.
'''
fn_map = {'is_online':is_online,
          'test_containers':test_containers}
ops = UserOptions()
parser = argparse.ArgumentParser(prog='parser', 
                                 description='CLI tester for Xtract metadata extractors',
                                 epilog='Contact jvsr1 \{at\} uchicago \{dot\} edu for support')

'''
Parse options to setup test environment. Currently only a few options are
implemented: configure, globus_eid, funcx_eid, local_metadata, and metadata_write_dir.
'''
parser.add_argument('configure',
                    action='store', type=str)
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
parser.parse_known_args(namespace=ops)
ops.configure_ep()

'''
Quick test.
'''
print('vars(ops): ' + str(vars(ops)))