# -*- coding: utf-8 -*-

from .context import kskit
import unittest
import os
import shutil
import tempfile
import filecmp

class AdvancedTestSuite(unittest.TestCase):
  """Writing and reading a key as QR produces the same key"""
  def test_write_read_same_key(self):
    name = "samekey"
    f128 = os.path.join(self.test_dir, f"{name}128.png")
    f256 = os.path.join(self.test_dir, f"{name}256.png")
    f512 = os.path.join(self.test_dir, f"{name}512.png")
    wkey128 = kskit.generate_qr_key(f128, 128)
    wkey256 = kskit.generate_qr_key(f256, 256)
    wkey512 = kskit.generate_qr_key(f512, 512)
    rkey128 = kskit.get_qr_key(f128)
    rkey256 = kskit.get_qr_key(f256)
    rkey512 = kskit.get_qr_key(f512)
    with self.subTest():
      self.assertEqual(wkey128, rkey128)
    with self.subTest():
      self.assertEqual(wkey256, rkey256)
    with self.subTest():
      self.assertEqual(wkey512, rkey512)
  
  """keys have the right length"""
  def test_keys_right_length(self):
    name = "rightlength"
    f32 = os.path.join(self.test_dir, f"{name}32.png")
    f128 = os.path.join(self.test_dir, f"{name}128.png")
    f256 = os.path.join(self.test_dir, f"{name}256.png")
    f512 = os.path.join(self.test_dir, f"{name}512.png")
    wkey32 = kskit.generate_qr_key(f32, 32)
    wkey128 = kskit.generate_qr_key(f128, 128)
    wkey256 = kskit.generate_qr_key(f256, 256)
    wkey512 = kskit.generate_qr_key(f512, 512)
    with self.subTest():
      self.assertEqual(len(wkey32), 32)
    with self.subTest():
      self.assertEqual(len(wkey128), 128)
    with self.subTest():
      self.assertEqual(len(wkey256), 256)
    with self.subTest():
      self.assertEqual(len(wkey512), 512)
   
  """Encrypting and decrypting produces the same file"""
  def test_crypt_decrypt_same_file(self):
    name = "same_file"
    keyfile = os.path.join(self.test_dir, f"{name}256-key.png")
    key = kskit.generate_qr_key(keyfile, 32)
    plain = os.path.join(self.test_dir, f"{name}-plain")
    crypted = os.path.join(self.test_dir, f"{name}-crypted")
    replain = os.path.join(self.test_dir, f"{name}-replain")
    
    # writing 10MB random file
    with open(plain, 'wb') as fout:
      fout.write(os.urandom(10*1024*1024)) 
    #encrypt and decrypt
    kskit.encrypt(plain, crypted, key)
    kskit.decrypt(crypted, replain, key)
    #obtaining same file
    self.assertTrue(filecmp.cmp(plain, replain))

  def setUp(self):
    self.test_dir = tempfile.mkdtemp(None, "kskit_test_")

  def tearDown(self):
    shutil.rmtree(self.test_dir)

if __name__ == '__main__':
    unittest.main()
