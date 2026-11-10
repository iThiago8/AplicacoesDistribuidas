#!/usr/bin/env bash
set -euo pipefail

PROJETO="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
JDK="$PROJETO/.jdk"

if [[ -x "$JDK/bin/java" && -x "$JDK/bin/javac" ]]; then
    echo "O JDK local já está instalado em $JDK"
    exit 0
fi
if [[ -e "$JDK" || -L "$JDK" ]]; then
    echo "A pasta .jdk já existe. Verifique seu conteúdo antes de continuar." >&2
    exit 1
fi

for ferramenta in curl tar; do
    command -v "$ferramenta" >/dev/null || { echo "Falta instalar $ferramenta." >&2; exit 1; }
done
[[ "$(uname -s)" == Linux ]] || { echo 'Este script suporta Linux.' >&2; exit 1; }
case "$(uname -m)" in
    x86_64) ARQUITETURA=x64 ;;
    aarch64|arm64) ARQUITETURA=aarch64 ;;
    *) echo 'Arquitetura não suportada.' >&2; exit 1 ;;
esac

TEMPORARIO="$(mktemp -d "$PROJETO/.jdk-download.XXXXXX")"
trap 'rm -rf -- "$TEMPORARIO"' EXIT
echo 'Baixando Eclipse Temurin JDK 21...'
curl --fail --location --retry 3 \
    "https://api.adoptium.net/v3/binary/latest/21/ga/linux/$ARQUITETURA/jdk/hotspot/normal/eclipse" \
    --output "$TEMPORARIO/jdk.tar.gz"
mkdir "$TEMPORARIO/jdk"
tar -xzf "$TEMPORARIO/jdk.tar.gz" -C "$TEMPORARIO/jdk" --strip-components=1
"$TEMPORARIO/jdk/bin/java" -version
"$TEMPORARIO/jdk/bin/javac" -version
touch "$TEMPORARIO/jdk/.instalado-pelo-projeto-rpc"
mv -- "$TEMPORARIO/jdk" "$JDK"
echo 'Pronto! Use ./.jdk/bin/java e ./.jdk/bin/javac na pasta do projeto.'
