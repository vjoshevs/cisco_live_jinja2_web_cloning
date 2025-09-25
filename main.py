import os
import yaml
from jinja2 import Environment, FileSystemLoader
import shutil
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description='Process Jinja templates and copy files for POD directories.')
    parser.add_argument('--source_dir', required=True, help='Original directory with Jinja templates')
    parser.add_argument('--base_output_dir', required=True, help='Directory where modified copies will be saved')
    parser.add_argument('--pod_config', required=True, help='YAML file with POD details')
    parser.add_argument('--mkdocs_config', required=True, help='Original mkdocs.yml file to read navigation structure from')
    return parser.parse_args()

def initialize_environment(source_dir):
    return Environment(loader=FileSystemLoader(source_dir))

def load_pod_details(yaml_file):
    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)
    return data['pods']

def load_mkdocs_config(mkdocs_file):
    """Load the navigation section from mkdocs.yml configuration"""
    with open(mkdocs_file, 'r') as file:
        content = file.read()
        
        # Extract nav section manually to avoid YAML parsing issues with custom tags
        lines = content.split('\n')
        nav_lines = []
        in_nav = False
        nav_indent = 0
        
        for line in lines:
            if line.strip().startswith('nav:'):
                in_nav = True
                nav_indent = len(line) - len(line.lstrip())
                nav_lines.append(line)
            elif in_nav:
                current_indent = len(line) - len(line.lstrip()) if line.strip() else 0
                if line.strip() and current_indent <= nav_indent:
                    # We've reached the end of the nav section
                    break
                nav_lines.append(line)
        
        # Parse just the nav section
        nav_yaml = '\n'.join(nav_lines)
        try:
            nav_data = yaml.safe_load(nav_yaml)
            return {'nav': nav_data['nav']} if nav_data and 'nav' in nav_data else {'nav': []}
        except Exception as e:
            print(f"Warning: Could not parse navigation from mkdocs.yml: {e}")
            return {'nav': []}

def extract_lab_navigation(nav_structure):
    """Extract the Lab navigation section from the original mkdocs config"""
    for item in nav_structure:
        if isinstance(item, dict) and 'Lab' in item:
            return item['Lab']
    return None

def create_pod_navigation(lab_nav, pod_number):
    """Create navigation structure for a specific POD by prefixing file paths"""
    if not lab_nav:
        return None
    
    def prefix_paths(nav_item, pod_prefix):
        if isinstance(nav_item, dict):
            result = {}
            for key, value in nav_item.items():
                if isinstance(value, str) and value.endswith('.md'):
                    # This is a file path, prefix it with POD directory
                    result[key] = f"{pod_prefix}/{value}"
                elif isinstance(value, list):
                    # This is a list of navigation items
                    result[key] = [prefix_paths(item, pod_prefix) for item in value]
                elif isinstance(value, dict):
                    # This is a nested navigation structure
                    result[key] = prefix_paths(value, pod_prefix)
                else:
                    result[key] = value
            return result
        elif isinstance(nav_item, list):
            return [prefix_paths(item, pod_prefix) for item in nav_item]
        else:
            return nav_item
    
    pod_prefix = f"POD{pod_number}"
    return prefix_paths(lab_nav, pod_prefix)

