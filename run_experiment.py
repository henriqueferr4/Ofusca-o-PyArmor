#!/usr/bin/env python3
"""
Automacao do experimento do Trabalho IV.

Executa cada VERSAO (baseline + configs ofuscadas) para cada ENTRADA,
repetindo REPS vezes, cronometra cada execucao e grava um CSV.
No fim imprime (e salva) uma tabela com media, mediana, desvio padrao,
minimo e maximo por caso.

Ajuste as listas VERSIONS e INPUTS conforme sua calibragem.

Uso:
    python3 run_experiment.py
"""

import csv
import statistics
import subprocess
import sys
import time

# -------------------- CONFIGURACAO --------------------

# Cada versao: (rotulo, comando como lista). {input} e substituido pela entrada.
# Ajuste os caminhos conforme onde o PyArmor gerou os scripts (dist_A, dist_B).
# obf_A = config leve (obf-code 1, padrao) ; obf_B = config pesada (obf-code 2 + wrap)
# Ambas funcionam na TRIAL do PyArmor 9.3 (sem mix-str, sem BCC/RFT).
VERSIONS = [
    ("baseline", ["python3", "benchmark.py", "{input}"]),
    ("obf_A",    ["python3", "dist_A/benchmark.py", "{input}"]),
    ("obf_B",    ["python3", "dist_B/benchmark.py", "{input}"]),
]

# 3 entradas, cada uma >= 50% maior que a anterior.
# A MENOR deve durar >= 20s no baseline — CALIBRE na sua maquina antes
# de rodar p/ valer (veja o passo de calibragem). Estes sao so um ponto
# de partida; rode calibrate.py para achar os seus.
INPUTS = [7500, 11250, 16875]

REPS = 10
CSV_RAW = "resultados_brutos.csv"
CSV_SUMMARY = "resultados_resumo.csv"

# ------------------------------------------------------


def time_once(cmd):
    """Roda o comando uma vez e devolve o tempo de parede em segundos."""
    start = time.perf_counter()
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.perf_counter() - start
    if result.returncode != 0:
        sys.stderr.write(
            "ERRO em {}:\n{}\n".format(" ".join(cmd), result.stderr)
        )
        sys.exit(1)
    return elapsed


def main():
    raw_rows = []  # (versao, entrada, repeticao, tempo)

    for label, template in VERSIONS:
        for inp in INPUTS:
            cmd = [part.replace("{input}", str(inp)) for part in template]
            print("== {} | entrada={} ==".format(label, inp))
            for r in range(1, REPS + 1):
                t = time_once(cmd)
                raw_rows.append((label, inp, r, t))
                print("  rep {:2d}: {:.4f}s".format(r, t))

    # grava CSV bruto
    with open(CSV_RAW, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["versao", "entrada", "repeticao", "tempo_s"])
        w.writerows(raw_rows)

    # resumo por (versao, entrada)
    summary = []
    for label, _ in VERSIONS:
        for inp in INPUTS:
            times = [t for (v, i, _, t) in raw_rows if v == label and i == inp]
            summary.append({
                "versao": label,
                "entrada": inp,
                "media": statistics.mean(times),
                "mediana": statistics.median(times),
                "desvio_padrao": statistics.stdev(times) if len(times) > 1 else 0.0,
                "minimo": min(times),
                "maximo": max(times),
            })

    with open(CSV_SUMMARY, "w", newline="") as f:
        cols = ["versao", "entrada", "media", "mediana",
                "desvio_padrao", "minimo", "maximo"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for row in summary:
            w.writerow(row)

    # imprime tabela
    print("\n=== RESUMO ===")
    print("{:<10} {:>8} {:>10} {:>10} {:>10} {:>10} {:>10}".format(
        "versao", "entrada", "media", "mediana", "desv.pad", "min", "max"))
    for row in summary:
        print("{:<10} {:>8} {:>10.4f} {:>10.4f} {:>10.4f} {:>10.4f} {:>10.4f}".format(
            row["versao"], row["entrada"], row["media"], row["mediana"],
            row["desvio_padrao"], row["minimo"], row["maximo"]))
    print("\nBrutos: {}  |  Resumo: {}".format(CSV_RAW, CSV_SUMMARY))


if __name__ == "__main__":
    main()
