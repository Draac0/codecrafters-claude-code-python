import os
from collections.abc import Iterable

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from app.lsp import get_lsp_client
from app.tool_calls import (
    exec_bash_cmds,
    exec_skill_tool,
    read_file_tool,
    write_file_tool,
)
from app.tool_definitions import (
    LSH_tool_def,
    bash_tool_def,
    read_tool_def,
    skill_tool_def,
    write_tool_def,
)

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")
MODEL = os.getenv("LOCAL_MODEL", default="anthropic/claude-haiku-4.5")


def call_agent(
    messages: Iterable[ChatCompletionMessageParam],
):
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    tool_defs = [read_tool_def, write_tool_def, bash_tool_def, skill_tool_def]

    if get_lsp_client():
        tool_defs.append(LSH_tool_def)

    while True:
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
            if tool.type == "function" and tool.function.name == "Read":
                args = tool.function.arguments
                tool_content = read_file_tool(args)
                messages.append(
                    {"role": "tool", "tool_call_id": tool.id, "content": tool_content}
                )
            elif tool.type == "function" and tool.function.name == "Write":
                args = tool.function.arguments
                tool_content = write_file_tool(args)
                messages.append(
                    {"role": "tool", "tool_call_id": tool.id, "content": tool_content}
                )
            elif tool.type == "function" and tool.function.name == "Bash":
                args = tool.function.arguments
                tool_content = exec_bash_cmds(args)
                messages.append(
                    {"role": "tool", "tool_call_id": tool.id, "content": tool_content}
                )
            elif tool.type == "function" and tool.function.name == "Skill":
                args = tool.function.arguments
                tool_content = exec_skill_tool(args)
                messages.append(
                    {"role": "tool", "tool_call_id": tool.id, "content": tool_content}
                )
            elif tool.type == "function" and tool.function.name == "LSH":
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool.id,
                        "content": "LSP is not implemented yet",
                    }
                )
            else:
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool.id,
                        "content": f"Tool with {tool.id} is not present in defined tools list",
                    }
                )
        else:
            return chat.choices[0].message.content
