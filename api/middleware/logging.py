"""
Request Logging Middleware for FastAPI

Logs all API requests, responses, and performance metrics.
Integrates with the existing logging system.
"""

import time
import json
import logging
from typing import Callable
from datetime import datetime
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging API requests and responses"""
    
    def __init__(self, app: ASGIApp, logger: logging.Logger = None):
        super().__init__(app)
        self.logger = logger or logging.getLogger(__name__)
        self.start_time = datetime.now()
        self.request_count = 0
        self.error_count = 0
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details"""
        
        # Start timing
        start_time = time.time()
        request_timestamp = datetime.now().isoformat()
        
        # Increment request counter
        self.request_count += 1
        
        # Extract request details
        request_details = await self._extract_request_details(request)
        
        # Log request start
        self.logger.info(f"Request started: {request.method} {request.url.path}")
        self.logger.debug(f"Request details: {json.dumps(request_details, indent=2)}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Extract response details
            response_details = self._extract_response_details(response, process_time)
            
            # Log response
            self._log_response(request, response, process_time, request_details, response_details)
            
            # Add custom headers
            response.headers["X-Process-Time"] = str(round(process_time, 4))
            response.headers["X-Request-ID"] = str(self.request_count)
            response.headers["X-Timestamp"] = request_timestamp
            
            return response
            
        except Exception as e:
            # Log error
            process_time = time.time() - start_time
            self.error_count += 1
            
            self.logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"in {process_time:.4f}s - {str(e)}"
            )
            
            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "detail": str(e),
                    "timestamp": request_timestamp,
                    "request_id": self.request_count
                },
                headers={
                    "X-Process-Time": str(round(process_time, 4)),
                    "X-Request-ID": str(self.request_count),
                    "X-Timestamp": request_timestamp
                }
            )
    
    async def _extract_request_details(self, request: Request) -> dict:
        """Extract relevant request details for logging"""
        
        details = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": {
                "user_agent": request.headers.get("user-agent"),
                "content_type": request.headers.get("content-type"),
                "content_length": request.headers.get("content-length"),
                "host": request.headers.get("host"),
                "accept": request.headers.get("accept")
            },
            "client_host": request.client.host if request.client else None,
            "request_id": self.request_count + 1
        }
        
        # Add request body for certain content types (with size limit)
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    # Read body (this consumes the stream, so we need to be careful)
                    body = await request.body()
                    if len(body) < 10000:  # Only log small bodies
                        try:
                            body_json = json.loads(body.decode())
                            # Sanitize sensitive data
                            details["body"] = self._sanitize_body(body_json)
                        except:
                            details["body_size"] = len(body)
                    else:
                        details["body_size"] = len(body)
                except:
                    details["body"] = "Could not read body"
        
        return details
    
    def _extract_response_details(self, response: Response, process_time: float) -> dict:
        """Extract response details for logging"""
        
        return {
            "status_code": response.status_code,
            "headers": {
                "content_type": response.headers.get("content-type"),
                "content_length": response.headers.get("content-length")
            },
            "process_time_seconds": round(process_time, 4)
        }
    
    def _log_response(self, request: Request, response: Response, 
                     process_time: float, request_details: dict, response_details: dict):
        """Log response with appropriate level based on status code"""
        
        status_code = response.status_code
        method = request.method
        path = request.url.path
        
        # Determine log level based on status code
        if status_code < 400:
            log_level = logging.INFO
            log_msg = "Request completed"
        elif status_code < 500:
            log_level = logging.WARNING
            log_msg = "Request completed with client error"
        else:
            log_level = logging.ERROR
            log_msg = "Request completed with server error"
            self.error_count += 1
        
        # Main log message
        self.logger.log(
            log_level,
            f"{log_msg}: {method} {path} -> {status_code} in {process_time:.4f}s"
        )
        
        # Detailed debug logging
        if self.logger.isEnabledFor(logging.DEBUG):
            full_details = {
                "request": request_details,
                "response": response_details
            }
            self.logger.debug(f"Full request details: {json.dumps(full_details, indent=2)}")
    
    def _sanitize_body(self, body_data: dict) -> dict:
        """Remove sensitive information from request body"""
        
        sensitive_keys = {
            'password', 'passwd', 'secret', 'token', 'key', 'auth',
            'authorization', 'api_key', 'apikey', 'access_token',
            'refresh_token', 'private_key', 'credential'
        }
        
        def sanitize_dict(data):
            if isinstance(data, dict):
                return {
                    k: "***REDACTED***" if k.lower() in sensitive_keys 
                    else sanitize_dict(v) for k, v in data.items()
                }
            elif isinstance(data, list):
                return [sanitize_dict(item) for item in data]
            else:
                return data
        
        return sanitize_dict(body_data)
    
    def get_stats(self) -> dict:
        """Get middleware statistics"""
        uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "uptime_seconds": round(uptime_seconds, 2),
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "error_rate": round((self.error_count / max(self.request_count, 1)) * 100, 2),
            "requests_per_second": round(self.request_count / max(uptime_seconds, 1), 4),
            "start_time": self.start_time.isoformat()
        }


