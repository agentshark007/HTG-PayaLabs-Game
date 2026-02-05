from enum import Enum


class InterpolationMethod(Enum):
    LINEAR = 1
    EASE_IN = 2
    EASE_OUT = 3
    EASE_IN_OUT = 4


def lerp(t, a, b, method):
    """Linear interpolation between a and b with t in [0, 1]."""
    if method == InterpolationMethod.LINEAR:
        return a + t * (b - a)
    elif method == InterpolationMethod.EASE_IN:
        return a + (t**2) * (b - a)
    elif method == InterpolationMethod.EASE_OUT:
        return a + (1 - (1 - t) ** 2) * (b - a)
    elif method == InterpolationMethod.EASE_IN_OUT:
        if t < 0.5:
            return a + (2 * t**2) * (b - a)
        else:
            return a + (1 - (-2 * t + 2) ** 2 / 2) * (b - a)
    else:
        raise ValueError("Invalid interpolation method")


def inverse_lerp(value, a, b):
    """Inverse linear interpolation to find t in [0, 1] for value between a and b."""
    if a == b:
        return 0.5  # Avoid division by zero
    return (value - a) / (b - a)
