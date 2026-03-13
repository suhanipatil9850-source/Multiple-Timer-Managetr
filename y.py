import threading
import time
from datetime import datetime
from uuid import uuid4

from flask import Flask, redirect, render_template_string, request, url_for


app = Flask(__name__)
timers = []
timers_lock = threading.Lock()

PAGE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Multiple Timer Manager</title>
    <style>
        :root {
            color-scheme: light;
            --bg: #f4efe6;
            --panel: #fffaf2;
            --accent: #d56f3e;
            --accent-dark: #8f4421;
            --text: #2d241d;
            --muted: #74655a;
            --border: #e4d3bf;
            --done: #2d8a58;
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            min-height: 100vh;
            font-family: Georgia, "Times New Roman", serif;
            color: var(--text);
            background:
                radial-gradient(circle at top left, #f9d6b8 0, transparent 24%),
                radial-gradient(circle at bottom right, #f6c7b4 0, transparent 22%),
                var(--bg);
        }

        .wrap {
            max-width: 920px;
            margin: 0 auto;
            padding: 32px 20px 48px;
        }

        .hero {
            padding: 28px;
            border: 1px solid var(--border);
            border-radius: 24px;
            background: linear-gradient(135deg, rgba(255, 250, 242, 0.96), rgba(255, 239, 224, 0.9));
            box-shadow: 0 16px 50px rgba(110, 72, 43, 0.14);
        }

        h1 {
            margin: 0 0 8px;
            font-size: clamp(2rem, 4vw, 3.4rem);
            line-height: 1;
        }

        p {
            margin: 0;
            color: var(--muted);
        }

        form {
            margin-top: 24px;
        }

        .rows {
            display: grid;
            gap: 12px;
        }

        .timer-row {
            display: grid;
            grid-template-columns: 2fr 1fr auto;
            gap: 12px;
        }

        input {
            width: 100%;
            padding: 14px 16px;
            border: 1px solid var(--border);
            border-radius: 14px;
            background: #fff;
            color: var(--text);
            font-size: 1rem;
        }

        button {
            border: 0;
            border-radius: 14px;
            padding: 14px 18px;
            cursor: pointer;
            font-size: 1rem;
        }

        .primary {
            margin-top: 16px;
            background: var(--accent);
            color: #fffaf4;
        }

        .secondary {
            background: #f1e0cf;
            color: var(--accent-dark);
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 18px;
            margin-top: 24px;
        }

        .panel {
            padding: 20px;
            border: 1px solid var(--border);
            border-radius: 20px;
            background: var(--panel);
            box-shadow: 0 10px 30px rgba(110, 72, 43, 0.08);
        }

        .panel h2 {
            margin: 0 0 14px;
            font-size: 1.2rem;
        }

        .timer-card {
            padding: 14px 0;
            border-top: 1px solid var(--border);
        }

        .timer-card:first-of-type {
            border-top: 0;
            padding-top: 0;
        }

        .timer-name {
            font-weight: 700;
            margin-bottom: 4px;
        }

        .meta {
            color: var(--muted);
            font-size: 0.95rem;
        }

        .done {
            color: var(--done);
        }

        .empty {
            color: var(--muted);
            font-style: italic;
        }

        @media (max-width: 640px) {
            .timer-row {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="wrap">
        <section class="hero">
            <h1>Multiple Timer Manager</h1>
            <p>Create several timers at once and let them run in parallel.</p>

            <form method="post" action="{{ url_for('create_timers') }}">
                <div id="rows" class="rows">
                    <div class="timer-row">
                        <input name="name" type="text" placeholder="Timer name" value="Timer 1" required>
                        <input name="seconds" type="number" min="1" placeholder="Seconds" required>
                        <button type="button" class="secondary" onclick="addRow()">Add row</button>
                    </div>
                </div>
                <button type="submit" class="primary">Start Timers</button>
            </form>
        </section>

        <section class="grid">
            <div class="panel">
                <h2>Active Timers</h2>
                {% if active_timers %}
                    {% for timer in active_timers %}
                        <div class="timer-card">
                            <div class="timer-name">{{ timer['name'] }}</div>
                            <div class="meta">{{ timer['seconds'] }} seconds</div>
                            <div class="meta">Started at {{ timer['started_at'] }}</div>
                        </div>
                    {% endfor %}
                {% else %}
                    <div class="empty">No active timers.</div>
                {% endif %}
            </div>

            <div class="panel">
                <h2>Completed Timers</h2>
                {% if completed_timers %}
                    {% for timer in completed_timers %}
                        <div class="timer-card">
                            <div class="timer-name done">{{ timer['name'] }} finished</div>
                            <div class="meta">Ran for {{ timer['seconds'] }} seconds</div>
                            <div class="meta">Finished at {{ timer['finished_at'] }}</div>
                        </div>
                    {% endfor %}
                {% else %}
                    <div class="empty">No completed timers yet.</div>
                {% endif %}
            </div>
        </section>
    </div>

    <script>
        function addRow() {
            const rows = document.getElementById('rows');
            const index = rows.children.length + 1;
            const row = document.createElement('div');
            row.className = 'timer-row';
            row.innerHTML = `
                <input name="name" type="text" placeholder="Timer name" value="Timer ${index}" required>
                <input name="seconds" type="number" min="1" placeholder="Seconds" required>
                <button type="button" class="secondary" onclick="this.parentElement.remove()">Remove</button>
            `;
            rows.appendChild(row);
        }

        setInterval(() => {
            window.location.reload();
        }, 4000);
    </script>
</body>
</html>
"""


def now_text():
    return datetime.now().strftime("%I:%M:%S %p")


def run_timer(timer_id, seconds):
    time.sleep(seconds)
    with timers_lock:
        for timer in timers:
            if timer["id"] == timer_id:
                timer["status"] = "completed"
                timer["finished_at"] = now_text()
                break


@app.get("/")
def index():
    with timers_lock:
        active_timers = [timer.copy() for timer in timers if timer["status"] == "active"]
        completed_timers = [timer.copy() for timer in reversed(timers) if timer["status"] == "completed"]
    return render_template_string(
        PAGE,
        active_timers=active_timers,
        completed_timers=completed_timers,
    )


@app.post("/timers")
def create_timers():
    names = request.form.getlist("name")
    seconds_values = request.form.getlist("seconds")

    for name, seconds_text in zip(names, seconds_values):
        clean_name = name.strip() or "Unnamed timer"
        seconds = int(seconds_text)
        timer_id = str(uuid4())
        timer = {
            "id": timer_id,
            "name": clean_name,
            "seconds": seconds,
            "status": "active",
            "started_at": now_text(),
            "finished_at": None,
        }

        with timers_lock:
            timers.append(timer)

        thread = threading.Thread(target=run_timer, args=(timer_id, seconds), daemon=True)
        thread.start()

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)