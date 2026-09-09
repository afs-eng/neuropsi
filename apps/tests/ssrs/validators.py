from .config import SSRS_EXPECTED_ITEMS, SSRS_INFORMANTS


def validate_ssrs_input(responses: dict, informant: str, importance: dict | None = None) -> list[str]:
    errors = []
    if informant not in SSRS_INFORMANTS:
        errors.append("Informante invalido para o SSRS.")
        return errors
    if not responses:
        return ["Nenhuma resposta recebida."]
    expected = SSRS_EXPECTED_ITEMS[informant]
    for item in range(1, expected + 1):
        value = responses.get(str(item), responses.get(item))
        if value is None or value == "":
            errors.append(f"Item {item:02d} sem resposta.")
            continue
        try:
            numeric = int(value)
        except (TypeError, ValueError):
            errors.append(f"Item {item:02d} deve ser numerico.")
            continue
        if numeric < 0 or numeric > 5:
            errors.append(f"Item {item:02d} fora do intervalo permitido.")
    if informant == "pais":
        importance = importance or {}
        for item in range(1, 24):
            value = importance.get(str(item), importance.get(item))
            if value is None or value == "":
                errors.append(f"Importancia do item {item:02d} sem resposta.")
                continue
            try:
                numeric = int(value)
            except (TypeError, ValueError):
                errors.append(f"Importancia do item {item:02d} deve ser numerica.")
                continue
            if numeric < 0 or numeric > 2:
                errors.append(f"Importancia do item {item:02d} fora do intervalo permitido.")
    return errors
