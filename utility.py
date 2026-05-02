import math


def is_between(x, a, b):
    if a == b:
        return x == a
    elif a > b:
        return b < x < a
    elif a < b:
        return a < x < b
    else:
        return False


def is_point_in_rect(point, a, b):
    return is_between(point.x, a.x, b.x) and is_between(point.y, a.y, b.y)


def split_nonempty_lines(text: str):
    return [line for line in text.splitlines() if line.strip()]


def distance(a, b):
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)
