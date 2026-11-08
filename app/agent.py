import os
from collections.abc import Iterable

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCallUnion,
)

from app.lsp import get_lsp_client
from app.lsp_tool import call_lsp_tool, fetch_lsp_diagnostics
from app.tool_calls import (
    exec_bash_cmds,
    exec_skill_tool,
    read_file_tool,
    write_file_tool,
)
from app.tool_definitions import (
    LSP_tool_def,
    bash_tool_def,
    read_tool_def,
    skill_tool_def,
    write_tool_def,
)

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")
MODEL = os.getenv("LOCAL_MODEL", default="anthropic/claude-haiku-4.5")


def make_tool_call(
    tool: ChatCompletionMessageToolCallUnion, lsp_diagnostics: str
) -> str:
    args = tool.function.arguments
    if tool.type == "function" and tool.function.name == "Read":
        tool_content = read_file_tool(args)

    elif tool.type == "function" and tool.function.name == "Write":
        tool_content = write_file_tool(args)
    elif tool.type == "function" and tool.function.name == "Bash":
        tool_content = exec_bash_cmds(args)
    elif tool.type == "function" and tool.function.name == "Skill":
        tool_content = exec_skill_tool(args)
    elif tool.type == "function" and tool.function.name == "LSP":
        tool_content = call_lsp_tool(args)
    else:
        tool_content = (f"Tool with {tool.id} is not present in defined tools list",)
    return tool_content + lsp_diagnostics


def call_agent(
    messages: Iterable[ChatCompletionMessageParam],
):
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    tool_defs = [read_tool_def, write_tool_def, bash_tool_def, skill_tool_def]

    if get_lsp_client():
        tool_defs.append(LSP_tool_def)

    while True:
        lsp_diagnostics = fetch_lsp_diagnostics()
        chat = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tool_defs,
            tool_choice="auto",
        )

        message = chat.choices[0].message
        messages.append(message)
        if message.tool_calls:
            tool = message.tool_calls[0]
            tool_content = make_tool_call(tool, lsp_diagnostics)
            messages.append(
                {"role": "tool", "tool_call_id": tool.id, "content": tool_content}
            )
        else:
            return chat.choices[0].message.content
