"""Perfis declarativos; o registro não habilita execução clínica automática."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TestSpecialist:
    instrument_code: str
    name: str
    version: str = "1"


SPECIALISTS = {
    code: TestSpecialist(code, name)
    for code, name in (
        ("wisc4", "WISC-IV"), ("wais3", "WAIS-III"), ("wasi", "WASI"),
        ("bpa2", "BPA-2"), ("ravlt", "RAVLT"), ("fdt", "FDT"),
        ("etdah_pais", "E-TDAH-PAIS"), ("etdah_ad", "E-TDAH-AD"),
        ("scared", "SCARED"), ("srs2", "SRS-2"), ("epq_j", "EPQ-J"),
        ("bai", "BAI"), ("bfp", "BFP"), ("ebadep_a", "EBADEP-A"),
        ("ebadep_ij", "EBADEP-IJ"),
        ("ebaped_ij", "EBADEP-IJ"), ("thcp", "THCP"), ("ssrs", "SSRS"),
        ("cars2_hf", "CARS-2 HF"), ("mchat", "M-CHAT"),
    )
}


def get_specialist(instrument_code: str) -> TestSpecialist | None:
    return SPECIALISTS.get(instrument_code)
