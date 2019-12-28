# Python Client for [Cayley](https://github.com/cayleygraph/cayley)

This is a work in progress official Python client for the next version of Cayley.

### Usage

#### Print 10 nodes from the graph

```python
import cayley

client = cayley.Client()

for node in client.query(cayley.path.vertex().limit(10)):
    print(node)
```

### Development

- If not installed, install `poetry` globally with `pip3 install poetry`

In project's directory:

- Install dependencies with `poetry install`

The client uses the LinkedQL OWL schema file to generate the code for the client.

- Copy `schema.json` for generation
- Test with `poetry run python test.py`
