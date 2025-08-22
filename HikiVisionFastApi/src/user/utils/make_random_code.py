import random

def make_random_code() -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(6))
