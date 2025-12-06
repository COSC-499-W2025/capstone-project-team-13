# Highly efficient Python file (~93 time, ~93 space)

# ------------------------
# Simple loop
# ------------------------
def sum_list(lst):
    total = 0
    for x in lst:  # single shallow loop
        total += x
    return total

# ------------------------
# Minimal array operation
# ------------------------
def create_small_matrix():
    return [[0, 0], [0, 0]]  # tiny 2x2 array

# ------------------------
# Non-recursive function
# ------------------------
def greet(name):
    return f"Hello, {name}!"

# ------------------------
# Main
# ------------------------
def main():
    sum_list([1, 2, 3])
    create_small_matrix()
    greet("World")

if __name__ == "__main__":
    main()
