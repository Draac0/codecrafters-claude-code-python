import argparse
import os
import sys

from dotenv import load_dotenv

from app.agent import call_agent
from app.lsp import set_lsp_client
from app.lsp_client import LSPClient
from app.utils import expand_skill_command, stringify_skill_metadata

load_dotenv()


API_KEY = os.getenv("OPENROUTER_API_KEY")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    skills_metadata = stringify_skill_metadata()
    expanded_skills_array = expand_skill_command(args.p)
    messages = [
        {
            "role": "system",
            "content": f"You have access to the following skills:\n\n- {skills_metadata}\n\nIf a skill matches the user's request, call the Skill tool with its name and follow the instructions it returns.",
        },
        *[{"role": "user", "content": content} for content in expanded_skills_array],
    ]

    lsp_client = LSPClient.from_environment()
    set_lsp_client(lsp_client)
    if lsp_client is not None:
        print("LSP client connected", file=sys.stderr)

    response = call_agent(messages)
    print(response)


if __name__ == "__main__":
    main()
