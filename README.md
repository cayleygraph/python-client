# Python Client for [Cayley](https://github.com/cayleygraph/cayley)

This is a work in progress official Python client for the next version of Cayley.

### Usage

#### Print 10 nodes from the graph

```python
import cayley

client = cayley.Client()

for node in client.g.vertex().limit(10):
    print(node)
```

### Development

The client uses the LinkedQL OWL schema file to generate the code for the client.

- Copy `schema.json` to generate
- Execute `python3 -m generate`
- Test the generated code
