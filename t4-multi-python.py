import sys
import time


def matrix_mult(A, B, C, n):
    for i in range(n):
        for j in range(n):
            for k in range(n):
                C[i * n + j] += A[i * n + k] * B[k * n + j]


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <size>", file=sys.stderr)
        sys.exit(1)

    n = int(sys.argv[1])
    if n % 8 != 0:
        n += 8 - n % 8

    print(f"number of rows x cols: {n}")

    A = [1.0] * (n * n)  # Do not
    B = [1.0] * (n * n)  # change
    C = [0.0] * (n * n)  # it

    start = time.perf_counter()
    matrix_mult(A, B, C, n)
    end = time.perf_counter()

    elapsed = end - start

    answer = ["bad", "ok"]
    is_ok = 1

    for i in range(n):
        broke = False
        for j in range(n):
            if C[i * n + j] != float(n):
                is_ok = 0
                broke = True
                break
        if broke:
            break

    print(f"multiply values are {answer[is_ok]}\ntime: {elapsed:.3f} seconds")


if __name__ == "__main__":
    main()
