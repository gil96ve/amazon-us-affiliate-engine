#!/usr/bin/env python3
"""Linter determinista de contratos y compliance para amazon-us-affiliate-engine.

Uso:
    python scripts/validate_contracts.py [--root RUTA] [--strict]

Solo usa la librería estándar de Python. Nunca imprime valores de secretos.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_VERSION = "1.0"
DISCLOSURE = "As an Amazon Associate I earn from qualifying purchases."
CTA = "Check Latest Price on Amazon"
TAG = "vettedgearlab-20"

CLICHES = ("game changer", "buy now", "must-have", "life-changing", "best seller")
PRICE_RE = re.compile(r"(?:\$\s*\d|\bUSD\s*\d|\bonly\s+\d)", re.IGNORECASE)
SECRET_PATTERNS = (
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{20,}", re.IGNORECASE),
)
INJECTION_RE = re.compile(
    r"ignore (?:all )?(?:previous|prior) instructions|print (?:your )?(?:token|secret)|"
    r"reveal (?:your )?system prompt|do not follow (?:the )?rules",
    re.IGNORECASE,
)
PHYSICAL_PRODUCT_RE = re.compile(
    r"\b(product|item|device|unit|package|box|strap|object)\b", re.IGNORECASE
)


def _walk_strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _walk_strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_strings(item)


def _check_text(field: str, value: Any, errors: list[str]) -> None:
    """Valida una cadena sin filtrar su contenido sensible."""
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field}: EMPTY_FIELD")
        return
    for pattern in SECRET_PATTERNS:
        if pattern.search(value):
            errors.append(f"{field}: SECRET_EXPOSED")
            return
    if INJECTION_RE.search(value):
        errors.append(f"{field}: PROMPT_INJECTION")
    lowered = value.lower()
    if any(cliche in lowered for cliche in CLICHES):
        errors.append(f"{field}: CLICHE")
    if PRICE_RE.search(value):
        errors.append(f"{field}: STATIC_PRICE")


def _load_json(path: Path, rel: str, errors: list[str]) -> Any:
    if not path.exists():
        errors.append(f"{rel}: MISSING_FILE")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        errors.append(f"{rel}: INVALID_JSON ({type(exc).__name__})")
        return None


def _records(doc: Any, keys: tuple[str, ...], rel: str, errors: list[str],
             warnings: list[str]) -> list[Any]:
    if doc is None:
        return []
    if isinstance(doc, list):
        records = doc
    elif isinstance(doc, dict):
        records = None
        for key in keys:
            if key in doc:
                records = doc[key]
                break
        if records is None:
            errors.append(f"{rel}: MISSING_FIELD records")
            return []
    else:
        errors.append(f"{rel}: INVALID_ROOT_TYPE")
        return []
    if not isinstance(records, list):
        errors.append(f"{rel}: INVALID_RECORDS_TYPE")
        return []
    if not records:
        warnings.append(f"{rel}: NO_ARTIFACTS_YET")
    return records


def _common(record: Any, producer: str, field: str, errors: list[str]) -> None:
    if not isinstance(record, dict):
        errors.append(f"{field}: INVALID_RECORD")
        return
    if record.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"{field}: SCHEMA_VERSION")
    if not isinstance(record.get("run_id"), str) or not record["run_id"].strip():
        errors.append(f"{field}: MISSING_FIELD run_id")
    if record.get("producer") != producer:
        errors.append(f"{field}: PRODUCER_MISMATCH")
    digest = record.get("input_sha256")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        errors.append(f"{field}: INPUT_SHA256")
    if not isinstance(record.get("created_at"), str) or not record["created_at"].strip():
        errors.append(f"{field}: MISSING_FIELD created_at")


def validate_state(state: Any, errors: list[str]) -> None:
    field = "data/state_memory.json"
    if not isinstance(state, dict):
        errors.append(f"{field}: INVALID_ROOT_TYPE")
        return
    for key in ("project_version", "amazon_config", "processed_asins", "niches_tested",
                "winning_hooks_history", "last_updated"):
        if key not in state:
            errors.append(f"{field}: MISSING_FIELD {key}")
    config = state.get("amazon_config")
    if not isinstance(config, dict):
        errors.append(f"{field}: MISSING_FIELD amazon_config")
        return
    if config.get("store_id") != TAG:
        errors.append(f"{field}: STORE_ID_MISMATCH")
    if config.get("allow_static_prices") is not False:
        errors.append(f"{field}: STATIC_PRICES_ALLOWED")
    if config.get("require_ftc_disclosure") is not True:
        errors.append(f"{field}: DISCLOSURE_DISABLED")
    for key in ("processed_asins", "niches_tested", "winning_hooks_history"):
        if not isinstance(state.get(key), list):
            errors.append(f"{field}: INVALID_LIST {key}")
    for text in _walk_strings(state):
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"{field}: SECRET_EXPOSED")
                break


def validate_products(records: list[Any], errors: list[str]) -> None:
    for index, record in enumerate(records):
        field = f"data/products.json[{index}]"
        _common(record, "01_SKILL_PRODUCT_ANALYST", field, errors)
        if not isinstance(record, dict):
            continue
        if record.get("status") != "OK":
            errors.append(f"{field}: STATUS_NOT_OK")
        product = record.get("product")
        if not isinstance(product, dict):
            errors.append(f"{field}: MISSING_FIELD product")
            continue
        for key in ("asin", "source_url", "niche_keyword", "title", "problem",
                    "target_audience_us", "benefits", "objections", "specs_verified",
                    "missing_fields"):
            if key not in product:
                errors.append(f"{field}.product: MISSING_FIELD {key}")
        if not (product.get("asin") or product.get("niche_keyword")):
            errors.append(f"{field}.product: MISSING_FIELD asin|keyword")
        if product.get("specs_verified") is not True:
            errors.append(f"{field}.product: SPECS_NOT_VERIFIED")
        if product.get("missing_fields") != []:
            errors.append(f"{field}.product: MISSING_FIELDS_NOT_EMPTY")
        benefits = product.get("benefits")
        if not isinstance(benefits, list) or len(benefits) != 3:
            errors.append(f"{field}.product.benefits: EXPECT_3")
        else:
            for i, benefit in enumerate(benefits):
                bfield = f"{field}.product.benefits[{i}]"
                if not isinstance(benefit, dict):
                    errors.append(f"{bfield}: INVALID_RECORD")
                    continue
                if benefit.get("source") not in ("user", "amazon_page"):
                    errors.append(f"{bfield}: SOURCE_NOT_VERIFIABLE")
                if benefit.get("verified") is not True:
                    errors.append(f"{bfield}: NOT_VERIFIED")
                _check_text(f"{bfield}.claim", benefit.get("claim"), errors)
                _check_text(f"{bfield}.evidence", benefit.get("evidence"), errors)
        objections = product.get("objections")
        if not isinstance(objections, list) or len(objections) < 3:
            errors.append(f"{field}.product.objections: EXPECT_3")
        else:
            for i, objection in enumerate(objections):
                ofield = f"{field}.product.objections[{i}]"
                if not isinstance(objection, dict):
                    errors.append(f"{ofield}: INVALID_RECORD")
                    continue
                _check_text(f"{ofield}.objection", objection.get("objection"), errors)
                _check_text(f"{ofield}.response", objection.get("response"), errors)
        for key in ("title", "problem", "target_audience_us"):
            _check_text(f"{field}.product.{key}", product.get(key), errors)


def validate_assets(records: list[Any], errors: list[str]) -> None:
    for index, record in enumerate(records):
        field = f"data/content_assets.json[{index}]"
        _common(record, "02_SKILL_VIRAL_SCRIPTER", field, errors)
        if not isinstance(record, dict):
            continue
        if record.get("status") != "OK":
            errors.append(f"{field}: STATUS_NOT_OK")
        if record.get("language") != "en-US":
            errors.append(f"{field}: LANGUAGE_NOT_EN_US")
        for key, expected in (("pain_points", 10), ("hooks", 10)):
            values = record.get(key)
            if not isinstance(values, list) or len(values) != expected:
                errors.append(f"{field}.{key}: EXPECT_{expected}")
                continue
            for i, value in enumerate(values):
                _check_text(f"{field}.{key}[{i}]", value, errors)
        combo = record.get("winning_combo")
        if not isinstance(combo, dict):
            errors.append(f"{field}.winning_combo: MISSING_FIELD")
        else:
            for key in ("pain_point_index", "hook_index"):
                value = combo.get(key)
                if not isinstance(value, int) or not 0 <= value < 10:
                    errors.append(f"{field}.winning_combo: INVALID_INDEX {key}")
            _check_text(f"{field}.winning_combo.justification",
                        combo.get("justification"), errors)
        script = record.get("script_30s")
        if not isinstance(script, list) or len(script) != 6:
            errors.append(f"{field}.script_30s: EXPECT_6_BEATS")
        else:
            expected_start = 0
            for i, beat in enumerate(script):
                bfield = f"{field}.script_30s[{i}]"
                if not isinstance(beat, dict):
                    errors.append(f"{bfield}: INVALID_RECORD")
                    continue
                match = re.fullmatch(r"(\d+)-(\d+)s", str(beat.get("time", "")))
                if not match:
                    errors.append(f"{bfield}: INVALID_TIME")
                else:
                    start, end = int(match.group(1)), int(match.group(2))
                    if start != expected_start or end - start != 5:
                        errors.append(f"{bfield}: NON_CONTIGUOUS_5S")
                    expected_start = end
                _check_text(f"{bfield}.voiceover", beat.get("voiceover"), errors)
                visual = beat.get("visual")
                _check_text(f"{bfield}.visual", visual, errors)
                if isinstance(visual, str) and not PHYSICAL_PRODUCT_RE.search(visual):
                    errors.append(f"{bfield}: MISSING_PHYSICAL_PRODUCT_VISUAL")
            if expected_start != 30:
                errors.append(f"{field}.script_30s: TOTAL_NOT_30S")
        media = record.get("media_prompts")
        if not isinstance(media, dict):
            errors.append(f"{field}.media_prompts: MISSING_FIELD")
        else:
            for key in ("images", "video_clips"):
                values = media.get(key)
                if not isinstance(values, list) or len(values) < 2:
                    errors.append(f"{field}.media_prompts.{key}: EXPECT_2")
                else:
                    for i, value in enumerate(values):
                        _check_text(f"{field}.media_prompts.{key}[{i}]", value, errors)
        titles = record.get("title_thumbnail_ideas")
        if not isinstance(titles, list) or len(titles) != 3:
            errors.append(f"{field}.title_thumbnail_ideas: EXPECT_3")
        else:
            for i, item in enumerate(titles):
                tfield = f"{field}.title_thumbnail_ideas[{i}]"
                if not isinstance(item, dict):
                    errors.append(f"{tfield}: INVALID_RECORD")
                    continue
                _check_text(f"{tfield}.title", item.get("title"), errors)
                _check_text(f"{tfield}.thumbnail", item.get("thumbnail"), errors)
        questions = record.get("comment_questions")
        if not isinstance(questions, list) or len(questions) != 3:
            errors.append(f"{field}.comment_questions: EXPECT_3")
        else:
            for i, question in enumerate(questions):
                _check_text(f"{field}.comment_questions[{i}]", question, errors)


def validate_html(path: Path, errors: list[str]) -> None:
    field = "docs/index.html"
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        errors.append(f"{field}: UNREADABLE ({type(exc).__name__})")
        return
    lowered = text.lower()
    required = (
        "<!doctype html>", '<html lang="en">', 'name="viewport"', "<style",
        'id="hero"', 'id="problem"', 'id="comparison"', 'id="cta"',
        'id="affiliate-cta"', 'id="disclosure"', "</html>",
    )
    for token in required:
        if token not in lowered:
            errors.append(f"{field}: MISSING_MARKUP {token}")
    if DISCLOSURE not in text:
        errors.append(f"{field}: DISCLOSURE_MISSING")
    if CTA not in text:
        errors.append(f"{field}: CTA_MISSING")
    if TAG not in text:
        errors.append(f"{field}: AFFILIATE_TAG_MISSING")
    anchor = re.search(r"<a\b[^>]*\bid=[\"']affiliate-cta[\"'][^>]*>", lowered)
    if not anchor:
        errors.append(f"{field}: AFFILIATE_ANCHOR_MISSING")
    else:
        tag = anchor.group(0)
        if "amazon.com" not in tag or TAG not in tag:
            errors.append(f"{field}: AFFILIATE_HREF_INVALID")
        if "nofollow" not in tag or "noopener" not in tag:
            errors.append(f"{field}: AFFILIATE_REL_INVALID")
        if 'target="_blank"' not in tag:
            errors.append(f"{field}: AFFILIATE_TARGET_INVALID")
    external_patterns = (
        re.compile(r"<script[^>]+\bsrc\s*=", re.IGNORECASE),
        re.compile(r"<link[^>]+\bhref\s*=\s*[\"']https?://", re.IGNORECASE),
        re.compile(r"@import", re.IGNORECASE),
        re.compile(r"url\(\s*[\"']?https?://", re.IGNORECASE),
        re.compile(r"<img[^>]+\bsrc\s*=\s*[\"']https?://", re.IGNORECASE),
    )
    for pattern in external_patterns:
        if pattern.search(text):
            errors.append(f"{field}: EXTERNAL_RESOURCE")
            break
    if PRICE_RE.search(text):
        errors.append(f"{field}: STATIC_PRICE")
    if any(cliche in lowered for cliche in CLICHES):
        errors.append(f"{field}: CLICHE")
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            errors.append(f"{field}: SECRET_EXPOSED")
            break


def validate_all(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    state = _load_json(root / "data" / "state_memory.json", "data/state_memory.json", errors)
    if state is not None:
        validate_state(state, errors)
    products = _load_json(root / "data" / "products.json", "data/products.json", errors)
    product_records = _records(products, ("records", "products"), "data/products.json",
                               errors, warnings)
    validate_products(product_records, errors)
    assets = _load_json(root / "data" / "content_assets.json",
                        "data/content_assets.json", errors)
    asset_records = _records(assets, ("records", "assets"), "data/content_assets.json",
                             errors, warnings)
    validate_assets(asset_records, errors)
    html_path = root / "docs" / "index.html"
    if not html_path.exists():
        errors.append("docs/index.html: MISSING_FILE")
    else:
        validate_html(html_path, errors)
    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "counts": {"products": len(product_records), "assets": len(asset_records)},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT), help="Raíz del monorepo")
    parser.add_argument("--strict", action="store_true", help="Tratar warnings como errores")
    args = parser.parse_args()
    report = validate_all(Path(args.root).resolve())
    if args.strict and report["warnings"]:
        report["errors"].extend(f"WARNING: {item}" for item in report["warnings"])
        report["ok"] = False
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
