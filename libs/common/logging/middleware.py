from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware

from .context import set_correlation_id


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    header_name = "X-Correlation-ID"

    async def dispatch(self, request, call_next):
        correlation_id = request.headers.get(self.header_name) or str(uuid4())
        set_correlation_id(correlation_id)

        response = await call_next(request)
        response.headers[self.header_name] = correlation_id
        return response
