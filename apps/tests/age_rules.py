INSTRUMENT_AGE_RULES = {
    "thcp": {
        "min_age": 4,
        "max_age": 7,
        "message": "O THCP pode ser aplicado apenas entre 4 e 7 anos.",
    },
    "wisc4": {
        "min_age": 6,
        "max_age": 16,
        "message": "O WISC-IV pode ser aplicado apenas entre 6 e 16 anos.",
    },
    "wais3": {
        "min_age": 16,
        "max_age": 89,
        "message": "O WAIS-III pode ser aplicado apenas entre 16 e 89 anos.",
    },
    "wasi": {
        "min_age": 6,
        "max_age": 89,
        "message": "O WASI pode ser aplicado apenas entre 6 e 89 anos.",
    },
    "fdt": {
        "min_age": 6,
        "max_age": 92,
        "message": "O FDT pode ser aplicado apenas entre 6 e 92 anos.",
    },
    "bpa2": {
        "min_age": 6,
        "max_age": 94,
        "message": "O BPA-2 pode ser aplicado apenas entre 6 e 94 anos.",
    },
    "bai": {
        "min_age": 18,
        "max_age": None,
        "message": "O BAI pode ser aplicado apenas a partir de 18 anos.",
    },
    "ebadep_a": {
        "min_age": 17,
        "max_age": 81,
        "message": "O EBADEP-A pode ser aplicado apenas entre 17 e 81 anos.",
    },
    "ebadep_ij": {
        "min_age": 7,
        "max_age": 18,
        "message": "O EBADEP-IJ pode ser aplicado apenas entre 7 e 18 anos.",
    },
    "ebaped_ij": {
        "min_age": 7,
        "max_age": 18,
        "message": "O EBADEP-IJ pode ser aplicado apenas entre 7 e 18 anos.",
    },
    "epq_j": {
        "min_age": 10,
        "max_age": 16,
        "message": "O EPQ-J pode ser aplicado apenas entre 10 e 16 anos.",
    },
    "etdah_ad": {
        "min_age": 12,
        "max_age": None,
        "message": "O ETDAH-AD pode ser aplicado apenas a partir de 12 anos.",
    },
    "etdah_pais": {
        "min_age": 2,
        "max_age": 17,
        "message": "O ETDAH-PAIS pode ser aplicado apenas entre 2 e 17 anos.",
    },
    "scared": {
        "min_age": None,
        "max_age": 18,
        "message": "O SCARED pode ser aplicado apenas até 18 anos.",
    },
}


def get_instrument_age_rule(code: str):
    return INSTRUMENT_AGE_RULES.get(code)
