from pathlib import Path
from .generate import generate

module_path = Path(__file__).parent.parent / "cayley" / "path.py"

with module_path.open("w+") as file:
    file.write(generate())