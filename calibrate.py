#!/usr/bin/env python3
"""
Calibragem das entradas para o Trabalho IV.

Mede o tempo do benchmark NAO ofuscado em alguns pontos, estima a relacao
tempo x entrada e sugere 3 entradas tais que:
  - a MENOR dure >= ALVO_SEGUNDOS (padrao 20s) no baseline;
  - cada entrada seja >= 50% maior que a anterior.

Rode isto UMA vez, na maquina final de testes, antes do experimento.
Depois copie as 3 entradas sugeridas para INPUTS em run_experiment.py.

Uso:
    python3 calibrate.py
"""

import subprocess
import time

ALVO_SEGUNDOS = 20.0
PONTOS_SONDA = [300, 600, 1200]  # pequenos, so para estimar a inclinacao


def mede(n):
    t0 = time.perf_counter()
    subprocess.run(["python3", "benchmark.py", str(n)], capture_output=True)
    return time.perf_counter() - t0


def main():
    print("Sondando (tempos curtos para estimar a escala)...")
    amostras = []
    for n in PONTOS_SONDA:
        t = mede(n)
        amostras.append((n, t))
        print("  n={:5d} -> {:6.2f}s".format(n, t))

    # ajuste linear simples t = a*n (passa pela origem: overhead ~ constante pequeno)
    # usa o maior ponto, mais estavel
    n_ref, t_ref = amostras[-1]
    seg_por_passo = t_ref / n_ref

    menor = int(ALVO_SEGUNDOS / seg_por_passo) + 1
    entradas = [menor, int(menor * 1.5), int(menor * 2.25)]

    print("\nEstimativa: ~{:.5f} s/passo nesta maquina".format(seg_por_passo))
    print("Entradas sugeridas (menor >= {:.0f}s, +50% entre si):".format(ALVO_SEGUNDOS))
    print("  INPUTS = {}".format(entradas))
    print("\nTempos previstos no baseline:")
    for e in entradas:
        print("  n={:6d} -> ~{:5.1f}s".format(e, e * seg_por_passo))
    print("\nConfira rodando a menor de verdade:")
    print("  python3 benchmark.py {}".format(entradas[0]))


if __name__ == "__main__":
    main()
