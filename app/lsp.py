from app.lsp_client import LSPClient

client: LSPClient | None = None


def set_lsp_client(c: LSPClient | None):
    global client
    client = c


def get_lsp_client() -> LSPClient | None:
    return client
