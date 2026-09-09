from django.apps import AppConfig


class TestsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.tests"
    verbose_name = "Testes"

    def ready(self):
        from apps.tests.bfp import BFPModule  # noqa
        from apps.tests.fdt import FDTModule  # noqa
        from apps.tests.bpa2 import BPA2Module  # noqa
        from apps.tests.wasi import WASIModule  # noqa
        from apps.tests.wisc4 import WISC4Module  # noqa
        from apps.tests.wais3 import WAIS3Module  # noqa
        from apps.tests.ebaped_ij import EBADEPIJModule  # noqa
        from apps.tests.ebadep_a import EBADEPAModule  # noqa
        from apps.tests.epq_j import EPQJModule  # noqa
        from apps.tests.etdah_ad import ETDAHADModule  # noqa
        from apps.tests.etdah_pais import ETDAHPAISModule  # noqa
        from apps.tests.ravlt import RAVLTModule  # noqa
        from apps.tests.scared import SCAREDModule  # noqa
        from apps.tests.cars2_hf import CARS2HFModule  # noqa
        from apps.tests.mchat import MCHATModule  # noqa
        from apps.tests.ssrs import SSRSModule  # noqa
