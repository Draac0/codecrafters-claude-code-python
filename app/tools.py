import json
import subprocess
import sys

from app.utils import (
    add_scripts_location,
    fill_args_in_skill,
    parse_skill_text,
    read_file,
)


def read_file_tool(args: str) -> str:
    args = json.loads(args)
    if "file_path" not in args:
        return "file_path arg missing in tool"
    else:
        file_path = args["file_path"]
    return read_file(file_path=file_path)


def write_file_tool(args: str) -> str:
    args = json.loads(args)
    file_path = args.get("file_path", "")
    content = args.get("content", "")

    if not file_path:
        return "file_path arg is empty."

    with open(file_path, "w", encoding="utf+8") as file:
        file.write(content)
    return "content is written to file_path"


def exec_bash_cmds(args: str) -> str:
    args = json.loads(args)
    command = args.get("command", "")
    print(command, file=sys.stderr)

    result = subprocess.run(
        command, check=False, shell=True, capture_output=True, text=True
    )

    return f"STDOUT: '{result.stdout}'\nSTDERR: '{result.stderr}'"


def exec_skill_tool(args: str) -> str:
    args = json.loads(args)
    name = args.get("name", "")
    skill_args = args.get("args", "")
    if not name:
        return "Skill name is required argument"

    _, markdown = parse_skill_text()
    if name not in markdown:
        return f"Skill with {name} doesn't exist in user skills folder"

    return add_scripts_location(name) + fill_args_in_skill(markdown[name], skill_args)
