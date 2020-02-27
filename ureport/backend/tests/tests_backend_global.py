import unittest
from django.conf import settings

from temba_client.clients import CursorQuery
from temba_client.v2 import TembaClient

from ureport.backend.rapidpro import RapidProBackendGlobal


class TestRapidProBackendGlobal(unittest.TestCase):
    def setUp(self):
        self.backend_global = RapidProBackendGlobal()

    def test_get_host(self):
        self.assertEqual(
            self.backend_global.host, settings.SITE_API_HOST
        )

    def test_get_token(self):
        self.assertEqual(
            self.backend_global.token, settings.TOKEN_WORKSPACE_GLOBAL
        )

    def test_get_temba_client(self):
        return isinstance(self.backend_global.temba_client, TembaClient)

    def test_query_get_flow(self):
        return isinstance(self.backend_global.query_get_flow, CursorQuery)

    def test_get_all_flows(self):
        temba_client = TembaClient(host=settings.SITE_API_HOST, token=settings.TOKEN_WORKSPACE_GLOBAL)

        return len(temba_client.get_flows().all()) == len(self.backend_global.get_all_flows())
