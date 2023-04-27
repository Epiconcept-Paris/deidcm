from . import crypto
import os
import hashlib
from getpass import getpass

def create_backup_key(key_dest):
  crypto.generate_qr_key(key_dest, 32) #256 bits    

def backup_file(source, crypted_dest,  webcam_pwd = True, clipboard_pwd = False, md5sum = None):   
  if not os.path.exists(source):
    raise FileNotFoundError(f"The source file {source} cannot be found")
  if md5sum:
    md5hash = hashlib.md5(open(source,'rb').read()).hexdigest()
    if md5hash != md5sum:
      raise ValueError(f"The file to backup {source} has not the expected checksum  '{md5sum}'")
    else:
      print("md5 of source file is OK")
  if webcam_pwd or clipboard_pwd:
    import clipboard
  if webcam_pwd:
    b64key = crypto.read_webcam_key(auto_close = True, camera_index = 0)
  elif clipboard_pwd:
    b64key = clipboard.paste()
  else:
    b64key = getpass("Please type ecryption key")
    raise ValueError("either webcam or clipboard password has to be usef")
  crypto.encrypt(source, crypted_dest, b64key)
  if webcam_pwd or clipboard_pwd:
    clipboard.copy("")
  

def restore_file(crypted_source, dest,  webcam_pwd = True, clipboard_pwd = False, md5sum = None):   
  if webcam_pwd or clipboard_pwd:
    import clipboard
  if webcam_pwd:
    b64key = crypto.read_webcam_key(auto_close = True, camera_index = 0)
  elif clipboard_pwd:
    b64key = clipboard.paste()
  else:
    b64key = getpass("Please type ecryption key")
    raise ValueError("either webcam or clipboard password has to be usef")
  if os.path.exists(dest):
    raise ValueError("Destination file already exists cannot override it")
  crypto.decrypt(crypted_source, dest, b64key)

  if webcam_pwd or clipboard_pwd:
    clipboard.copy("")
  if md5sum:
    md5hash = hashlib.md5(open(dest,'rb').read()).hexdigest()
    if md5hash != md5sum:
      raise ValueError(f"The restored file {dest} has not the expected checksum '{md5sum}'")
    else:
      print("md5 of decrypted file is OK")

