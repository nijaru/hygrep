#!/bin/bash

# Hygrep Runner
# Automatically sets up the environment to handle Mojo/Python linking issues.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OS=$(uname)

# Detect .pixi folder
# If running from source, it's in .pixi
# If installed, we might need a different strategy (Phase 4 distribution).
# For now, assume source checkout.

PIXI_DIR="$PROJECT_ROOT/.pixi"

if [ -d "$PIXI_DIR" ]; then
    # Try to find libpython
    if [ "$OS" == "Darwin" ]; then
        LIBPYTHON=$(find "$PIXI_DIR" -name "libpython3*.dylib" | grep "envs/default" | head -n 1)
    else
        LIBPYTHON=$(find "$PIXI_DIR" -name "libpython3*.so" | grep "envs/default" | head -n 1)
    fi

    if [ -n "$LIBPYTHON" ]; then
        export MOJO_PYTHON_LIBRARY="$LIBPYTHON"
        # Debug
        # echo "Using Python Lib: $LIBPYTHON"
    fi
fi

# Run the binary
# Assumes binary is named 'hygrep' and in the same dir
"$PROJECT_ROOT/hygrep" "$@"
