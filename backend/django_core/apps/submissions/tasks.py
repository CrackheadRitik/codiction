"""
Codiction — Submissions Celery Tasks

Async tasks for judging code submissions.
"""

import logging

from celery import shared_task
from django.utils import timezone

from apps.submissions.judge0_client import Judge0Client, Judge0Error
from apps.submissions.models import Submission

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=10)
def judge_submission(self, submission_id: str):
    """
    Judge a submission against all test cases.

    Args:
        submission_id: UUID string of the Submission to judge
    """
    try:
        submission = Submission.objects.select_related("problem").get(id=submission_id)
    except Submission.DoesNotExist:
        logger.error(f"Submission {submission_id} not found")
        return

    # Skip if already judged
    if submission.verdict != Submission.Verdict.PENDING:
        logger.info(f"Submission {submission_id} already judged, skipping")
        return

    try:
        # Get test cases for this problem
        if submission.is_sample_run:
            test_cases = submission.problem.test_cases.filter(is_sample=True)
        else:
            test_cases = submission.problem.test_cases.all()

        if not test_cases.exists():
            submission.verdict = Submission.Verdict.SE
            submission.error_message = "No test cases found for this problem."
            submission.save()
            return

        # Run each test case
        client = Judge0Client()
        final_verdict = Submission.Verdict.AC
        total_runtime = 0
        total_memory = 0.0
        worst_error = None

        for test_case in test_cases:
            try:
                result = client.run_test_case(
                    code=submission.code,
                    language=submission.language,
                    stdin=test_case.input_data,
                    expected_output=test_case.expected_output,
                )
            except Judge0Error as e:
                logger.error(f"Judge0 error for submission {submission_id}: {e}")
                submission.verdict = Submission.Verdict.SE
                submission.error_message = f"Judge system error: {str(e)}"
                submission.save()
                return

            # Track metrics
            if result["runtime_ms"]:
                total_runtime += result["runtime_ms"]
            if result["memory_mb"]:
                total_memory = max(total_memory, float(result["memory_mb"]))

            # Stop on first failure
            if result["verdict"] != "AC":
                final_verdict = result["verdict"]
                worst_error = result.get("error_message")
                break

        # Update submission
        submission.verdict = final_verdict
        submission.runtime_ms = total_runtime or None
        submission.memory_mb = total_memory or None
        submission.error_message = worst_error
        submission.save(
            update_fields=["verdict", "runtime_ms", "memory_mb", "error_message", "updated_at"]
        )

        logger.info(f"Submission {submission_id} judged: {final_verdict}")

    except Exception as e:
        logger.exception(f"Error judging submission {submission_id}: {e}")
        submission.verdict = Submission.Verdict.SE
        submission.error_message = f"Internal error: {str(e)}"
        submission.save()
        raise self.retry(exc=e)