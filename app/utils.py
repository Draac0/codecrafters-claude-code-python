import os
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

def parse_skill_metadata() -> list:
    skill_content = read_skill_content()
    metadata = []
    for skill in skill_content:
        parts = skill.split('---',2)
        if len(parts) >= 3:
            yaml_block = parts[1]
            m = yaml.safe_load(yaml_block)
            metadata.append(m)
    return metadata

def stringify_skill_metadata() -> str:
    metadata = parse_skill_metadata()
    result = ''
    for meta in metadata:
        result += f'- {meta['name']}: {meta['description']}\n'
    return result

# if __name__ == "__main__":
#     print(stringify_skill_metadata())

    