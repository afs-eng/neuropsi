from .endpoints import router
from apps.tests.thcp.api import router as thcp_router
from apps.tests.vineland3.api import router as vineland3_router

router.add_router("/thcp", thcp_router)
router.add_router("/vineland3", vineland3_router)

__all__ = ["router"]
