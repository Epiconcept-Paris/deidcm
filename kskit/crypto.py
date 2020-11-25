from Crypto.Cipher import AES
import secrets
import base64
import qrcode
from PIL import Image
from pyzbar.pyzbar import decode
import cv2
import numpy as np
import sys
import os
import struct

def generate_qr_key(dest, nBytes=512):
  key = secrets.token_bytes(nBytes)
  qr = qrcode.make(base64.b64encode(key))
  qr.save(dest)
  return(key)

def get_qr_key(png):
  img = Image.open(png)
  key = decode(img)[0].data
  return(base64.decodebytes(key))

def read_webcam_key(auto_close = True, camera_index = 0):
  key = ""
  square = []
  font = cv2.FONT_HERSHEY_SIMPLEX
  text = "Present key on your webcam, or press any key to quit" 
  cam = cv2.VideoCapture(camera_index)
  try:
    # initialize the camera
    s, img = cam.read()
    if s:    # frame captured without any errors
      cv2.namedWindow("key extractor",cv2.WINDOW_AUTOSIZE)
      while(True):
        s, img = cam.read()
        if cv2.waitKey(1)!= -1 or (len(key) > 0 and auto_close): 
          cam.release()
          cv2.destroyWindow("key extractor")
          return(key)
        codes = decode(img)
        if len(codes) > 0:
          shape = codes[0].polygon
          square = np.array([[shape[0].x, shape[0].y], [shape[1].x, shape[1].y],[shape[2].x, shape[2].y],[shape[3].x, shape[3].y]], np.int32)
          key = base64.decodebytes(codes[0].data)
        if len(square) > 0:
          cv2.polylines(img, [square], True, (0,255,0), thickness=3)
          text = "key found, please any key to continue"
        cv2.putText(img, text ,(20,20), font, 0.8,(25,25,25),2,cv2.LINE_AA)
        cv2.imshow("key extractor",img)
  except:
    cam.release()
    raise Exception(f"Error found while getting code from webcam {sys.exc_info()}")
    
def encrypt(infile, cryptfile, key = None):
  if key == None:
    key = read_webcam_key()
  iv = secrets.token_bytes(16)
  if(not isinstance(key, bytes) or len(key) != 32):
    raise ValueError(f"Key must be a 256 byte array, but got {type(key)} of length {len(key)}")
  aes = AES.new(key, AES.MODE_CBC, iv)
  fsz = os.path.getsize(infile)
  with open(cryptfile, 'wb') as fout:
    fout.write(struct.pack('<Q', fsz))
    fout.write(iv)
    sz = 2048
  
    with open(infile, "rb") as fin:
      while True:
        data = fin.read(sz)
        n = len(data)
        if n == 0:
          break
        elif n % 16 != 0:
          data += b' ' * (16 - n % 16) # <- padded with spaces
        encd = aes.encrypt(data)
        fout.write(encd) 

def decrypt(infile, plainfile, key = None):
  if key == None:
    key = read_webcam_key()
  if(not isinstance(key, bytes) or len(key) != 32):
    raise ValueError(f"Key must be a 256 byte array, but got {type(key)} of length {len(key)}")
  with open(infile, "rb") as fin:
    fsz = struct.unpack('<Q', fin.read(struct.calcsize('<Q')))[0]
    iv = fin.read(16)
  
    aes = AES.new(key, AES.MODE_CBC, iv)
  
    with open(plainfile, 'wb') as fout:
      sz = 2048
      while True:
        data = fin.read(sz)
        n = len(data)
        if n == 0:
            break
        decd = aes.decrypt(data)
        n = len(decd)
        if fsz > n:
          fout.write(decd)
        else:
          fout.write(decd[:fsz]) # <- remove padding on last block
        fsz -= n
