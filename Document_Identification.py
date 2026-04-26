"""
Document Identification & Analysis Web App
Supported formats: PDF, PNG, JPG/JPEG, WEBP, TXT, CSV
Run: venv\Scripts\python Document_Identification.py  →  http://localhost:5001
"""

import os
import io
import re
import base64
import json
import uuid

from flask import Flask, render_template, request, jsonify, session, send_from_directory
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "docid-dev-secret-key-change-in-prod")

client = Anthropic()

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
RULES_FILE  = os.path.join(BASE_DIR, "keyword_rules.json")
STORE_FILE  = os.path.join(BASE_DIR, "doc_store.json")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

MEDIA_TYPES = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg",
    "png": "image/png",  "webp": "image/webp", "gif": "image/gif",
}


# ── Store persistence ─────────────────────────────────────────────────────────
# { sid: { id, filename, file_path, text, is_image, image_media_type,
#           identification, chat_history, rule_matches } }

def _load_store():
    if os.path.exists(STORE_FILE):
        try:
            with open(STORE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save_store():
    with open(STORE_FILE, "w", encoding="utf-8") as f:
        json.dump(_store, f, ensure_ascii=False)

_store = _load_store()


# ── Rule persistence ───────────────────────────────────────────────────────────

def load_rules():
    if os.path.exists(RULES_FILE):
        try:
            with open(RULES_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_rules(rules):
    with open(RULES_FILE, "w") as f:
        json.dump(rules, f, indent=2)

def apply_rules(text: str) -> list:
    text_lower = text.lower()
    matches = []
    for rule in load_rules():
        matched = [kw for kw in rule.get("keywords", []) if kw.lower() in text_lower]
        if matched:
            matches.append({
                "rule_id": rule["id"], "label": rule["label"],
                "matched_keywords": matched,
                "total_keywords": len(rule.get("keywords", [])),
            })
    return matches


# ── Document helpers ───────────────────────────────────────────────────────────

def extract_pdf_text(file_bytes: bytes) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages = []
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                if text.strip():
                    pages.append(f"[Page {i + 1}]\n{text}")
            return "\n\n".join(pages)
    except Exception as e:
        return f"[PDF extraction error: {e}]"


def load_image_b64(doc: dict) -> str:
    file_path = doc.get("file_path", "")
    if file_path and os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return base64.standard_b64encode(f.read()).decode("utf-8")
    return ""


def identify_document(text=None, image_b64=None, image_media_type=None, filename=""):
    prompt = (
        "Analyze this document and respond ONLY with valid JSON using this schema:\n"
        "{\n"
        '  "document_type": "e.g. Invoice, Balance Sheet, Bank Statement",\n'
        '  "confidence": "High | Medium | Low",\n'
        '  "summary": "2-3 sentence summary",\n'
        '  "key_fields": { "field_name": "value" },\n'
        '  "date": "document date or null",\n'
        '  "parties": ["company or person names"],\n'
        '  "currency": "currency code or null",\n'
        '  "total_amount": "primary total if financial, else null",\n'
        '  "period": "reporting period or null"\n'
        "}\n\n"
        "Common types: Balance Sheet, Income Statement, Cash Flow Statement, Invoice, "
        "Purchase Order, Bank Statement, Tax Return, Payroll Statement, Expense Report, "
        "Receipt, Contract, Quotation, Credit Note, Debit Note, Accounts Receivable, "
        "Accounts Payable, Delivery Note, Insurance Policy."
    )
    content = (
        [
            {"type": "image", "source": {"type": "base64",
             "media_type": image_media_type, "data": image_b64}},
            {"type": "text", "text": prompt},
        ]
        if image_b64
        else f"Filename: {filename}\n\nContent:\n{(text or '')[:10000]}\n\n{prompt}"
    )
    resp = client.messages.create(
        model="claude-opus-4-6", max_tokens=1024,
        messages=[{"role": "user", "content": content}],
    )
    raw = re.sub(r"^```(?:json)?\n?", "", resp.content[0].text.strip())
    raw = re.sub(r"\n?```$", "", raw)
    try:
        return json.loads(raw)
    except Exception:
        return {"document_type": "Unknown", "confidence": "Low", "summary": raw, "key_fields": {}}


def get_doc(sid):
    return _store.get(sid)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    if "sid" not in session:
        session["sid"] = str(uuid.uuid4())
    return render_template("document_id.html")


@app.route("/api/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "No file selected"}), 400

    sid        = session.setdefault("sid", str(uuid.uuid4()))
    filename   = f.filename
    ext        = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    file_bytes = f.read()
    is_image   = ext in MEDIA_TYPES

    if not is_image and ext not in ("pdf", "txt", "csv"):
        return jsonify({"error": "Unsupported type. Use PDF, PNG, JPG, WEBP, TXT, or CSV."}), 400

    # Remove old file if one exists
    old = _store.get(sid, {})
    old_fp = old.get("file_path", "")
    if old_fp and os.path.exists(old_fp):
        os.remove(old_fp)

    # Save new file to disk
    safe_name = re.sub(r"[^\w.\-]", "_", filename)
    file_path = os.path.join(UPLOADS_DIR, f"{sid}_{safe_name}")
    with open(file_path, "wb") as out:
        out.write(file_bytes)

    # Extract text or prepare image
    text             = ""
    image_media_type = None
    image_b64        = None

    if is_image:
        image_media_type = MEDIA_TYPES[ext]
        image_b64        = base64.standard_b64encode(file_bytes).decode("utf-8")
    elif ext == "pdf":
        text = extract_pdf_text(file_bytes)
    else:
        text = file_bytes.decode("utf-8", errors="replace")

    identification = identify_document(
        text=text if not is_image else None,
        image_b64=image_b64, image_media_type=image_media_type,
        filename=filename,
    )
    rule_matches = apply_rules(text) if text else []

    _store[sid] = {
        "filename": filename, "file_path": file_path,
        "text": text, "is_image": is_image,
        "image_media_type": image_media_type,
        "identification": identification,
        "chat_history": [], "rule_matches": rule_matches,
    }
    _save_store()

    return jsonify({
        "filename": filename, "identification": identification,
        "has_text": bool(text), "rule_matches": rule_matches,
    })


@app.route("/api/docs-state")
def docs_state():
    """Return current document state so the page can restore itself on reload."""
    sid = session.get("sid")
    doc = get_doc(sid)
    if not doc:
        return jsonify({"loaded": False})
    return jsonify({
        "loaded": True,
        "filename": doc["filename"],
        "identification": doc["identification"],
        "has_text": bool(doc.get("text")),
        "rule_matches": doc.get("rule_matches", []),
    })


@app.route("/api/download")
def download():
    sid = session.get("sid")
    doc = get_doc(sid)
    if not doc:
        return jsonify({"error": "No document loaded"}), 404
    fp = doc.get("file_path", "")
    if not fp or not os.path.exists(fp):
        return jsonify({"error": "File not found on disk"}), 404
    return send_from_directory(
        os.path.dirname(fp), os.path.basename(fp),
        as_attachment=True, download_name=doc["filename"],
    )


@app.route("/api/search", methods=["POST"])
def search():
    sid = session.get("sid")
    doc = get_doc(sid)
    if not doc:
        return jsonify({"error": "No document loaded"}), 400
    query = (request.get_json() or {}).get("query", "").strip()
    if not query:
        return jsonify({"matches": [], "count": 0})
    text = doc.get("text", "")
    if not text:
        return jsonify({"error": "Search unavailable for image documents. Use chat instead."}), 400
    matches     = []
    query_lower = query.lower()
    lines       = text.split("\n")
    for i, line in enumerate(lines):
        if query_lower in line.lower():
            context     = "\n".join(lines[max(0, i - 1):min(len(lines), i + 2)])
            highlighted = re.sub(f"({re.escape(query)})", r"<mark>\1</mark>", context, flags=re.IGNORECASE)
            matches.append({"line": i + 1, "context": highlighted})
    return jsonify({"matches": matches[:30], "count": len(matches), "query": query})


@app.route("/api/chat", methods=["POST"])
def chat():
    sid = session.get("sid")
    doc = get_doc(sid)
    if not doc:
        return jsonify({"error": "No document loaded. Please upload a document first."}), 400

    user_msg = (request.get_json() or {}).get("message", "").strip()
    if not user_msg:
        return jsonify({"error": "Empty message"}), 400

    history  = doc["chat_history"]
    doc_type = doc["identification"].get("document_type", "document")

    if doc["is_image"]:
        image_b64 = load_image_b64(doc)
        system    = (f"You are a document analysis assistant. The image is a {doc_type}. "
                     "Answer questions based on what is visible in the document.")
        if not history:
            messages = [{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64",
                 "media_type": doc["image_media_type"], "data": image_b64}},
                {"type": "text", "text": user_msg},
            ]}]
        else:
            first_q  = history[0]["content"]
            messages = [
                {"role": "user", "content": [
                    {"type": "image", "source": {"type": "base64",
                     "media_type": doc["image_media_type"], "data": image_b64}},
                    {"type": "text", "text": first_q},
                ]},
                *[{"role": h["role"], "content": h["content"]} for h in history[1:]],
                {"role": "user", "content": user_msg},
            ]
    else:
        doc_text = (doc.get("text") or "")[:15000]
        system   = (f"You are a document analysis assistant. The user uploaded a {doc_type}.\n\n"
                    f"Full document content:\n---\n{doc_text}\n---\n\n"
                    "Answer questions precisely. Reference specific values, dates, or sections. Be concise.")
        messages = history + [{"role": "user", "content": user_msg}]

    resp  = client.messages.create(model="claude-opus-4-6", max_tokens=1024, system=system, messages=messages)
    reply = resp.content[0].text

    history.append({"role": "user",      "content": user_msg})
    history.append({"role": "assistant", "content": reply})
    doc["chat_history"] = history[-20:]
    _save_store()

    return jsonify({"reply": reply})


