import unittest

class TestClient(unittest.TestCase):
    def test_import(self):
        try:
            import cayley
        except Exception as exception:
            self.fail(f"import raised {exception} unexpectedly!")

    def test_init(self):
        try:
            import cayley
            client = cayley.Client()
        except Exception as exception:
            self.fail(f"import raised {exception} unexpectedly!")

if __name__ == '__main__':
    unittest.main()