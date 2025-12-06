# ===============================================
# Highly Inefficient Python Code (~60 lines)
# ===============================================

# ------------------------
# Section 1: Nested Loops
# ------------------------
def nested_loops_a(n):
    total = 0
    for i in range(n):
        for j in range(n):
            for k in range(n):
                total += i * j * k
    return total

def nested_loops_b(n):
    total = 0
    for i in range(n):
        for j in range(n):
            for k in range(n):
                for l in range(n):
                    total += i + j + k + l
    return total

# ------------------------
# Section 2: Recursive Functions
# ------------------------
def recursive_sum(n):
    if n <= 0:
        return 0
    return n + recursive_sum(n-1)

def recursive_factorial(n):
    if n <= 1:
        return 1
    return n * recursive_factorial(n-1)

# ------------------------
# Section 3: Inefficient Array Ops
# ------------------------
def matrix_multiply(n):
    result = [[0]*n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            for k in range(n):
                result[i][j] += i * j * k
    return result

def matrix_addition(n):
    result = [[0]*n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            result[i][j] = i + j
    return result

# ------------------------
# Section 4: Main
# ------------------------
def main():
    nested_loops_a(5)
    nested_loops_b(4)
    recursive_sum(15)
    recursive_factorial(6)
    matrix_multiply(4)
    matrix_addition(5)

if __name__ == "__main__":
    main()
