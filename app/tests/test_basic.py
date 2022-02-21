from django.test import TestCase 

mytestdata = {}

class BasicTestCase(TestCase):
    def setUp(self):
        mytestdata['key'] = 'value'

    def test_key_in_mytestdata(self): 
        self.assertIn('key', mytestdata) 
    
    def test_key_value(self):
        self.assertEqual(mytestdata['key'],'value')