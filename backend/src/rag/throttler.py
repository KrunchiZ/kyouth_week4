"""Rate-aware throttling using rate_limits.txt.
Copied helpers from tag_data.py — that file will be removed after this implementation.
"""
import time
import logging
from pathlib import Path
from collections import defaultdict

logging.basicConfig(
	level=logging.INFO,
	format="[%(asctime)s] | %(levelname)s | %(message)s",
	datefmt="%d/%m/%y %H:%M:%S",
)

# Hypothetical local model rate limits (fallback)
LOCAL_RPM = 60
LOCAL_TPM = 250_000


def _parse_num(s: str) -> int:
	"""Parse K/M suffixes (e.g. '250K' -> 250000)."""
	s = s.upper().replace(",", "")
	if s.endswith("M"):
		return int(float(s[:-1]) * 1_000_000)
	if s.endswith("K"):
		return int(float(s[:-1]) * 1_000)
	return int(s)


def _parse_rate_limits(path: Path) -> dict:
	"""Parse rate_limits.txt into {model: {rpm, tpm, rpd}}."""
	limits: dict = {}
	if not path.exists():
		logging.warning("rate_limits.txt not found at %s — no throttling applied", path)
		return limits
	for line in path.read_text().splitlines():
		line = line.strip()
		if not line or line.startswith("#"):
			continue
		parts = line.split()
		if len(parts) < 4:
			continue
		model, rpm_s, tpm_s, rpd_s = parts[0], parts[1], parts[2], parts[3]
		limits[model] = {
			"rpm": _parse_num(rpm_s),
			"tpm": _parse_num(tpm_s),
			"rpd": _parse_num(rpd_s),
		}
	return limits


class RateLimiter:
	"""Track per-model request counts and enforce RPM/TPM/RPD limits."""

	def __init__(self, limits_path: Path):
		self._limits = _parse_rate_limits(limits_path)
		# Sliding windows: model -> list of timestamps
		self._rpm_window: dict[str, list[float]] = defaultdict(list)
		self._tpm_window: dict[str, list[tuple[float, int]]] = defaultdict(list)
		self._rpd_window: dict[str, list[float]] = defaultdict(list)

	def _estimate_tokens(self, text: str) -> int:
		"""Rough token estimate: ~4 chars per token."""
		return max(1, len(text) // 4)

	def _prune_windows(self, model: str, window_minutes: int = 1):
		"""Remove expired entries from sliding windows."""
		cutoff = time.time() - (window_minutes * 60)
		self._rpm_window[model] = [
			t for t in self._rpm_window[model] if t > cutoff
		]
		self._tpm_window[model] = [
			(t, tok) for t, tok in self._tpm_window[model] if t > cutoff
		]
		self._rpd_window[model] = [
			t for t in self._rpd_window[model] if t > cutoff
		]

	def wait_if_needed(self, model: str, prompt_text: str) -> float:
		"""Check rate limits and sleep if needed. Returns actual delay applied.

		For local/non-Gemini models, no throttling is applied.
		"""
		if model not in self._limits:
			# Local model or unknown — no throttling
			return 0.0

		limit = self._limits[model]
		rpm = limit["rpm"]
		tpm = limit["tpm"]
		rpd = limit["rpd"]
		tokens = self._estimate_tokens(prompt_text)

		self._prune_windows(model)

		delay = 0.0

		# RPM check
		rpm_count = len(self._rpm_window[model])
		if rpm_count >= rpm:
			oldest = self._rpm_window[model][0]
			wait = 60.0 - (time.time() - oldest) + 0.1
			if wait > 0:
				logging.info("RPM limit reached for %s, waiting %.1fs", model, wait)
				delay = max(delay, wait)

		# TPM check
		tpm_used = sum(tok for _, tok in self._tpm_window[model])
		if tpm_used + tokens > tpm:
			# Wait until some capacity frees up — rough estimate
			if self._tpm_window[model]:
				oldest_time, oldest_tokens = self._tpm_window[model][0]
				wait = 60.0 - (time.time() - oldest_time) + 0.1
				if wait > 0:
					logging.info("TPM limit reached for %s, waiting %.1fs", model, wait)
					delay = max(delay, wait)

		# RPD check
		rpd_count = len(self._rpd_window[model])
		if rpd_count >= rpd:
			logging.info("RPD limit reached for %s", model)
			delay = max(delay, 60.0)

		if delay > 0:
			time.sleep(delay)

		# Record this request
		now = time.time()
		self._rpm_window[model].append(now)
		self._tpm_window[model].append((now, tokens))
		self._rpd_window[model].append(now)

		return delay
