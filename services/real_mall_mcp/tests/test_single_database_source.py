import unittest

import database


class SingleDatabaseSourceTest(unittest.TestCase):
    def test_database_layer_exposes_only_primary_database_source(self):
        self.assertFalse(hasattr(database, "DEMO_DATABASE_URL"))
        self.assertFalse(hasattr(database, "demo_engine"))
        self.assertFalse(hasattr(database, "DemoSessionLocal"))
