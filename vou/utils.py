import numpy as np


def logistic(x, L, k, x0):
    """
    Simple logisitic function.

    L is the curve's maximum value
    k is the logistic growth rate or steepness of the curve
    x0 is the x value at the sigmoid's midpoint
    """
    y = L / (1 + np.exp(-k * (x - x0)))
    return y
