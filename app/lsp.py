client = None


def set_lsp_client(c):
    global client
    client = c


def get_lsp_client():
    return client
