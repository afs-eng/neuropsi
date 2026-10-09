from io import BytesIO
import math

import matplotlib.pyplot as plt


def saved_percentile_radar(labels: list[str], values: list[float]) -> bytes | None:
    if len(labels) < 3 or len(labels) != len(values) or any(value < 0 or value > 100 for value in values):
        return None
    angles = [2 * math.pi * index / len(labels) for index in range(len(labels))]
    figure, axis = plt.subplots(figsize=(8, 6), subplot_kw={"projection": "polar"})
    axis.plot([*angles, angles[0]], [*values, values[0]], color="#548235")
    axis.fill([*angles, angles[0]], [*values, values[0]], color="#548235", alpha=0.18)
    axis.set_xticks(angles, labels, fontsize=8)
    axis.set_ylim(0, 100)
    axis.set_title("IPHEXA — Perfil dos percentis", pad=25)
    output = BytesIO()
    figure.savefig(output, format="png", dpi=180, bbox_inches="tight")
    plt.close(figure)
    return output.getvalue()
