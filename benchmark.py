#!/usr/bin/env python3
"""
Benchmark CPU-bound para o Trabalho IV (ofuscacao).

Carga: simulacao de N-corpos (gravitacional), puramente CPU-bound,
sem I/O, para que o custo da ofuscacao nao fique mascarado.

Uso:
    python3 benchmark.py <n_passos>

A entrada (<n_passos>) controla quantos passos de integracao sao
executados. Calibre as 3 entradas de modo que a MENOR dure >= 20s
no codigo NAO ofuscado, e cada entrada seja >= 50% maior que a anterior.

Exemplo de ponto de partida (ajuste na sua maquina):
    python3 benchmark.py 2500     # menor  (alvo: >= 20s no baseline)
    python3 benchmark.py 3750     # +50%
    python3 benchmark.py 5625     # +50%
"""

import sys

# Corpos fixos: mantem o tamanho do arquivo pequeno (importante p/ trial do PyArmor)
# e a carga concentrada no laco de integracao, nao na geracao de dados.
N_BODIES = 120


def init_bodies(n):
    """Posicoes, velocidades e massas deterministicas (sem random, p/ reprodutibilidade)."""
    bodies = []
    for i in range(n):
        # distribuicao deterministica simples
        x = (i * 37 % 1000) / 100.0 - 5.0
        y = (i * 53 % 1000) / 100.0 - 5.0
        z = (i * 71 % 1000) / 100.0 - 5.0
        vx = (i * 13 % 200) / 1000.0 - 0.1
        vy = (i * 17 % 200) / 1000.0 - 0.1
        vz = (i * 19 % 200) / 1000.0 - 0.1
        mass = 1.0 + (i % 5)
        bodies.append([x, y, z, vx, vy, vz, mass])
    return bodies


def advance(bodies, dt):
    """Um passo de integracao O(n^2): atualiza velocidades e posicoes."""
    n = len(bodies)
    softening = 0.01
    for i in range(n):
        bi = bodies[i]
        ax = ay = az = 0.0
        for j in range(n):
            if i == j:
                continue
            bj = bodies[j]
            dx = bj[0] - bi[0]
            dy = bj[1] - bi[1]
            dz = bj[2] - bi[2]
            dist2 = dx * dx + dy * dy + dz * dz + softening
            inv = 1.0 / (dist2 * (dist2 ** 0.5))
            f = bj[6] * inv
            ax += dx * f
            ay += dy * f
            az += dz * f
        bi[3] += ax * dt
        bi[4] += ay * dt
        bi[5] += az * dt
    for b in bodies:
        b[0] += b[3] * dt
        b[1] += b[4] * dt
        b[2] += b[5] * dt


def energy(bodies):
    """Soma simples para forcar o uso do resultado (evita otimizacoes de morte de codigo)."""
    total = 0.0
    for b in bodies:
        total += b[6] * (b[3] * b[3] + b[4] * b[4] + b[5] * b[5])
    return total


def main():
    if len(sys.argv) != 2:
        print("uso: python3 benchmark.py <n_passos>", file=sys.stderr)
        sys.exit(1)
    n_steps = int(sys.argv[1])

    bodies = init_bodies(N_BODIES)
    dt = 0.01
    for _ in range(n_steps):
        advance(bodies, dt)

    # imprime o resultado para garantir que o trabalho nao foi descartado
    print("{:.6f}".format(energy(bodies)))


if __name__ == "__main__":
    main()
