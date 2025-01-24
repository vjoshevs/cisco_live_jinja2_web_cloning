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
    return parser.parse_args()

def initialize_environment(source_dir):
    return Environment(loader=FileSystemLoader(source_dir))

def load_pod_details(yaml_file):
    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)
    return data['pods']

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

    pod_details = load_pod_details(pod_config)
    env = initialize_environment(source_dir)

    for i, pod_detail in enumerate(pod_details, start=1):
        pod_dir = os.path.join(base_output_dir, f'POD{i}')
        process_and_copy_files(env, source_dir, pod_dir, pod_detail['pod_name'], pod_detail['pod_ip'])

    print("All POD directories created successfully!")

if __name__ == '__main__':
    main()
