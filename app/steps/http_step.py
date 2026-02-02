
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
        headers = self.config.get("headers", {})
        timeout = self.config.get("timeout", 10)
        
        try:
            # Prepare arguments
            kwargs = {
                "headers": headers,
                "timeout": timeout
            }
            
            # If input is a dict and method is POST/PUT, send as JSON body?
            # Or if config has 'body_from_input': True
            # For this simple use case (Weather), we ignore input for the request usually,
            # unless constructing dynamic URL.
            # Simplified: just request.
            
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
            else:
                return self._fail(
                    started_at, 
                    f"HTTP {response.status_code}: {response.text[:200]}", 
                    context,
                    error_type="transient" if response.status_code >= 500 else "permanent"
                )
                
        except Exception as e:
            return self._fail(started_at, str(e), context, error_type="transient")

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
