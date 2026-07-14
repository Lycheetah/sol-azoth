#!/bin/bash
# 999agent — self-executing launcher

cd "$(dirname "${BASH_SOURCE[0]}")" || exit 1
exec python3 ./agent.py "$@"
