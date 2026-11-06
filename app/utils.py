import os
import re
import yaml

def read_file(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            return content
    except FileNotFoundError:
        return "Error: file not found in the path: '{file_path}'"
    

def read_skill_content() -> list[str]:
    path_to_skills = os.path.join(os.curdir,'.claude','skills')
    if not os.path.isdir(path_to_skills):
        return []
    skill_content = []
    for name in os.listdir(path=path_to_skills):
        full_path = os.path.join(path_to_skills, name)
        if os.path.isdir(full_path):
            content = read_file(os.path.join(full_path, 'SKILL.md'))
            skill_content.append(content)
            
    return skill_content

def parse_skill_metadata() -> tuple[list, list]:
    skill_content = read_skill_content()
    metadata = []
    markdown = []
    for skill in skill_content:
        parts = skill.split('---',2)
        if len(parts) >= 3:
            yaml_block = parts[1]
            m = yaml.safe_load(yaml_block)
            name = m["name"]
            metadata.append(m)
            markdown.append({name: parts[2]})
    return metadata, markdown

def stringify_skill_metadata() -> str:
    metadata, _ = parse_skill_metadata()
    result = ''
    for meta in metadata:
        result += f'- {meta['name']}: {meta['description']}\n'
    return result

def fill_args_in_skill(skill: str, args: str) -> str:
    split_args = args.strip().split(' ')
    def replace(match):
        index = int(match.group(1) or match.group(2))
        return split_args[index] if index < len(split_args) else ""
    skill = re.sub(r"\$(?:ARGUMENTS\[(\d+)\]|(\d+))", replace, skill)
    skill = re.sub(r"\$ARGUMENTS", lambda _: args.strip(), skill)
    return skill
    

def expand_skill_command(text: str) -> str:
    with_slash = r'^/(\S+)'
    match = re.match(with_slash, text)
    if not match:
        return text
    args = text[match.end():]
    skill = match.group(1)
    _, markdown = parse_skill_metadata()
    for m in markdown:
        if skill in m:
            return fill_args_in_skill(m[skill], args)
    return text

    

if __name__ == "__main__":
    print(expand_skill_command("/apple staging eu-west"))

    