def generate_mkdocs_nav(pod_details, mkdocs_config, base_output_dir, original_mkdocs_file):
    """Generate mkdocs.yml with per-POD navigation structure as separate top-level sections within nav"""
    
    # Extract the original Lab navigation structure
    original_nav = mkdocs_config.get('nav', [])
    lab_nav_structure = extract_lab_navigation(original_nav)
    
    if not lab_nav_structure:
        print("Warning: Could not find 'Lab' section in navigation. Using empty structure.")
        lab_nav_structure = []
    
    # Build new navigation preserving original structure completely
    new_nav = []
    
    # First, keep all original navigation sections intact (Home, Lab, etc.)
    for item in original_nav:
        new_nav.append(item)
    
    # Then add POD sections as separate top-level items within nav
    for i, pod_detail in enumerate(pod_details, start=1):
        pod_name = pod_detail['pod_name']
        pod_nav = create_pod_navigation(lab_nav_structure, i)
        
        if pod_nav:
            pod_section = {f"POD{pod_name}": pod_nav}
            new_nav.append(pod_section)
    
    # Read original mkdocs.yml content and replace nav section
    with open(original_mkdocs_file, 'r') as f:
        original_content = f.read()

    # Find and replace the nav section
    lines = original_content.split('\n')
    new_lines = []
    in_nav = False
    nav_indent = 0

    def format_nav_item(item, indent_level=1):
        """Format navigation items with proper indentation"""
        indent = '  ' * indent_level
        formatted_lines = []
        
        if isinstance(item, dict):
            for key, value in item.items():
                if isinstance(value, str):
                    # Simple key-value pair (e.g., "Introduction: Introduction.md")
                    formatted_lines.append(f"{indent}- {key}: {value}")
                elif isinstance(value, list):
                    # Key with list of sub-items
                    formatted_lines.append(f"{indent}- {key}:")
                    for sub_item in value:
                        formatted_lines.extend(format_nav_item(sub_item, indent_level + 1))
                elif isinstance(value, dict):
                    # Key with nested dictionary
                    formatted_lines.append(f"{indent}- {key}:")
                    formatted_lines.extend(format_nav_item(value, indent_level + 1))
        elif isinstance(item, list):
            for list_item in item:
                formatted_lines.extend(format_nav_item(list_item, indent_level))
        
        return formatted_lines

    for line in lines:
        if line.strip().startswith('nav:'):
            in_nav = True
            nav_indent = len(line) - len(line.lstrip())
            # Add the new navigation with proper formatting
            new_lines.append('nav:')
            for nav_item in new_nav:
                new_lines.extend(format_nav_item(nav_item, 1))
        elif in_nav:
            current_indent = len(line) - len(line.lstrip()) if line.strip() else 0
            if line.strip() and current_indent <= nav_indent:
                # We've reached the end of the nav section
                in_nav = False
                new_lines.append(line)
            # Skip original nav content
        else:
            new_lines.append(line)    # Write back to the original mkdocs.yml file
    with open(original_mkdocs_file, 'w') as f:
        f.write('\n'.join(new_lines))
    
    print(f"Updated original mkdocs.yml with {len(pod_details)} POD sections at: {original_mkdocs_file}")
    print(f"Original Lab navigation structure preserved and replicated for each POD")

def process_and_copy_files(env, src_dir, dest_dir, pod_name, pod_ip):
    try:
        if os.path.exists(dest_dir):
            print(f"Removing existing directory: {dest_dir}")
            shutil.rmtree(dest_dir)
        os.makedirs(dest_dir, exist_ok=True)
        print(f"Created directory: {dest_dir}")

        for root, dirs, files in os.walk(src_dir):
            dirs[:] = [d for d in dirs if not d.startswith('POD') or not d[3:].isdigit()]
            # Ignore other folders in this case img folder
            dirs[:] = [d for d in dirs if d != 'img']

            rel_root = os.path.relpath(root, src_dir)
            dest_root = os.path.join(dest_dir, rel_root)

            os.makedirs(dest_root, exist_ok=True)

            for file_name in files:
                src_file_path = os.path.join(root, file_name)
                dest_file_path = os.path.join(dest_root, file_name)

                if file_name.endswith('.md'):
                    template = env.get_template(os.path.relpath(src_file_path, src_dir))
                    rendered_content = template.render(pod_name=pod_name, pod_ip=pod_ip)

                    with open(dest_file_path, 'w') as output_file:
                        output_file.write(rendered_content)
                    print(f"Processed and saved file: {dest_file_path}")
                else:
                    shutil.copy2(src_file_path, dest_file_path)
                    print(f"Copied file: {dest_file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    args = parse_arguments()
    source_dir = args.source_dir
    base_output_dir = args.base_output_dir
    pod_config = args.pod_config
    mkdocs_config_path = args.mkdocs_config

    # Load configurations
    pod_details = load_pod_details(pod_config)
    mkdocs_config = load_mkdocs_config(mkdocs_config_path)
    env = initialize_environment(source_dir)

    # Process POD directories
    for i, pod_detail in enumerate(pod_details, start=1):
        pod_dir = os.path.join(base_output_dir, f'POD{i}')
        process_and_copy_files(env, source_dir, pod_dir, pod_detail['pod_name'], pod_detail['pod_ip'])

    # Generate mkdocs.yml with per-POD navigation
    generate_mkdocs_nav(pod_details, mkdocs_config, base_output_dir, mkdocs_config_path)

    print("All POD directories and mkdocs.yml created successfully!")

if __name__ == '__main__':
    main()
