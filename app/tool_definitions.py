LSH_tool_def = {
    "type": "function",
    "function": {
        "name": "LSP",
        "description": "Returns the file, line, and character where a symbol is defined.",
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["goToDefinition"]},
                "filePath": {
                    "type": "string",
                    "description": "Absolute path, or a path relative to the agent's current working directory.",
                },
                "line": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "1-based line number of the symbol.",
                },
                "character": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "1-based character offset in UTF-16 code units (same as character count for ASCII).",
                },
            },
            "required": ["operation", "filePath", "line", "character"],
        },
    },
}

read_tool_def = {
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
}
write_tool_def = {
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
}
bash_tool_def = {
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
}
skill_tool_def = {
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
}
