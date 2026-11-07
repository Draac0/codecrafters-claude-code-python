import json
import os
from pathlib import Path
import sys
from urllib.parse import unquote, urlparse

from app.lsp import get_lsp_client
from app.lsp_client import LSPClient
from app.utils import read_file

_opened_uris: set(str) = set()


def path_to_uri(abs_path: str) -> str:
    return Path(abs_path).as_uri()


def uri_to_relpath(uri: str) -> str:
    abs_path = unquote(urlparse(uri).path)
    return os.path.relpath(abs_path)


def ensure_open(client: LSPClient, uri: str, abs_path: str) -> None:
    if uri in _opened_uris:
        return

    text = read_file(abs_path)
    ext = os.path.splitext(abs_path)[1]
    language_id = client.extension_to_language.get(ext, "plaintext")

    client.notify(
        "textDocument/didOpen",
        {
            "textDocument": {
                "uri": uri,
                "languageId": language_id,
                "version": 1,
                "text": text,
            }
        },
    )

    _opened_uris.add(uri)


def call_lsp_tool(args: str) -> str:
    client = get_lsp_client()
    if not client:
        return "Error: LSP is not configuresd"

    args = json.loads(args)

    if args.get("operation") != "goToDefinition":
        return f"Error: unsupported operation {args.get('operation')!r}"

    abs_path = os.path.abspath(args["filePath"])
    if not os.path.isfile(abs_path):
        return f"Error: file not found: {args['filePath']}"

    uri = path_to_uri(abs_path)

    try:
        ensure_open(client, uri, abs_path)
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

    print(f"[lsp] definition response: {result}", file=sys.stderr)  # debug, remove later
    # in case the bridge wraps the answer as {"result": ...}
    if isinstance(result, dict) and "result" in result:
        result = result["result"]

    # servers may return a single location or a list of them
    if isinstance(result, list):
        result = result[0] if result else None
    if not result:
        return "No definition found"

    start = result["range"]["start"]
    path = uri_to_relpath(result["uri"])
    return f"Defined in {path}:{start['line'] + 1}:{start['character'] + 1}"  # back to 1-based
