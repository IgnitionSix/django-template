from django.test import TestCase
from rest_framework.test import APIClient, APITestCase

# Create your tests here.
class DefaultRunnerTest(APITestCase):
    """ Test for making sure that our runner work """
    
    def setUp(self):
        pass
        
    def test_runner_working(self):
        self.assertEqueal(True, True)