import unittest
from django.conf import settings

from temba_client.clients import CursorQuery
from temba_client.v2 import TembaClient

from .models import RapidProBackendGlobal


class TestRapidProBackendGlobal(unittest.TestCase):
    def setUp(self):
        self.backend_global = RapidProBackendGlobal()

    def test_get_host(self):
        self.assertEqual(
            self.backend_global.get_host(), settings.SITE_API_HOST
        )

    def test_get_token(self):
        self.assertEqual(
            self.backend_global.get_token(), "8e8ff83e267e0dd0d12ca9de22d57c4846d3364f"
        )

    def test_get_temba_client(self):
        return isinstance(self.backend_global.get_temba_client(), TembaClient)

    def test_query_get_flow(self):
        return isinstance(self.backend_global.query_get_flow, CursorQuery)

    def test_get_all_flow(self):
        temba_client = TembaClient()
