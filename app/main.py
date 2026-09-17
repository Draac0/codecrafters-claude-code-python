import argparse
import os
import sys
from dotenv import load_dotenv
import json

load_dotenv()

from openai import OpenAI

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")
MODEL = os.getenv("LOCAL_MODEL",default="anthropic/claude-haiku-4.5")


def read_file_tool(args: str) -> str:
    args = json.loads(args)
    if "file_path" not in args:
        return "file_path arg missing in tool"
    else:
        file_path = args["file_path"]
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            return content
    except FileNotFoundError:
        return "Error: file not found in the path: '{file_path}'"

def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    
    messages = [{"role": "user", "content": args.p}]

    while True:
        chat = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=[{
            "type": "function",
            "function": {
                "name": "Read",
                "description": "Read and return the contents of a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "The path to the file to read"
                        }
                    },
                    "required": ["file_path"]
                }
            }
            }],
            tool_choice="auto"
        )
        
        message = chat.choices[0].message
        messages.append(message)
        if message.tool_calls:
            tool = message.tool_calls[0]
            if tool.type == "function" and tool.function.name == "Read":
                args = tool.function.arguments
                tool_content = read_file_tool(args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool.id,
                    "content": tool_content
                })
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
