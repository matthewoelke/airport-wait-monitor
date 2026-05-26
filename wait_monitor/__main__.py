from __future__ import annotations

import sys

from .cli import main as cli_main
from .server import main as server_main

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        raise SystemExit(server_main(sys.argv[2:]))
    raise SystemExit(cli_main())
