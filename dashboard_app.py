import os
import uuid
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

from extract_messages import run_pipeline


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_ROOT = BASE_DIR / "uploads"
DB_PATH = BASE_DIR / "runs.db"


load_dotenv(override=True)

app = Flask(__name__)


def init_db() -> None:
    """Initialize the SQLite database for storing run history."""
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS group_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                group_name TEXT NOT NULL,
                no_messages_sent INTEGER NOT NULL,
                date_sent TEXT NOT NULL,
                run_timestamp TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def record_group_runs(run_id: str, entries: List[Dict]) -> None:
    """Persist per-group run summary entries to the database."""
    if not entries:
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        for entry in entries:
            cur.execute(
                """
                INSERT INTO group_runs (run_id, group_name, no_messages_sent, date_sent, run_timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    entry.get("group_name", "Unknown"),
                    int(entry.get("no_messages_sent", 0)),
                    entry.get("date_sent", ""),
                    entry.get("run_timestamp", datetime.utcnow().isoformat()),
                ),
            )
        conn.commit()
    finally:
        conn.close()


def get_dates_with_history() -> List[str]:
    """Return a list of distinct dates for which history exists."""
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT date_sent FROM group_runs ORDER BY date_sent DESC")
        rows = cur.fetchall()
        return [row[0] for row in rows]
    finally:
        conn.close()


def get_summary_by_date(date_str: str) -> List[Dict]:
    """Return all group run entries for a given date (no aggregation)."""
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT group_name, no_messages_sent, date_sent, run_timestamp
            FROM group_runs
            WHERE date_sent = ?
            ORDER BY run_timestamp DESC, group_name ASC
            """,
            (date_str,),
        )
        rows = cur.fetchall()
        result: List[Dict] = []
        for group_name, no_messages_sent, date_sent, run_timestamp in rows:
            result.append(
                {
                    "group_name": group_name,
                    "no_messages_sent": no_messages_sent,
                    "date_sent": date_sent,
                    "run_timestamp": run_timestamp,
                }
            )
        return result
    finally:
        conn.close()


