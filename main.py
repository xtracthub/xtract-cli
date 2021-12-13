import argparse
import pathlib
import os
import json
import subprocess

class UserOptions:
  def __init__(self):
    self.name = None
    self.globus_eid = None
    self.local_metadata = None
    self.metadata_write_dir = None

'''
Initialize.
'''
ops = UserOptions()
parser = argparse.ArgumentParser(prog='parser', 
                                 description='CLI tester for Xtract metadata extractors',
                                 epilog='Contact jvsr1 at uchicago dot edu for support')

'''
Parse options to setup test environment. Currently only a few options are
implemented: configure, globus_eid, funcx_eid, metadata_write_dir.
'''
parser.add_argument('configure'
                    action='store', dest='name', type=str)
parser.add_argument("-g", "--globus_eid", 
                    action="store", dest='globus_eid', type=str)
parser.add_argument("-l", "--local_metadata",
                    action="store", dest='local_metadata', type=str)
parser.add_argument("-m", "--metadata_write_dir", 
                    action="store", dest='metadata_write_dir', type=str)

'''
Quick test.
'''
parser.parse_known_args(namespace=ops)
print('vars(ops): ' + str(vars(ops)))