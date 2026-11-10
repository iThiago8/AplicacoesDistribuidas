#!/usr/bin/env bash
set -euo pipefail

PROJETO="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
JDK="$PROJETO/.jdk"

if [[ ! -e "$JDK" && ! -L "$JDK" ]]; then
    echo 'Nenhum JDK local para remover.'
    exit 0
fi
if [[ -L "$JDK" || ! -f "$JDK/.instalado-pelo-projeto-rpc" ]]; then
    echo 'Remoção cancelada: .jdk não foi criada pelo instalador deste projeto.' >&2
    exit 1
fi

rm -rf -- "$JDK"
echo 'JDK local removido.'
