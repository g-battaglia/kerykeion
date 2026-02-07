#!/bin/bash

# Script to run Dart tests with proper library path for libsweph.so
# This ensures the Swiss Ephemeris library can be found

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set the library path to include the current directory
export LD_LIBRARY_PATH="$SCRIPT_DIR:$LD_LIBRARY_PATH"

echo "Running tests with LD_LIBRARY_PATH=$LD_LIBRARY_PATH"
echo ""

# Run the tests
dart test "$@"
