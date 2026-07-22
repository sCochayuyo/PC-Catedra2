import math
from typing import Tuple
import numba
import numpy as np


@numba.njit
def category_stats(
    prices: np.ndarray,
    type_id: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Calcula estadisticas descriptivas por categira de forma manual y acelerada.

    Args:
        prices (np.ndarray): Arreglo NumPy con los precios (float)
        type_id (np.ndarray): Arreglo NumPy con los IDs de las categorias (int)

    Returns:
        Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]: Cinco arreglos
        indexados por type_id que contienen respectivamente: cantidad de productos, precio
        minimo, precio máximo, precio promedio y desviación estándar.
    """
    max_id = 0

    for i in range(len(type_id)):
        if type_id[i] > max_id:
            max_id = type_id[i]

    counts = np.zeros(max_id + 1, dtype=np.int64)
    mins = np.full(max_id + 1, np.inf, dtype=np.float64)
    maxs = np.full(max_id + 1, -np.inf, dtype=np.float64)
    sums = np.zeros(max_id + 1, dtype=np.float64)

    for i in range(len(prices)):
        tid = type_id[i]
        p = prices[i]
        counts[tid] += 1
        sums[tid] += p

        if p < mins[tid]:
            mins[tid] = p
        if p > maxs[tid]:
            maxs[tid] = p

        means = np.zeros(max_id + 1, dtype=np.float64)
        for i in range(max_id + 1):
            if counts[i] > 0:
                means[i] = sums[i] / counts[i]

        sq_diff_sums = np.zeros(max_id + 1, dtype=np.float64)
        for i in range(len(prices)):
            tid = type_id[i]
            sq_diff_sums[tid] += (prices[i] - means[tid]) ** 2

        stds = np.zeros(max_id + 1, dtype=np.float64)
        for i in range(max_id + 1):
            if counts[i] > 0:
                stds[i] = math.sqrt(sq_diff_sums[i] / counts[i])

    return counts, mins, maxs, means, stds


@numba.njit
def price_zscores(
    prices: np.ndarray,
    type_id: np.ndarray,
) -> np.ndarray:
    """
    Calcula el z-score de cada precio respecto a su propia categoria.

    Args:
        prices(np.ndarray): Arreglo NumPy con los precios de los productos
        type_id(np.ndarray): Arreglo NumPy con los IDs de las categorias

    Returns:
        np.ndarray: Arreglo NumPy con el z-score calculado para cada producto.
    """

    counts, mins, maxs, means, stds = category_stats(prices, type_id)
    zscores = np.zeros(len(prices), dtype=np.float64)

    for i in range(len(prices)):
        tid = type_id[i]
        if stds[tid] > 0:
            zscores[i] = (prices[i] - means[tid]) / stds[tid]
        else:
            zscores[i] = 0.0

    return zscores


def price_zscores_pure_python(prices: np.ndarray, type_ids: np.ndarray) -> np.ndarray:
    """
    Version en Python puro del calculo de z-scores para comparar rendimiento.

    Args:
        prices (np.ndarray): Arreglo NumPy con los precios.
        type_ids (np.ndarray): Arreglo NumPy con los IDs de categoria.

    Returns:
        np.ndarray: Arreglo NumPy con el z-score de cada producto.
    """
    max_id = 0
    for tid in type_ids:
        if tid > max_id:
            max_id = tid

    counts = [0] * (max_id + 1)
    sums = [0.0] * (max_id + 1)
    for p, tid in zip(prices, type_ids):
        counts[tid] += 1
        sums[tid] += p

    means = [0.0] * (max_id + 1)
    for i in range(max_id + 1):
        if counts[i] > 0:
            means[i] = sums[i] / counts[i]

    sq_diff_sums = [0.0] * (max_id + 1)
    for p, tid in zip(prices, type_ids):
        sq_diff_sums[tid] += (p - means[tid]) ** 2

    stds = [0.0] * (max_id + 1)
    for i in range(max_id + 1):
        if counts[i] > 1:
            stds[i] = math.sqrt(sq_diff_sums[i] / counts[i])

    zscores = np.zeros(len(prices), dtype=np.float64)
    for i in range(len(prices)):
        tid = type_ids[i]
        if stds[tid] > 0:
            zscores[i] = (prices[i] - means[tid]) / stds[tid]
        else:
            zscores[i] = 0.0

    return zscores
