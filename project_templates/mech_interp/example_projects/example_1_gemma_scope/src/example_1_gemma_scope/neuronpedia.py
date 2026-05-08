"""Neuronpedia URL helpers and explanation fetcher.

Neuronpedia (https://www.neuronpedia.org) hosts auto-interpreted dashboards for many
SAE releases — including Gemma Scope 2 features for Gemma 3. This module:

  - builds the dashboard / API URL for a given (model, source, feature_index)
  - fetches the top auto-interp explanation via Neuronpedia's public JSON API
  - parallelizes a batch fetch via ThreadPoolExecutor
  - never raises on failure: returns None, so an offline/transient/500 failure does
    not break the analysis script.

Source-name conventions (verified 2026-05-05):

  Gemma Scope 2 1B residual:   "{layer}-gemmascope-2-res-{width}"   e.g. "13-gemmascope-2-res-16k"
  Gemma Scope 2 1B mlp:        "{layer}-gemmascope-2-mlp-{width}"
  Gemma Scope 2 1B attention:  "{layer}-gemmascope-2-att-{width}"

Note: the SAELens sae_id includes an L0 bucket (small/medium/big), but Neuronpedia
hosts dashboards only for the canonical (medium) variant per (layer, width). The L0
bucket is therefore NOT part of the Neuronpedia source name.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import Iterable

NEURONPEDIA_BASE = "https://www.neuronpedia.org"


def gemma_scope_2_source(layer: int, site: str = "res", width: str = "16k") -> str:
    """Neuronpedia source name for a Gemma Scope 2 SAE on a Gemma 3 model.

    Args:
        layer: layer index (must be a layer Gemma Scope 2 actually publishes — 1B-pt-res
               only ships {7, 13, 17, 22}).
        site: "res" | "mlp" | "att".
        width: "16k" | "65k" | "262k" | "1m".
    """
    return f"{layer}-gemmascope-2-{site}-{width}"


def dashboard_url(model_short: str, source: str, feature_index: int) -> str:
    """Human-browsable dashboard URL for one feature."""
    return f"{NEURONPEDIA_BASE}/{model_short}/{source}/{feature_index}"


def api_url(model_short: str, source: str, feature_index: int) -> str:
    """JSON API URL for one feature's metadata + explanations."""
    return f"{NEURONPEDIA_BASE}/api/feature/{model_short}/{source}/{feature_index}"


def fetch_explanation(
    model_short: str,
    source: str,
    feature_index: int,
    timeout: float = 3.0,
) -> str | None:
    """Fetch the top auto-interp explanation for a single feature.

    Returns the explanation string, or None on any failure (network error, 4xx/5xx,
    invalid JSON, no explanations available). The caller can treat None as "label
    unavailable" and continue.
    """
    url = api_url(model_short, source, feature_index)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "mi-components/0.1"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return None
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, ValueError):
        return None
    explanations = data.get("explanations") or []
    if not explanations:
        return None
    return explanations[0].get("description")


def fetch_explanations_parallel(
    queries: Iterable[tuple[str, str, int]],
    timeout_per: float = 3.0,
    max_workers: int = 8,
) -> dict[tuple[str, str, int], str | None]:
    """Fetch many feature explanations in parallel.

    Args:
        queries: iterable of (model_short, source, feature_index) tuples.
        timeout_per: per-request timeout in seconds.
        max_workers: max concurrent HTTP connections.

    Returns: dict mapping each query tuple to its explanation string or None.
    """
    queries = list(queries)
    out: dict[tuple[str, str, int], str | None] = {}
    if not queries:
        return out
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        future_to_key = {
            ex.submit(fetch_explanation, m, s, i, timeout_per): (m, s, i) for m, s, i in queries
        }
        for fut, key in future_to_key.items():
            try:
                out[key] = fut.result()
            except Exception:
                out[key] = None
    return out
