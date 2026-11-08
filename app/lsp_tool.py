import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote, urlparse

from app.lsp import get_lsp_client, get_lsp_cursor, set_lsp_cursor
from app.lsp_client import LSPClient
from app.utils import read_file

_uri_to_version: dict[str, int] = defaultdict(int)
_last_shown_diagnostics: dict[str, set[tuple[int, int, str]]] = defaultdict(
    set
)  # file -> line, character, message


def path_to_uri(abs_path: str) -> str:
    return Path(abs_path).as_uri()


def uri_to_relpath(uri: str) -> str:
    abs_path = unquote(urlparse(uri).path)
    return os.path.relpath(abs_path)


def _open_file(client: LSPClient, uri: str, file_contet: str, language_id: str) -> None:
    client.notify(
        "textDocument/didOpen",
        {
            "textDocument": {
                "uri": uri,
                "languageId": language_id,
                "version": 1,
                "text": file_contet,
            }
        },
    )
    _uri_to_version[uri] = 1


def _update_file(client: LSPClient, uri: str, file_contet: str) -> None:
    client.notify(
        "textDocument/didChange",
        {
            "textDocument": {
                "uri": uri,
                "version": _uri_to_version[uri] + 1,
            },
            "contentChanges": [{"text": file_contet}],
        },
    )
    _uri_to_version[uri] += 1


def ensure_open_or_update(client: LSPClient, uri: str, abs_path: str) -> None:
    file_content = read_file(abs_path)
    ext = os.path.splitext(abs_path)[1]
    language_id = client.extension_to_language.get(ext, "")
    if not language_id:
        raise ValueError(f"no language server configured for {ext} files")

    if uri in _uri_to_version:
        _update_file(client, uri, file_content)
    else:
        _open_file(client, uri, file_content, language_id)


def _implement_go_to_definition(client: LSPClient, uri: str, args: dict) -> str:
    try:
        result = client.request(
            "textDocument/definition",
            {
                "textDocument": {"uri": uri},
                "position": {
                    "line": args["line"] - 1,  # 1-based -> 0-based
                    "character": args["character"] - 1,
                },
            },
        )
    except RuntimeError as e:
        return f"LSP error: {e}"

    if not result:
        return "No definition found"

    start = result["range"]["start"]
    path = uri_to_relpath(result["uri"])
    return f"Defined in {path}:{start['line'] + 1}:{start['character'] + 1}"


def _implement_find_references(client: LSPClient, uri: str, args: dict) -> str:
    try:
        result = client.request(
            "textDocument/references",
            {
                "textDocument": {"uri": uri},
                "position": {
                    "line": args["line"] - 1,  # 1-based -> 0-based
                    "character": args["character"] - 1,
                },
                "context": {"includeDeclaration": True},
            },
        )
    except RuntimeError as e:
        return f"LSP error: {e}"

    if not result:
        return "No references found"

    files_map = defaultdict(list)
    for res in result:
        path = uri_to_relpath(res["uri"])
        start = res["range"]["start"]
        files_map[path].append(f"Line {start['line'] + 1}:{start['character'] + 1}")

    references = f"Found {len(result)} references across {len(files_map)} files:\n\n"
    for file, lines in files_map.items():
        references += f"{file}:\n\n" + "\n".join(lines) + "\n\n"
    return references


def call_lsp_tool(args: str) -> str:
    client = get_lsp_client()
    if not client:
        return "Error: LSP is not configuresd"

    args = json.loads(args)

    if args.get("operation") not in ["goToDefinition", "findReferences"]:
        return f"Error: unsupported operation {args.get('operation')!r}"

    abs_path = os.path.abspath(args["filePath"])
    if not os.path.isfile(abs_path):
        return f"Error: file not found: {args['filePath']}"

    uri = path_to_uri(abs_path)

    if uri not in _uri_to_version:
        try:
            ensure_open_or_update(client, uri, abs_path)   # takes the didOpen path
        except ValueError as e:
            return f"Error: {e}"
        except RuntimeError as e:
            print(f"[lsp] open failed: {e}", file=sys.stderr)
            return f"LSP error: {e}"

    op = args.get("operation")
    if op == "goToDefinition":
        return _implement_go_to_definition(client, uri, args)
    elif op == "findReferences":
        return _implement_find_references(client, uri, args)


def fetch_lsp_diagnostics() -> str:
    client = get_lsp_client()
    if not client:
        return ""
    cursor = get_lsp_cursor()
    try:
        new_diag = client.notifications(cursor, 0)
    except RuntimeError:
        return ""  # treat a failed poll as "nothing new"
    set_lsp_cursor(new_diag.get("cursor", cursor))
    notifications = new_diag.get("notifications", [])

    # keep only the latest current report per file in this batch
    latest: dict[str, list] = {}

    for note in notifications:
        if note.get("method") != "textDocument/publishDiagnostics":
            continue
        params = note.get("params")
        if not isinstance(params, dict):
            continue
        uri = params.get("uri")
        if not uri:
            continue

        version = params.get("version")
        if version is not None and version != _uri_to_version.get(uri):
            continue  # stale report

        latest[uri] = params.get("diagnostics", [])

    report = []
    for uri, diagnostics in latest.items():
        curr_issues: set[tuple[int, int, str]] = set()
        for d in diagnostics:
            start = d["range"]["start"]
            curr_issues.add((start["line"] + 1, start["character"] + 1, d["message"]))
        new_issues = curr_issues - _last_shown_diagnostics.get(uri, set())
        _last_shown_diagnostics[uri] = curr_issues
        if new_issues:
            lines = [f"{uri_to_relpath(uri)}:"]
            for line, char, message in sorted(new_issues):
                lines.append(f"  [Line {line}:{char}] {message}")
            report.append("\n".join(lines))
    if not report:
        return ""

    body = "\n\n".join(report)
    return (
        "<new-diagnostics>The following new diagnostic issues were detected:\n\n"
        f"{body}</new-diagnostics>"
    )
