import json
import os
import sys
from collections import defaultdict
from pathlib import Path
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


def _implement_go_to_definition(
    client: LSPClient, uri: str, args: dict
) -> str:
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


def _implement_find_references(
    client: LSPClient, uri: str,  args: dict
) -> str:
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
        return "No definition found"

    files_map = defaultdict(list)
    for res in result:
        path = uri_to_relpath(res["uri"])
        start = res["range"]["start"]
        files_map[path].append(f"Line {start['line'] + 1}:{start['character'] + 1}")

    references = f"Found {len(result)} references across {len(files_map)} files:\n\n"
    for file, lines in files_map.items():
        references += f"{file}:\n" + "\n".join(lines)
    print(references, file=sys.stderr)
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

    try:
        ensure_open(client, uri, abs_path)
    except RuntimeError as e:
        return f"LSP error: {e}"

    op = args.get("operation")
    if op == "goToDefinition":
        return _implement_go_to_definition(client, uri, args)
    elif op == "findReferences":
        return _implement_find_references(client, uri, args)
