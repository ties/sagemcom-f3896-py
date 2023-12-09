from typing import List

from sagemcom_f3896_client.log_parser import ParsedMessage
from sagemcom_f3896_client.models import EventLogItem


def format_log_entries(logs: List[ParsedMessage]):
    for entry in logs:
        yield f"{' ' * 8}<tr><td>{entry.time.ctime()}</td><td>"
        if entry.priority == "error":
            yield f"<emph>{entry.priority}</emph>"
        else:
            yield entry.priority

        yield f"</td><td>{entry.message}</td></tr>"


def index_template(logs: List[EventLogItem]) -> str:
    return f"""<html>
            <head><title>Sagemcom F3896</title></head>
            <style>
                body {{
                    font-family: helvetica, arial, sans-serif;
                }}

                emph {{
                    font-weight: bold;
                }}

                table {{
                    font-size: 75%;
                }}

                thead td {{
                    font-weight: bold;
                    padding: 0.5em;
                }}

                td {{
                    padding: 0 0.5em;
                }}
            </style>
            <body>
                <h1>SagemCom F3896</h1>
                <p><a href="/metrics">Metrics</a></p>
                <p>
                <table>
                    <thead>
                    <tr><td>Time</td><td>Priority</td><td>Message</td></tr>
                    </thread>
                    <tbody>
                    {''.join(list(format_log_entries(logs)))}
                    </tbody>
                </table>
                </p>
                <p>
                    <small>F3896 exporter <a href="https://github.com/ties/sagemcom-f3896-py">github.com/ties/sagemcom-f3896-py</a></small>
                </p>
            </body>
        </html>"""
