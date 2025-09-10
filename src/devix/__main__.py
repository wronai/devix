#!/usr/bin/env python3
"""
Devix package entry point for direct execution
Enables: python -m devix [command] [args]
"""

import sys
from devix.cli.main import main


if __name__ == "__main__":
    sys.exit(main())
