#!/usr/bin/env python3

import yaml
import json
import sys
from pathlib import Path

# Add the devix directory to the path
sys.path.insert(0, str(Path(__file__).parent))
from monitor import ApplicationMonitor

def load_config(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

if __name__ == '__main__':
    config = load_config('devix/config.yaml')
    m = ApplicationMonitor('.', config)
    issues, metrics = m.check_all()
    print(json.dumps({'issues': issues, 'metrics': metrics}, indent=2))
