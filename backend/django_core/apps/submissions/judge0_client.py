"""
Codiction — Judge0 Client

Wrapper for Judge0 CE API.

Handles:
- Language ID mapping
- Submission creation
- Result polling
- Multi-test-case execution
- Mock mode for development
"""

import time
import uuid
from typing import Optional

import requests
from django.conf import settings


# =====================================================
# MOCK MODE — Read from Django settings
# =====================================================
JUDGE0_MOCK_MODE = getattr(settings, "JUDGE0_MOCK_MODE", False)


# =====================================================
# LANGUAGE ID MAP
# =====================================================
JUDGE0_LANGUAGE_IDS = {
    "python": 92,
    "java": 91,
    "cpp": 89,
    "javascript": 93,
    "go": 95,
}


# =====================================================
# JUDGE0 STATUS IDs → our verdicts
# =====================================================
JUDGE0_STATUS_MAP = {
    1: "PENDING",
    2: "PENDING",
    3: "AC",
    4: "WA",
    5: "TLE",
    6: "CE",
    7: "RE",
    8: "RE",
    9: "RE",
    10: "RE",
    11: "RE",
    12: "RE",
    13: "SE",
    14: "SE",
}


class Judge0Error(Exception):
    """Raised when Judge0 API returns an error."""

    pass


class Judge0Client:
    """Client for Judge0 CE API."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30,
        poll_interval: float = 0.5,
        max_poll_time: int = 30,
    ):
        self.api_url = (api_url or getattr(settings, "JUDGE0_API_URL", "")).rstrip("/")
        self.api_key = api_key or getattr(settings, "JUDGE0_API_KEY", "")
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.max_poll_time = max_poll_time

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-RapidAPI-Key"] = self.api_key
            headers["X-RapidAPI-Host"] = "judge0-ce.p.rapidapi.com"
        return headers

    def submit(
        self,
        code: str,
        language: str,
        stdin: str = "",
        expected_output: str = "",
        cpu_time_limit: float = 2.0,
        memory_limit_kb: int = 256000,
    ) -> str:
        """Submit code to Judge0 and return the submission token."""
        # =====================================================
        # MOCK MODE — Return fake token
        # =====================================================
        if JUDGE0_MOCK_MODE:
            return f"mock-{uuid.uuid4()}"

        if language not in JUDGE0_LANGUAGE_IDS:
            raise Judge0Error(f"Unsupported language: {language}")

        payload = {
            "source_code": code,
            "language_id": JUDGE0_LANGUAGE_IDS[language],
            "stdin": stdin,
            "expected_output": expected_output,
            "cpu_time_limit": cpu_time_limit,
            "memory_limit": memory_limit_kb,
        }

        try:
            response = requests.post(
                f"{self.api_url}/submissions",
                json=payload,
                headers=self._headers(),
                timeout=self.timeout,
                params={"base64_encoded": "false", "wait": "false"},
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise Judge0Error(f"Judge0 submission failed: {e}") from e

        data = response.json()
        token = data.get("token")
        if not token:
            raise Judge0Error(f"Judge0 returned no token: {data}")
        return token

    def get_result(self, token: str) -> dict:
        """Poll Judge0 until the result is ready, then return it."""
        # =====================================================
        # MOCK MODE — Return fake AC verdict
        # =====================================================
        if JUDGE0_MOCK_MODE:
            time.sleep(0.1)  # Simulate slight delay
            return {
                "verdict": "AC",
                "runtime_ms": 45,
                "memory_mb": 14.25,
                "error_message": None,
                "stdout": "",
                "stderr": None,
                "status_description": "Accepted (MOCK)",
            }

        start_time = time.time()

        while time.time() - start_time < self.max_poll_time:
            try:
                response = requests.get(
                    f"{self.api_url}/submissions/{token}",
                    headers=self._headers(),
                    timeout=self.timeout,
                    params={"base64_encoded": "false"},
                )
                response.raise_for_status()
            except requests.RequestException as e:
                raise Judge0Error(f"Judge0 poll failed: {e}") from e

            data = response.json()
            status_id = data.get("status", {}).get("id", 1)
            if status_id not in (1, 2):
                return self._parse_result(data)
            time.sleep(self.poll_interval)

        raise Judge0Error(f"Judge0 polling timed out after {self.max_poll_time}s")

    def _parse_result(self, data: dict) -> dict:
        status_id = data.get("status", {}).get("id", 13)
        verdict = JUDGE0_STATUS_MAP.get(status_id, "SE")

        runtime_sec = data.get("time")
        runtime_ms = int(float(runtime_sec) * 1000) if runtime_sec else None

        memory_kb = data.get("memory")
        memory_mb = round(memory_kb / 1024, 2) if memory_kb else None

        error_message = None
        if verdict in ("CE", "RE", "SE"):
            error_message = (
                data.get("compile_output")
                or data.get("stderr")
                or data.get("message")
            )

        return {
            "verdict": verdict,
            "runtime_ms": runtime_ms,
            "memory_mb": memory_mb,
            "error_message": error_message,
            "stdout": data.get("stdout"),
            "stderr": data.get("stderr"),
            "status_description": data.get("status", {}).get("description"),
        }

    def run_test_case(
        self,
        code: str,
        language: str,
        stdin: str,
        expected_output: str,
        cpu_time_limit: float = 2.0,
        memory_limit_kb: int = 256000,
    ) -> dict:
        """Submit code for a single test case and wait for the result."""
        token = self.submit(
            code=code,
            language=language,
            stdin=stdin,
            expected_output=expected_output,
            cpu_time_limit=cpu_time_limit,
            memory_limit_kb=memory_limit_kb,
        )
        return self.get_result(token)