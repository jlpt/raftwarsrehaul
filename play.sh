#!/bin/bash
# Play the modded Robokill in Ruffle (the open-source Flash emulator in tools/ruffle).
cd "$(dirname "$0")"
exec tools/ruffle/ruffle robokill_mod.swf "$@"
