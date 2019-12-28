import unittest


class TestClient(unittest.TestCase):
    def _import(self):
        try:
            import cayley

            return cayley
        except Exception as exception:
            self.fail(f"import raised {exception} unexpectedly!")

    def _client(self):
        cayley = self._import()
        return cayley.Client()

    def test_import(self):
        self._import()

    def test_init(self):
        self._client()

    def test_path(self):
        cayley = self._import()
        prefix = "http://example.org/"
        (
            cayley.path.vertex([])
            .properties([prefix + "name", prefix + "likes"])
            .select(tags=[])
        )

    # def test_query(self):
    #     cayley = self._import()
    #     client = self._client()
    #     prefix = "http://example.org/"
    #     path = (
    #         cayley.path.Path()
    #         .vertex([])
    #         .properties([prefix + "likes", prefix + "name"])
    #         .documents()
    #     )
    #     response = client.query(
    #         path,
    #         language=cayley.QueryLanguage.linkedql,
    #         content_type=cayley.QueryContentType.json_ld,
    #     )
    #     from pprint import pprint

    #     pprint(response.json())
    #     client.close()


if __name__ == "__main__":
    unittest.main()
