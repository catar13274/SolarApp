"""Gemini-based invoice parser."""

import json
import re
from typing import Dict

import httpx

from .document_parser import extract_document_text


def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _normalize_invoice_payload(payload: Dict) -> Dict:
    items = payload.get("items", [])
    normalized_items = []
    for item in items:
        normalized_items.append(
            {
                "description": str(item.get("description", "")).strip(),
                "sku": str(item.get("sku", "")).strip(),
                "quantity": float(item.get("quantity", 0) or 0),
                "unit_price": float(item.get("unit_price", 0) or 0),
                "total_price": float(item.get("total_price", 0) or 0),
            }
        )

    return {
        "invoice_number": str(payload.get("invoice_number", "")).strip(),
        "invoice_date": str(payload.get("invoice_date", "")).strip(),
        "supplier_name": str(payload.get("supplier_name", "")).strip(),
        "currency": str(payload.get("currency", "RON")).strip() or "RON",
        "total_amount": float(payload.get("total_amount", 0) or 0),
        "items": normalized_items,
    }


async def parse_invoice_with_gemini(
    *,
    file_path: str,
    file_extension: str,
    api_key: str,
    model: str = "gemini-1.5-flash",
) -> Dict:
    """Extract invoice data from file text using Gemini."""
    text = extract_document_text(file_path, file_extension)
    if not text.strip():
        return {
            "invoice_number": "",
            "invoice_date": "",
            "supplier_name": "",
            "currency": "RON",
            "total_amount": 0.0,
            "items": [],
        }

    prompt = f"""
You are an invoice extraction engine.
Extract invoice details from this text and return ONLY valid JSON, no markdown, no comments.

Required JSON shape:
{{
  "invoice_number": "string",
  "invoice_date": "YYYY-MM-DD or empty string",
  "supplier_name": "string",
  "currency": "RON|EUR|USD|other",
  "total_amount": number,
  "items": [
    {{
      "description": "string",
      "sku": "string",
      "quantity": number,
      "unit_price": number,
      "total_price": number
    }}
  ]
}}

Rules:
- If a field is missing, return empty string or 0.
- Keep decimals as numbers.
- Do not invent items.

Invoice text:
{text}
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1},
    }

    async with httpx.AsyncClient(timeout=45.0) as client:
        response = await client.post(url, json=body)
        response.raise_for_status()
        data = response.json()

    candidates = data.get("candidates", [])
    if not candidates:
        raise ValueError("Gemini returned no candidates.")

    parts = candidates[0].get("content", {}).get("parts", [])
    text_parts = [part.get("text", "") for part in parts if part.get("text")]
    if not text_parts:
        raise ValueError("Gemini response does not contain text output.")

    raw = _strip_code_fences("\n".join(text_parts))
    parsed = json.loads(raw)
    return _normalize_invoice_payload(parsed)
