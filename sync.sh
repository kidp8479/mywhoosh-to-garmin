#!/usr/bin/env bash
# Lance le sync MyWhoosh -> Garmin depuis cette machine (IP maison, pas de blocage 429).
# Usage :  ./sync.sh            # dernière activité
#          ./sync.sh --batch 5  # les 5 dernières
cd "$(dirname "$0")" || exit 1
exec .venv/bin/python main.py "$@"
