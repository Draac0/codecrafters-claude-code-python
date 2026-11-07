import os
import re
import yaml

def read_file(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            return content
    except IsADirectoryError:
        return f"Error: {file_path} is a directory, not a file"
    except FileNotFoundError:
        return f"Error: {file_path} does not exist"
    except OSError as e:
        return f"Error reading {file_path}: {e}"
    

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

def parse_skill_text() -> tuple[list, dict]:
    skill_content = read_skill_content()
    metadata = []
    markdown = {}
    for skill in skill_content:
        parts = skill.split('---',2)
        if len(parts) >= 3:
            yaml_block = parts[1]
            m = yaml.safe_load(yaml_block)
            name = m["name"]
            metadata.append(m)
            markdown[name] = parts[2]
    return metadata, markdown

def stringify_skill_metadata() -> str:
    metadata, _ = parse_skill_text()
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

def add_scripts_location(skill_name: str) -> str:
    return f'Skill: {skill_name} (located at .claude/skills/{skill_name})\nPaths in the instructions below are relative to that folder.\n\n'    

def expand_skill_command(text: str) -> list[str]:
    with_slash = r'^(?:/\S+\s*)+'
    match = re.match(with_slash, text)
    if not match:
        return [text]
    args = text[match.end():]
    skills = re.findall(r'/(\S+)', match.group())
    _, markdown = parse_skill_text()
    missing_skills = []
    found_skills = []
    for skill in skills:
        if skill not in markdown:
            missing_skills.append('/'+skill)
        else:
            found_skills.append(skill)
    args = " ".join(missing_skills) + " " + args.strip()
    if not found_skills:
        return [text]
    result: list[str] = []
    for skill in found_skills:
        result.append(add_scripts_location(skill)+fill_args_in_skill(markdown[skill], args))
    return result

    

if __name__ == "__main__":
    print(expand_skill_command("/apple 4127 /grape"))