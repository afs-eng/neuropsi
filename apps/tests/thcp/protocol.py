"""Referências fixas de CORRECAO.xlsm, aba THCP; apenas a coluna Nota é editável."""


def item(key, label, maximum=1, options=None, score_options=None):
    return {
        "key": key, "label": label, "max_score": maximum,
        "options": options or [], "score_options": score_options,
    }


PROTOCOL = {
    "hpm_i": [
        item("labirinto", "Total do labirinto", 4),
        item("copia_1a", "1a) Quadrado", 2),
        item("copia_1b", "1b) Triângulo", 2),
        item("copia_2a", "2a) Letra A", 2),
        item("copia_2b", "2b) Letra B", 2),
        item("copia_3a", "3a) Número 7", 2),
        item("copia_3b", "3b) Letra G", 2),
        item("copia_4", "4) Número 2", 2),
        item("figura_5a", "5a) Quadrado", 1),
        item("figura_5b", "5b) Círculo", 1),
        item("figura_5c", "5c) Posição", 1),
        item("figura_5d", "5d) Proporção", 1),
    ],
    "hpm_ii": [
        item(key, label, options=list(range(1, count + 1)))
        for key, label, count in [
            ("1", "1)", 5), ("2", "2)", 4), ("3", "3)", 5),
            ("4a", "4a)", 4), ("4b", "4b)", 4), ("4c", "4c)", 4),
            ("5", "5)", 4), ("6", "6)", 4),
        ]
    ],
    "linguagem": [item(str(i), f"{i})", options=[1, 2, 3, 4]) for i in range(1, 13)],
    "pq": [
        item(key, label, options=list(range(1, count + 1)))
        for key, label, count in [
            ("1", "1)", 4), ("2a", "2a)", 5), ("2b", "2b)", 5),
            ("3", "3)", 4), ("4", "4)", 4), ("5", "5)", 4),
            ("6", "6)", 4), ("7", "7)", 4), ("8", "8)", 7),
            ("9", "9)", 6), ("10", "10)", 4),
        ]
    ],
    "memoria": [
        item("1", "1)", options=[1, 2, 3]),
        item("2", "2)", options=[1, 2, 3]),
        item("3", "3)", 3, score_options=[0, 1, 3]),
        item("4", "4)", 5, score_options=[0, 1, 2, 3, 5]),
    ],
}


def protocol_totals(responses):
    totals = {group: sum(value["score"] for value in entries.values()) for group, entries in responses.items()}
    return {
        "hpm": totals["hpm_i"] + totals["hpm_ii"],
        **{group: totals[group] for group in ("linguagem", "pq", "memoria")},
    }
