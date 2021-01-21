import requests
import os
import shlex
import glob

def build_classpath(repo, paths, dest):
 """
   Download java classpath from maven given the provided file with paths
   Files will  be put together on the dest folder
 """
 with open(paths, "r") as f:
   deps = f.read().splitlines() 

 current_files = set("__".join(d.split("/")) for d in deps)
 os.makedirs(dest, exist_ok = True)
 
 for dep in deps:
   # uri to download
   uri = f"{repo}/{dep}"

   # path to build locally
   parts = dep.split("/")
   # static part of the path on the destination
   static_path = "__".join(parts[0:len(parts) - 2])

   # deleting other versionis if any
   for other in (os.path.split(f)[-1] for f in glob.glob(os.path.join(dest, f"{static_path}*"))):
     if not other in current_files:
       os.unlink(os.path.join(dest, other))
   
   # downloading and writing file if it does not already exists
   dest_file = os.path.join(dest, "__".join(parts))
   # downloading file if it does not exists already
   if not os.path.exists(dest_file):
     print(f"getting {dep}")
     r = requests.get(uri)
     with open(dest_file, 'wb') as f:
       f.write(r.content)



def java_path():
  """ 
    get the java path using JAVA_HOME if set
  """
  if os.environ.get('JAVA_HOME') == None:
    return "java"
  else:
    return os.path.join(os.environ.get('JAVA_HOME'), "bin", "java") 


def java_job(main_class, class_path, memory, args = []):
  esc_args = list(shlex.quote(a) for a in args)
  cmd = " ".join([
    java_path(), #java executable
    f"-cp \"{class_path}/*\"", #class path 
    f"-Xmx{memory}", #memory limits
    main_class, #java/scala main class
    " ".join(esc_args) #arguments to the call
  ])

  print(cmd) # uncomment this to see the command sent
  res = os.system(cmd)
  if res != 0:
    raise Exception(f"Error encountered while exeuting: {cmd}")

