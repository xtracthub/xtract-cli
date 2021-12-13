import argparse
import pathlib
import os
import json
import subprocess

class UserOptions:
  def load_config(self):
    '''
    Load defaulted options here. There is a choice to be made about where
      (1) a server somewhere
      (2) the repository of a particular extractor (if we don't find it simply
          default to no options, and then leave it up to the user to actually
          fill in the information they need)
      (3) the repository of xtract_cli (this would be very annoying to
          maintain, and probably not a good use of time)
    '''
    if self.load_config_path is None or not os.path.isfile(self.load_config_path):
      return
    data = None
    with open(self.load_config_path) as f:
      data = json.loads(f.read())
    for key in data.keys():
      if hasattr (self, key):
        self.key = data[key]

  def run_test(self):
    try:
      self.ep_path = "/Users/joaovictor/xtract/xtract-service/tests/event_tests/hdf_tests.py"
      process = subprocess.run(['python', self.ep_path], capture_output=True, text=True)
      print (process.stderr)
    except:
      print('Error: unable to run metadata extractor as subprocess.')
      return
  
  def __init__(self):
    self.mode = None
    self.load_config_path = None
    self.save_config_path = None

    ''' Test options '''
    self.ep_path = None
    self.write_path = None

    """ 
    Future additions: 
    self.xtract_dir = None
    self.sys_path_add = None
    self.module_path = None
    self.metadata_write_path = None
    self.base_path = None
    self.default_config = None
    self.verbose = False
    self.test_paths = None
    self.expected_paths = None
    call load defaults!
    """
    self.load_config()
    self.run_test()

ops = UserOptions()
parser = argparse.ArgumentParser(prog='parser', 
                                 description='CLI tester for Xtract metadata extractors',
                                 epilog='Contact jvsr1 at uchicago dot edu for support')

'''
General setup: 
  -- populate defaults given '--xtractor' option, but also allow user to
     overwrite previously loaded in paths as needed.
  -- pass options to event_basetry:
        process = subprocess.run(
            ['pycodestyle', file_path], capture_output=True, text=True)
        for _, line, char, descrip in re.findall("(.*):(.*):(.*): (.*)", process.stdout):
            issue = {"line": line, "char": char, "description": descrip}
            issues.append(issue)
    except:
        print('Error: unable to run pycodestyle as subprocess.')
        returnd options after pulling down hosted extractors
  -- write statistics to desired directory
  -- allow the user to select their chosen test suite (?)

  -- allow metadata extractor to accept different types of files as input
     example: directory vs single file
  -- auxiliary data? Probably not necessary
'''

'''
Parse options to setup test environment.
'''
# parser.add_argument("-lc", "--load_config", 
#                     help="Load a testing configuration. If no testing configuration is\
#                       provided, the testing suite will be set to its default values.",
#                     action="store", dest='load_config_path', type=pathlib.Path)
# parser.add_argument("-sc", "--save_config", 
#                     help="Save a testing configuration. If no testing configuration is\
#                       provided, the testing suite will be set to its default values.",
#                     action="store", dest='save_config_path', type=pathlib.Path)
# parser.add_argument("-m", "--mode", 
#                     help="Mode to run the Xtract testing suite -- basic, full, single.\
#                       If neither the user inputs neither basic nor full, the parser will\
#                       interpret the given input as the name of a single test.",
#                     action="store", type=str)

'''
Parse options passed to test file.
'''
# parser.add_argument("-en", "--ep_name", help="set name of endpoint",
#                     action="store", type=str)
# parser.add_argument("-xd", "--xtract_dir", help="set xtractor's default directory",
#                     action="store", type=pathlib.Path)
# parser.add_argument("-spa", "--sys_path_add", help="add system path",
#                     action="store", type=pathlib.Path)
# parser.add_argument("-mp", "--module_path", help="set xtractor's module path",
#                     action="store", type=pathlib.Path)
# parser.add_argument("-mwp", "--module_write_path", help="set xtractor's module write path",
#                     action="store", type=pathlib.Path)
# parser.add_argument("-bp", "--base_path", help="set xtractor's base path",
#                     action="store", type=pathlib.Path)

'''
Parse miscellaneous options.
'''
# parser.add_argument("-v", "--verbose", help="increase output verbosity",
#                     action="store_true")

# args = parser.parse_args(namespace=ops)




'''
Parse user options and store them in the UserOptions class.
'''

'''
Spawn subprocess, read the results, and then simply place them in a file
'''
# parser.parse_known_args(namespace=ops)
# print('vars(ops): ' + str(vars(ops)))


