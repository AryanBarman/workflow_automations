
"""
HttpStep - Real HTTP Request Step
"""

from datetime import datetime
from typing import Any
import requests

from app.core.executor_contract import (
    StepExecutor,
    StepResult,
    StepError,
    StepMetadata,
    ExecutionContext,
)


class HttpStep:
    """
    HttpStep - Executes a real HTTP request.
    
    Config:
        url: Target URL
        method: HTTP method (GET, POST, etc.) - default GET
        headers: Optional headers dict
        timeout: Timeout in seconds (default 10)
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
    
    def execute(self, input: Any, context: ExecutionContext) -> StepResult:
        started_at = datetime.utcnow()
        
        url = self.config.get("url")
        if not url:
           # Fail immediately if no URL
           return self._fail(started_at, "Missing URL in step config", context)

        method = self.config.get("method", "GET").upper()
        headers = self.config.get("headers", {}).copy()  # Copy to avoid mutating config
        timeout = self.config.get("timeout", 10)
        
        # Handle dynamic headers from input
        if self.config.get("headers_from_input") and isinstance(input, dict):
            dynamic_headers = input.get("_headers", {})
            if isinstance(dynamic_headers, dict):
                headers.update(dynamic_headers)
        
        # Prepare arguments
        kwargs = {
            "headers": headers,
            "timeout": timeout
        }
        
        # Handle dynamic body from input
        if self.config.get("body_from_input"):
             # Use the whole input as the JSON body (excluding _headers if we want to be clean, 
             # but strictly following "minimal code", we just pass input.
             # If input has _headers, it gets sent in body. 
             # Refinement: strip _headers?
             # Let's strip _headers to avoid leaking it to the API.
             if isinstance(input, dict):
                 json_body = input.copy()
                 json_body.pop("_headers", None)
                 kwargs["json"] = json_body
             else:
                 kwargs["json"] = input
        
        try:
            response = requests.request(method, url, **kwargs)
            
            # Check status
            if 200 <= response.status_code < 300:
                try:
                    output = response.json()
                except:
                    output = {"text": response.text}
                
                # Add metadata
                output["_status"] = response.status_code
                
                return self._success(started_at, output)
            
            # Application Logic Error (HTTP 4xx/5xx)
            else:
                is_server_error = response.status_code >= 500
                error_category = "Transient" if is_server_error else "Permanent"
                
                # Fail with explicit category in message
                return self._fail(
                    started_at, 
                    f"HTTP {response.status_code} ({error_category}): {response.text[:200]}", 
                    context,
                    error_type="transient" if is_server_error else "permanent"
                )
                
        except Exception as e:
            # Network/Timeout/Connection errors are generally transient
            return self._fail(
                started_at, 
                f"Network Error (Transient): {str(e)}", 
                context, 
                error_type="transient"
            )

    def _success(self, started_at, output):
        finished_at = datetime.utcnow()
        duration_ms = int((finished_at - started_at).total_seconds() * 1000)
        metadata = StepMetadata(duration_ms=duration_ms, started_at=started_at, finished_at=finished_at)
        return StepResult(status="success", output=output, metadata=metadata)

    def _fail(self, started_at, message, context, error_type="transient"):
        finished_at = datetime.utcnow()
        duration_ms = int((finished_at - started_at).total_seconds() * 1000)
        metadata = StepMetadata(duration_ms=duration_ms, started_at=started_at, finished_at=finished_at)
        error = StepError(
            code="HTTP_ERROR",
            message=message,
            retryable=(error_type == "transient"),
            error_type=error_type
        )
        return StepResult(status="failure", error=error, metadata=metadata)