@app.route("/api/clear", methods=["POST"])
def clear():
    sid = session.get("sid")
    doc = _store.pop(sid, None)
    if doc:
        fp = doc.get("file_path", "")
        if fp and os.path.exists(fp):
            os.remove(fp)
    _save_store()
    return jsonify({"success": True})


# ── Keyword classification rules ───────────────────────────────────────────────

@app.route("/api/rules", methods=["GET"])
def get_rules():
    return jsonify({"rules": load_rules()})

@app.route("/api/rules", methods=["POST"])
def add_rule():
    data     = request.get_json() or {}
    label    = data.get("label", "").strip()
    keywords = [k.strip() for k in data.get("keywords", []) if k.strip()]
    if not label or not keywords:
        return jsonify({"error": "Label and at least one keyword required"}), 400
    rules = load_rules()
    rule  = {"id": str(uuid.uuid4()), "label": label, "keywords": keywords}
    rules.append(rule)
    save_rules(rules)
    return jsonify({"rule": rule})

@app.route("/api/rules/<rule_id>", methods=["PUT"])
def update_rule(rule_id):
    data  = request.get_json() or {}
    rules = load_rules()
    for rule in rules:
        if rule["id"] == rule_id:
            if "label"    in data: rule["label"]    = data["label"].strip()
            if "keywords" in data: rule["keywords"]  = [k.strip() for k in data["keywords"] if k.strip()]
            save_rules(rules)
            return jsonify({"rule": rule})
    return jsonify({"error": "Rule not found"}), 404

@app.route("/api/rules/<rule_id>", methods=["DELETE"])
def delete_rule(rule_id):
    save_rules([r for r in load_rules() if r["id"] != rule_id])
    return jsonify({"success": True})

@app.route("/api/rules/reapply", methods=["POST"])
def reapply_rules():
    sid = session.get("sid")
    doc = get_doc(sid)
    if not doc:
        return jsonify({"rule_matches": []})
    rule_matches        = apply_rules(doc.get("text", "")) if not doc["is_image"] else []
    doc["rule_matches"] = rule_matches
    _save_store()
    return jsonify({"rule_matches": rule_matches})


if __name__ == "__main__":
    app.run(debug=True, port=5001)
