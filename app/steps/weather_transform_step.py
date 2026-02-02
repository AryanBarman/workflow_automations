
"""
WeatherTransformStep - Specialized transformation for weather data
"""

from datetime import datetime
from typing import Any

from app.core.executor_contract import (
    StepResult,
    StepMetadata,
    ExecutionContext,
)


class WeatherTransformStep:
    """
    WeatherTransformStep - Formats wttr.in JSON output into a human-readable log line.
    
    Expected Input: JSON response from wttr.in/?format=j1
    Output: Dictionary with "log_line" key.
    """
    
    def execute(self, input: Any, context: ExecutionContext) -> StepResult:
        started_at = datetime.utcnow()
        
        try:
            # Input comes from HttpStep output
            # HttpStep wraps its output in a dict? No, HttpStep output IS response.json() (+ metadata).
            
            # Extract data
            current = input.get("current_condition", [{}])[0]
            temp = current.get("temp_C", "?")
            desc = current.get("weatherDesc", [{}])[0].get("value", "Unknown")
            humidity = current.get("humidity", "?")
            
            # location data is in nearest_area
            area = input.get("nearest_area", [{}])[0].get("areaName", [{}])[0].get("value", "Unknown Location")
            
            log_line = f"[{datetime.now().isoformat()}] Weather in {area}: {temp}°C, {desc}, Humidity: {humidity}%"
            
            output = {
                "log_line": log_line,
                "processed": True
            }
            
            finished_at = datetime.utcnow()
            duration_ms = int((finished_at - started_at).total_seconds() * 1000)
            metadata = StepMetadata(duration_ms=duration_ms, started_at=started_at, finished_at=finished_at)
            
            return StepResult(status="success", output=output, metadata=metadata)
            
        except Exception as e:
             # If extracting fails, return failure
             # OR fallback to raw input dump
             return self._fail(started_at, f"Failed to parse weather data: {str(e)}")

    def _fail(self, started_at, message):
        finished_at = datetime.utcnow()
        duration_ms = int((finished_at - started_at).total_seconds() * 1000)
        metadata = StepMetadata(duration_ms=duration_ms, started_at=started_at, finished_at=finished_at)
        from app.core.executor_contract import StepError
        error = StepError(code="TRANSFORM_ERROR", message=message, retryable=False, error_type="permanent")
        return StepResult(status="failure", error=error, metadata=metadata)
