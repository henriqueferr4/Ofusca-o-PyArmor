import sys
import time

V = 8  # vocabulary size


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <size>", file=sys.stderr)
        sys.exit(1)

    n = int(sys.argv[1])
    if n % V != 0:
        n += V - n % V

    print(f"number of words: {n}")

    corpus = [f"word{i % V}" for i in range(n)]

    counts = {}

    start = time.perf_counter()
    for word in corpus:
        counts[word] = counts.get(word, 0) + 1
    end = time.perf_counter()

    elapsed = end - start

    answer = ["bad", "ok"]
    is_ok = 1
    expected = n // V

    for i in range(V):
        word = f"word{i}"
        if counts.get(word, 0) != expected:
            is_ok = 0
            break

    print(f"word counts are {answer[is_ok]}\ntime: {elapsed:.3f} seconds")


if __name__ == "__main__":
    main()
