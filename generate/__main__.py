import sys
from pathlib import Path
from .generate import generate

module_path = Path(__file__).parent.parent / "cayley" / "path.py"

generate(module_path)

print(f"Generated {module_path}", file=sys.stderr)
