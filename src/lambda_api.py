"""Lambda adapter for FastAPI app via Mangum."""

from mangum import Mangum

from src.api.main import app

handler = Mangum(app)
