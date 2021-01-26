import os
import getpass

def get_password(name, message = "Password"):
  if os.environ.get(f'{name.upper()}') == None :
    return getpass.getpass(prompt=f"{message}:", stream=None)
  return os.environ.get(f'{name.upper()}')