def get_summary_aggregate(mode: str) -> List[Dict]:
    """
    Aggregate history by the requested period.

    mode: one of ['day', 'date', 'week', 'month', 'year']
    """
    mode = mode.lower()
    if mode not in ("day", "date", "week", "month", "year"):
        return []

    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT group_name, no_messages_sent, date_sent
            FROM group_runs
            """
        )
        rows = cur.fetchall()

        aggregates = {}
        for group_name, no_messages_sent, date_sent in rows:
            try:
                d = datetime.fromisoformat(date_sent).date()
            except Exception:
                # Skip invalid dates
                continue

            if mode in ("day", "date"):
                period_label = d.isoformat()
            elif mode == "week":
                iso_year, iso_week, _ = d.isocalendar()
                period_label = f"{iso_year}-W{iso_week:02d}"
            elif mode == "month":
                period_label = f"{d.year}-{d.month:02d}"
            else:  # year
                period_label = f"{d.year}"

            key = (group_name, period_label)
            if key not in aggregates:
                aggregates[key] = {
                    "group_name": group_name,
                    "period": period_label,
                    "total_messages": 0,
                    "runs": 0,
                }

            aggregates[key]["total_messages"] += int(no_messages_sent)
            aggregates[key]["runs"] += 1

        # Sort by period desc, then group asc
        result = sorted(
            aggregates.values(),
            key=lambda x: (x["period"], x["group_name"]),
            reverse=True,
        )
        return result
    finally:
        conn.close()


def clear_all_history() -> int:
    """Delete all records from the group_runs table. Returns the number of deleted rows."""
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM group_runs")
        deleted_count = cur.rowcount
        conn.commit()
        return deleted_count
    finally:
        conn.close()


@app.route("/")
def index():
    """Serve the main dashboard page."""
    init_db()
    return render_template("dashboard.html")


@app.route("/upload-chats", methods=["POST"])
def upload_chats():
    """
    Accept one or more exported WhatsApp chat .txt files and store them in
    a structured uploads directory.
    """
    init_db()
    files = request.files.getlist("chats")
    if not files:
        return jsonify({"success": False, "error": "No chat files uploaded."}), 400

    upload_id = str(uuid.uuid4())
    base_dir = UPLOAD_ROOT / upload_id
    base_dir.mkdir(parents=True, exist_ok=True)

    groups: List[Dict] = []
    for f in files:
        if not f.filename.lower().endswith(".txt"):
            # Skip non-txt files silently
            continue
        # Use the stem of the filename as the group name (e.g., HomeHNI_chat.txt -> HomeHNI_chat)
        original_name = Path(f.filename).stem or "Group"
        group_dir = base_dir / original_name
        group_dir.mkdir(parents=True, exist_ok=True)
        dest = group_dir / "chat.txt"
        f.save(dest)
        groups.append({"group_name": original_name, "folder": str(group_dir)})

    if not groups:
        return jsonify({"success": False, "error": "No valid .txt chat files uploaded."}), 400

    # Persist a simple manifest for this upload
    manifest_path = base_dir / "manifest.txt"
    with manifest_path.open("w", encoding="utf-8") as mf:
        for g in groups:
            mf.write(f"{g['group_name']}|{g['folder']}\n")

    return jsonify({"success": True, "upload_id": upload_id, "groups": [g["group_name"] for g in groups]})


@app.route("/run-pipeline", methods=["POST"])
def run_pipeline_endpoint():
    """
    Run the property webpage + WhatsApp pipeline for all uploaded groups for a given date.
    Expects:
        - upload_id: ID returned from /upload-chats
        - date: date string in DD/MM/YYYY or DD/MM/YY format
    """
    init_db()
    data = request.get_json(silent=True) or request.form
    upload_id = data.get("upload_id")
    date_input = data.get("date")

    if not upload_id or not date_input:
        return jsonify({"success": False, "error": "Missing upload_id or date."}), 400

    base_dir = UPLOAD_ROOT / upload_id
    if not base_dir.exists():
        return jsonify({"success": False, "error": "Invalid upload_id."}), 400

    manifest_path = base_dir / "manifest.txt"
    if not manifest_path.exists():
        return jsonify({"success": False, "error": "Manifest not found for upload_id."}), 400

    run_id = str(uuid.uuid4())
    summary_entries: List[Dict] = []
    # Read manifest and run pipeline for each group folder
    with manifest_path.open("r", encoding="utf-8") as mf:
        for line in mf:
            line = line.strip()
            if not line:
                continue
            try:
                group_name, folder_str = line.split("|", 1)
            except ValueError:
                continue
            folder_path = Path(folder_str)
            result = run_pipeline(folder_path, date_input)
            if result is None:
                continue

            property_messages = result.get("property_messages") or []
            no_messages_sent = len(property_messages)

            if no_messages_sent <= 0:
                continue

            date_sent = result.get("date")
            if hasattr(date_sent, "strftime"):
                date_str = date_sent.strftime("%Y-%m-%d")
            else:
                date_str = str(date_sent)

            entry = {
                "group_name": group_name,
                "no_messages_sent": no_messages_sent,
                "date_sent": date_str,
                "run_timestamp": datetime.utcnow().isoformat(),
            }
            summary_entries.append(entry)

    # Record in DB
    record_group_runs(run_id, summary_entries)

    return jsonify({"success": True, "run_id": run_id, "entries": summary_entries})


@app.route("/summary/dates", methods=["GET"])
def summary_dates():
    """Return the list of dates for which history exists."""
    init_db()
    dates = get_dates_with_history()
    return jsonify({"success": True, "dates": dates})


@app.route("/summary/by-date", methods=["GET"])
def summary_by_date():
    """Return all group runs for a specific date (YYYY-MM-DD)."""
    init_db()
    date_str = request.args.get("date")
    if not date_str:
        return jsonify({"success": False, "error": "Missing date parameter."}), 400

    entries = get_summary_by_date(date_str)
    return jsonify({"success": True, "entries": entries})


@app.route("/summary/aggregate", methods=["GET"])
def summary_aggregate():
    """Return aggregated history by day/week/month/year."""
    init_db()
    mode = (request.args.get("mode") or "day").lower()
    if mode not in ("day", "date", "week", "month", "year"):
        return jsonify({"success": False, "error": "Invalid mode. Use day/date/week/month/year."}), 400

    entries = get_summary_aggregate(mode)
    return jsonify({"success": True, "entries": entries, "mode": mode})


@app.route("/clear-history", methods=["POST"])
def clear_history():
    """Clear all history from the database."""
    init_db()
    try:
        deleted_count = clear_all_history()
        return jsonify({"success": True, "deleted_count": deleted_count})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def create_app() -> Flask:
    """Factory to create the Flask app (useful for future extensions)."""
    init_db()
    return app


if __name__ == "__main__":
    init_db()
    # Bind to localhost only for safety; adjust host/port as needed.
    app.run(host="127.0.0.1", port=int(os.getenv("DASHBOARD_PORT", "5000")), debug=True)


