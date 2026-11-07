import argparse
import os

from dotenv import load_dotenv
from openai import OpenAI

from app.tools import exec_bash_cmds, exec_skill_tool, read_file_tool, write_file_tool
from app.utils import expand_skill_command, stringify_skill_metadata

load_dotenv()


API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")
MODEL = os.getenv("LOCAL_MODEL", default="anthropic/claude-haiku-4.5")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    skills_metadata = stringify_skill_metadata()
    expanded_skills_array = expand_skill_command(args.p)
    messages = [
        {
            "role": "system",
            "content": f"You have access to the following skills:\n\n- {skills_metadata}\n\nIf a skill matches the user's request, call the Skill tool with its name and follow the instructions it returns.",
        },
        *[{"role": "user", "content": content} for content in expanded_skills_array],
    ]

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
                print("Tool call not specified")
                break
        else:
            print(chat.choices[0].message.content)
            break

    # if not chat.choices or len(chat.choices) == 0:
    #     raise RuntimeError("no choices in response")

    # # You can use print statements as follows for debugging, they'll be visible when running tests.
    # print("Logs from your program will appear here!", file=sys.stderr)


if __name__ == "__main__":
    main()
