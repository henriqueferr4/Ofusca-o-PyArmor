#!/usr/bin/env python3
"""
Gera graficos a partir de resultados_brutos.csv.

Produz:
  - grafico_barras.png : media por versao, agrupada por entrada, com barra de erro (desvio padrao)
  - grafico_overhead.png : fator de overhead (tempo_ofuscado / tempo_baseline) por entrada

Requer: matplotlib  (pip install matplotlib)

Uso:
    python3 plot_results.py
"""

import csv
import statistics
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CSV_RAW = "resultados_brutos.csv"


def load():
    data = defaultdict(list)  # (versao, entrada) -> [tempos]
    with open(CSV_RAW, newline="") as f:
        for row in csv.DictReader(f):
            key = (row["versao"], int(row["entrada"]))
            data[key].append(float(row["tempo_s"]))
    return data


def main():
    data = load()
    versoes = sorted({k[0] for k in data}, key=lambda v: (v != "baseline", v))
    entradas = sorted({k[1] for k in data})

    # ---- grafico de barras: media + desvio padrao ----
    fig, ax = plt.subplots(figsize=(9, 5))
    n_v = len(versoes)
    largura = 0.8 / n_v
    for idx, v in enumerate(versoes):
        medias = [statistics.mean(data[(v, e)]) for e in entradas]
        erros = [statistics.stdev(data[(v, e)]) if len(data[(v, e)]) > 1 else 0
                 for e in entradas]
        posicoes = [i + idx * largura for i in range(len(entradas))]
        ax.bar(posicoes, medias, largura, yerr=erros, capsize=4, label=v)
    ax.set_xticks([i + largura * (n_v - 1) / 2 for i in range(len(entradas))])
    ax.set_xticklabels([str(e) for e in entradas])
    ax.set_xlabel("Entrada (n_passos)")
    ax.set_ylabel("Tempo medio (s)")
    ax.set_title("Tempo por versao e entrada (barra de erro = desvio padrao)")
    ax.legend()
    fig.tight_layout()
    fig.savefig("grafico_barras.png", dpi=150)
    print("gerado: grafico_barras.png")

    # ---- grafico de overhead relativo ao baseline ----
    fig2, ax2 = plt.subplots(figsize=(9, 5))
    for v in versoes:
        if v == "baseline":
            continue
        fatores = []
        for e in entradas:
            base = statistics.mean(data[("baseline", e)])
            fatores.append(statistics.mean(data[(v, e)]) / base)
        ax2.plot(entradas, fatores, marker="o", label=v)
    ax2.axhline(1.0, linestyle="--", color="gray", label="baseline (1x)")
    ax2.set_xlabel("Entrada (n_passos)")
    ax2.set_ylabel("Overhead (x vezes o baseline)")
    ax2.set_title("Custo relativo da ofuscacao por tamanho de entrada")
    ax2.legend()
    fig2.tight_layout()
    fig2.savefig("grafico_overhead.png", dpi=150)
    print("gerado: grafico_overhead.png")


if __name__ == "__main__":
    main()
