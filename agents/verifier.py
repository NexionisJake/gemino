import subprocess
import sys

class VerifierAgent:
    def run_test(self, test_path):
        """
        Runs the test at test_path using pytest.
        Returns (passed: bool, output: str).
        - passed = True if test passes, False otherwise.
        - output = combined stdout/stderr for error feedback.
        """
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', test_path, '-v'],
                capture_output=True,
                text=True,
                timeout=30
            )
            output = result.stdout + "\n" + result.stderr
            passed = result.returncode == 0
            return passed, output
        except subprocess.TimeoutExpired:
            return False, "Test timed out after 30 seconds."
        except Exception as e:
            return False, f"Error running test: {e}"
