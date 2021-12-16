# -*- coding: utf-8 -*-

from .context import kskit
from random import choice, randint
import unittest
import string


class DeidentificationMethodTest(unittest.TestCase):
    def test_regex(self):
        """test function for get_rule()"""
        self.assertEqual(kskit.deid_mammogram.get_rule('0x50ffffff'), 'RETIRER')
        self.assertEqual(kskit.deid_mammogram.get_rule('0x50a23e56'), 'RETIRER')
        self.assertEqual(kskit.deid_mammogram.get_rule('0x50123456'), 'RETIRER')
        self.assertEqual(kskit.deid_mammogram.get_rule('0x60003000'), 'RETIRER')
        self.assertEqual(kskit.deid_mammogram.get_rule('0x60004000'), 'RETIRER')
        self.assertEqual(kskit.deid_mammogram.get_rule('0x60564000'), 'RETIRER')
        self.assertEqual(kskit.deid_mammogram.get_rule('0x605d3000'), 'RETIRER')
    
    def test_offset4date(self):
        """test function for offset4date"""  
        self.assertEqual(kskit.deid_mammogram.offset4date('19930822', 1), '19930821')
        self.assertEqual(kskit.deid_mammogram.offset4date('20211119', 56), '20210924')
        self.assertEqual(kskit.deid_mammogram.offset4date('18700107', 890),'18670801')
        self.assertEqual(kskit.deid_mammogram.offset4date('20250101', -78), '20250320')
        self.assertEqual(kskit.deid_mammogram.offset4date('20010422', 678), '19990614')
        self.assertEqual(kskit.deid_mammogram.offset4date('22010122', 56), '22001127')
        self.assertEqual(kskit.deid_mammogram.offset4date('56090102', 15), '56081218')
        self.assertEqual(kskit.deid_mammogram.offset4date('20090608', 187), '20081203')
    
    def test_gen_uuid(self):
        """test function for gen_dicom_uid"""
        already_seen = []
        for i in range(0, 9999):
            patient_id = ''.join(choice(string.ascii_letters) for _ in range(randint(5,30)))
            guid = ''.join(choice(string.digits) for _ in range(30))
            new_hash = kskit.deid_mammogram.gen_dicom_uid(patient_id, guid)
            """Tests for duplicates on 10k hashes generated"""
            self.assertTrue(new_hash not in already_seen)
            already_seen.append(new_hash)
            """Tests if the operation can be reproduced"""
            self.assertEquals(kskit.deid_mammogram.gen_dicom_uid(patient_id, guid), new_hash)
    
    def test_levenshtein_distance(self):
        """test function for levenshtein_distance"""
        self.assertEquals(kskit.test_deid_mammogram.levenshtein_distance("chien","niche"), 4)
        self.assertEquals(kskit.test_deid_mammogram.levenshtein_distance("javawasneat","scalaisgreat"), 7)
        self.assertEquals(kskit.test_deid_mammogram.levenshtein_distance("forward","drawrof"), 6)
        self.assertEquals(kskit.test_deid_mammogram.levenshtein_distance("distance","eistancd"), 2)
        self.assertEquals(kskit.test_deid_mammogram.levenshtein_distance("sturgeon","urgently"), 6)
        self.assertEquals(kskit.test_deid_mammogram.levenshtein_distance("difference","distance"), 5)
        self.assertEquals(kskit.test_deid_mammogram.levenshtein_distance("example","samples"), 3)
        self.assertEquals(kskit.test_deid_mammogram.levenshtein_distance("bsfhebfkrn","bsthebtkrn"), 2)
        self.assertEquals(kskit.test_deid_mammogram.levenshtein_distance("cie","cle"), 1)
