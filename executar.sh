#!/usr/bin/env bash
#
# Automatiza o experimento do Trabalho IV com os benchmarks t4-*:
#   1. gera as versoes ofuscadas (dist_A e dist_B);
#   2. confere se as tres versoes de cada benchmark terminam com "ok";
#   3. roda o run_experiment.py e o plot_results.py para cada benchmark;
#   4. guarda CSVs, graficos e log em resultados/<benchmark>_<data>/.
#
# Uso:
#   ./executar.sh [--teste] [multi|palavras|todos]
#
#   --teste   rodada rapida, com entradas pequenas e 2 repeticoes, so para
#             verificar se tudo funciona (os tempos nao servem como resultado)
#
# As entradas e as repeticoes podem ser trocadas sem editar o arquivo:
#   MULTI_INPUTS="624 936 1408" REPS=10 ./executar.sh multi

set -euo pipefail

cd "$(dirname "$(readlink -f "$0")")"
RAIZ="$PWD"

# -------------------- CONFIGURACAO --------------------

# Cada entrada deve ser ao menos 50% maior que a anterior, e a menor deve durar
# ao menos 20 s no baseline. Use multiplos de 8, pois os benchmarks arredondam
# para cima.
MULTI_INPUTS="${MULTI_INPUTS:-624 936 1408}"

# Limitadas pela memoria: nao chegam aos 20 s (o script avisa no final da rodada).
PALAVRAS_INPUTS="${PALAVRAS_INPUTS:-13000000 19500000 29250000}"

REPS="${REPS:-10}"

# Memoria aproximada do corpus do t4-palavras.py, com uma pequena folga.
BYTES_POR_PALAVRA=60

MINIMO_SEGUNDOS=20

# ------------------------------------------------------

uso() {
    sed -n '9,13p' "$0" | sed 's/^# \{0,1\}//'
}

TESTE=0
ALVO="todos"
for arg in "$@"; do
    case "$arg" in
        --teste) TESTE=1 ;;
        multi|palavras|todos) ALVO="$arg" ;;
        -h|--help) uso; exit 0 ;;
        *) echo "Argumento invalido: $arg" >&2; uso >&2; exit 2 ;;
    esac
done

PREFIXO=""
if [ "$TESTE" -eq 1 ]; then
    MULTI_INPUTS="64 96 144"
    PALAVRAS_INPUTS="100000 150000 225000"
    REPS=2
    PREFIXO="teste_"
fi

if [ ! -f venv/bin/activate ]; then
    echo "Ambiente virtual nao encontrado em venv/." >&2
    exit 1
fi
# shellcheck disable=SC1091
source venv/bin/activate

if ! command -v pyarmor >/dev/null || ! python3 -c "import matplotlib" 2>/dev/null; then
    echo "Dependencias ausentes. Rode: pip install pyarmor matplotlib" >&2
    exit 1
fi

# Falha logo no inicio, e nao horas depois, se o corpus nao couber na memoria.
verificar_memoria() {
    local maior disponivel_kb necessario_kb
    maior=$(printf '%s\n' $PALAVRAS_INPUTS | sort -n | tail -1)
    necessario_kb=$(( maior * BYTES_POR_PALAVRA / 1024 ))
    disponivel_kb=$(awk '/^MemAvailable:/ {print $2}' /proc/meminfo)
    if [ "$necessario_kb" -ge "$disponivel_kb" ]; then
        echo "ERRO: t4-palavras.py com $maior palavras precisa de cerca de" \
             "$(( necessario_kb / 1024 )) MB, mas ha $(( disponivel_kb / 1024 )) MB disponiveis." >&2
        echo "Feche outros programas ou reduza PALAVRAS_INPUTS." >&2
        exit 1
    fi
}

gerar_ofuscados() {
    echo "== Gerando versoes ofuscadas =="
    pyarmor gen -O dist_A t4-multi-python.py t4-palavras.py
    pyarmor gen -O dist_B --no-wrap t4-multi-python.py t4-palavras.py
}

conferir() {
    local arquivo="$1" entrada="$2" prefixo
    for prefixo in "" "dist_A/" "dist_B/"; do
        if ! python3 "${prefixo}${arquivo}" "$entrada" | grep -q "are ok"; then
            echo "ERRO: ${prefixo}${arquivo} nao terminou com ok." >&2
            exit 1
        fi
        echo "  ok: ${prefixo}${arquivo}"
    done
}

# Define o benchmark por variaveis do proprio modulo, sem editar run_experiment.py.
# Roda de dentro da pasta de resultados, onde os CSVs e os graficos sao gravados.
medir() {
    local arquivo="$1" entradas="$2" pasta="$3"
    (
        cd "$pasta"
        RAIZ="$RAIZ" ARQUIVO="$arquivo" ENTRADAS="$entradas" REPS="$REPS" python3 -u - <<'PY'
import os
import sys

raiz = os.environ["RAIZ"]
arquivo = os.environ["ARQUIVO"]
sys.path.insert(0, raiz)
import run_experiment as exp

exp.VERSIONS = [
    ("baseline", ["python3", os.path.join(raiz, arquivo), "{input}"]),
    ("obf_A", ["python3", os.path.join(raiz, "dist_A", arquivo), "{input}"]),
    ("obf_B", ["python3", os.path.join(raiz, "dist_B", arquivo), "{input}"]),
]
exp.INPUTS = [int(e) for e in os.environ["ENTRADAS"].split()]
exp.REPS = int(os.environ["REPS"])
exp.main()
PY
        python3 "$RAIZ/plot_results.py"
    )
}

avisar_tempo_curto() {
    local pasta="$1"
    awk -F, -v minimo="$MINIMO_SEGUNDOS" '
        $1 == "baseline" && $3 + 0 < minimo {
            printf "AVISO: entrada %s durou %.1f s no baseline (minimo: %d s).\n", $2, $3, minimo
        }' "$pasta/resultados_resumo.csv"
}

rodar_benchmark() {
    local nome="$1" arquivo="$2" entradas="$3" entrada_conferencia="$4" pasta
    pasta="resultados/${PREFIXO}${nome}_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$pasta"

    echo
    echo "== Benchmark: $arquivo | entradas: $entradas | repeticoes: $REPS =="
    echo "== Conferindo as tres versoes =="
    conferir "$arquivo" "$entrada_conferencia"

    medir "$arquivo" "$entradas" "$pasta" 2>&1 | tee "$pasta/execucao.log"

    if [ "$TESTE" -eq 0 ]; then
        avisar_tempo_curto "$pasta" | tee -a "$pasta/execucao.log"
    fi
    echo "Resultados em: $pasta/"
}

if [ "$ALVO" != "multi" ]; then
    verificar_memoria
fi

gerar_ofuscados

if [ "$ALVO" != "palavras" ]; then
    rodar_benchmark multi t4-multi-python.py "$MULTI_INPUTS" 64
fi
if [ "$ALVO" != "multi" ]; then
    rodar_benchmark palavras t4-palavras.py "$PALAVRAS_INPUTS" 100000
fi

echo
echo "Experimento concluido."
