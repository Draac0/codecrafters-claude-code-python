import os
from collections.abc import Iterable

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from app.tools import exec_bash_cmds, exec_skill_tool, read_file_tool, write_file_tool

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")
MODEL = os.getenv("LOCAL_MODEL", default="anthropic/claude-haiku-4.5")


def call_agent(
    messages: Iterable[ChatCompletionMessageParam],
):
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    while True:
        chat = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "Read",
                        "description": "Read and return the contents of a file",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "The path to the file to read",
                                }
                            },
                            "required": ["file_path"],
                        },
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "Write",
                        "description": "Write content to a file",
                        "parameters": {
                            "type": "object",
                            "required": ["file_path", "content"],
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "The path of the file to write to",
                                },
                                "content": {
                                    "type": "string",
                                    "description": "The content to write to the file",
                                },
                            },
                        },
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "Bash",
                        "description": "Execute a shell command",
                        "parameters": {
                            "type": "object",
                            "required": ["command"],
                            "properties": {
                                "command": {
                                    "type": "string",
                                    "description": "The command to execute",
                                }
                            },
                        },
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "Skill",
                        "description": "Load a skill's instructions into the conversation",
                        "parameters": {
                            "type": "object",
                            "required": ["name"],
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "The name of the skill to use",
                                },
                                "args": {
                                    "type": "string",
                                    "description": "Optional arguments for the skill",
                                },
                            },
                        },
                    },
                },
            ],
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
