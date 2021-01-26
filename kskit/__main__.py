import sys
import argparse
from . import java 
from . import password 
from . import voo 



def main():
  # Base argument parser
  parsers = {}
  parser = argparse.ArgumentParser()
  subs = parser.add_subparsers()
  
  # java command
  java_parser = subs.add_parser("java", help = "Invoke java related commands") 
  java_subs = java_parser.add_subparsers()

  # java collect command
  jcollect_parser = java_subs.add_parser("collect", help = "Dowload java dependencies from maven and store them on the provided class path")
  parsers["jcollect"] = jcollect_parser
  jcollect_parser.add_argument("-d", "--dependencies", required=True, help="Path to a file containing the dependencies maven paths")
  jcollect_parser.add_argument("-r", "--repo", required=True, help="Base path of maben repository to download the dependencies from")
  jcollect_parser.add_argument("-c", "--classpath", required=True, help="Destination class path to store the downloaded dependencies")
  jcollect_parser.set_defaults(func = do_jcollect)

  # voozanoo commands
  voo_parser = subs.add_parser("voo", help = "Invoke voozanoo related commands") 
  voo_parser.set_defaults(func = print_voo_help)
  parsers["voo_parser"] = voo_parser
  voo_subs = voo_parser.add_subparsers()

  # voo read command
  vread_parser = voo_subs.add_parser("read", help = "Reading voozanoo data")
  parsers["vread"] = vread_parser
  vread_parser.add_argument("-v", "--voozanoo-url", required=True, help="Url of the voozanoo instance to get the data from")
  vread_parser.add_argument("-u", "--user", required=True, help="Voozanoo user name")
  vread_parser.add_argument("-n", "--name", required=False, help="Name of dataset to download")
  vread_parser.add_argument("-e", "--password-env-var", required=False, default="KS_PWD_VOO" , help="Environment variable to ge the password from, default = (KS_PWD_VOO)")
  vread_parser.set_defaults(func = do_vread)

  #calling handlers
  func = None
  try:
    args = parser.parse_args()
    func = args.func
  except AttributeError:
    parser.print_help()

  if func != None:
    args.func(args, parsers)

def do_jcollect(args):
  java.build_classpath(repo = args.repo, paths = args.dependencies, dest = args.classpath)

def do_vread(args, parsers):
  if args.name != None:
    df = voo.get_dataset(args.voozanoo_url, args.user, password.get_password(args.password_env_var, "Please provide the voozanoo password"), args.name)
    print(df)
  else:
    print(f"id\tresource_id\tname")
    for d in voo.get_datasets(
      args.voozanoo_url, 
      args.user, 
      password.get_password(args.password_env_var, "Please provide the voozanoo password")
    ):
      print(f"{d.id}\t{d.resource_id}\t{d.name}")

def print_voo_help(args, parsers):
  parsers["voo_parser"].print_help()

if __name__ == "__main__":
  main()