class APIMetrics:
    """Singleton class to track API metrics across requests"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.reset_metrics()
        return cls._instance
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.endpoint_stats = {}
        self.status_code_counts = {}
        self.total_requests = 0
        self.total_errors = 0
        self.start_time = datetime.now()
    
    def record_request(self, endpoint: str, method: str, status_code: int, process_time: float):
        """Record a request for metrics tracking"""
        
        # Track endpoint statistics
        endpoint_key = f"{method} {endpoint}"
        if endpoint_key not in self.endpoint_stats:
            self.endpoint_stats[endpoint_key] = {
                "count": 0,
                "total_time": 0,
                "avg_time": 0,
                "min_time": float('inf'),
                "max_time": 0,
                "error_count": 0
            }
        
        stats = self.endpoint_stats[endpoint_key]
        stats["count"] += 1
        stats["total_time"] += process_time
        stats["avg_time"] = stats["total_time"] / stats["count"]
        stats["min_time"] = min(stats["min_time"], process_time)
        stats["max_time"] = max(stats["max_time"], process_time)
        
        if status_code >= 400:
            stats["error_count"] += 1
            self.total_errors += 1
        
        # Track status codes
        self.status_code_counts[status_code] = self.status_code_counts.get(status_code, 0) + 1
        self.total_requests += 1
    
    def get_metrics(self) -> dict:
        """Get comprehensive API metrics"""
        uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "uptime_seconds": round(uptime_seconds, 2),
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "error_rate_percent": round((self.total_errors / max(self.total_requests, 1)) * 100, 2),
            "requests_per_second": round(self.total_requests / max(uptime_seconds, 1), 4),
            "endpoint_statistics": {
                endpoint: {
                    **stats,
                    "error_rate_percent": round((stats["error_count"] / stats["count"]) * 100, 2),
                    "avg_time": round(stats["avg_time"], 4),
                    "min_time": round(stats["min_time"], 4),
                    "max_time": round(stats["max_time"], 4)
                }
                for endpoint, stats in self.endpoint_stats.items()
            },
            "status_code_distribution": self.status_code_counts,
            "start_time": self.start_time.isoformat()
        }


# Enhanced middleware with metrics tracking
class EnhancedRequestLoggingMiddleware(RequestLoggingMiddleware):
    """Enhanced request logging middleware with metrics tracking"""
    
    def __init__(self, app: ASGIApp, logger: logging.Logger = None):
        super().__init__(app, logger)
        self.metrics = APIMetrics()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with metrics tracking"""
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Record metrics
            self.metrics.record_request(
                request.url.path,
                request.method,
                response.status_code,
                process_time
            )
            
            # Continue with normal logging
            request_details = await self._extract_request_details(request)
            response_details = self._extract_response_details(response, process_time)
            self._log_response(request, response, process_time, request_details, response_details)
            
            # Add headers
            response.headers["X-Process-Time"] = str(round(process_time, 4))
            response.headers["X-Request-ID"] = str(self.request_count)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            # Record error metrics
            self.metrics.record_request(
                request.url.path,
                request.method,
                500,
                process_time
            )
            
            self.logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"in {process_time:.4f}s - {str(e)}"
            )
            
            raise  # Re-raise to let FastAPI handle it
    
    def get_comprehensive_stats(self) -> dict:
        """Get both middleware and metrics statistics"""
        return {
            "middleware_stats": self.get_stats(),
            "api_metrics": self.metrics.get_metrics()
        }