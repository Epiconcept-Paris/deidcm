import sys
import argparse
from . import java 



def main(a):
  # Base argument parser
  parser = argparse.ArgumentParser()
  subs = parser.add_subparsers()
  
  # java command
  java_parser = subs.add_parser("java", help = "Invoke java related commands") 
  java_subs = java_parser.add_subparsers()

  # java collect command
  jcollect_parser = java_subs.add_parser("collect", help = "Dowload java dependencies from maven and store them on the provided class path")
  jcollect_parser.add_argument("-d", "--dependencies", required=True, help="Path to a file containing the dependencies maven paths")
  jcollect_parser.add_argument("-r", "--repo", required=True, help="Base path of maben repository to download the dependencies from")
  jcollect_parser.add_argument("-c", "--classpath", required=True, help="Destination class path to store the downloaded dependencies")
  jcollect_parser.set_defaults(func = do_jcollect)
  args = parser.parse_args()
  args.func(args)

def do_jcollect(args):
  java.build_classpath(repo = args.repo, paths = args.dependencies, dest = args.classpath)

if __name__ == "__main__":
  main(sys.argv[1])
