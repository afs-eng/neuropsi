from .endpoints import router
from apps.tests.thcp.api import router as thcp_router

router.add_router("/thcp", thcp_router)

__all__ = ["router"]
