#!/bin/bash

# Load environment variables
# Execute Python script

set -a # automatically export all variables
source `dirname "$0"`/.env
set +a

python `dirname "$0"`/solar-ev.py -v
