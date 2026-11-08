from app.lsp_client import LSPClient

_client: LSPClient | None = None
_cursor: int = 0


def set_lsp_client(c: LSPClient | None):
    global _client
    _client = c


def get_lsp_client() -> LSPClient | None:
    return _client


def set_lsp_cursor(c: int) -> None:
    global _cursor
    _cursor = c

def get_lsp_cursor() -> int:
    return _cursor