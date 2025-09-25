# Jinja folder multiplier 

This script is helping multiplication of folder and files in it using Jinja2



# Environment setup

Pre-requests is python virtual environment is used 

https://formulae.brew.sh/formula/pyenv#default

https://formulae.brew.sh/formula/pyenv-virtualenv#default 

Install Specific versions of Python

```sh
pyenv install 3.12.2
```

```sh
pyenv virtualenv 3.12.2 jinja2_markdown_clone
```


# Install the needed pkgs

```sh
pip install -r requirements.txt
```


# Run the command 

Prior running the command tune the script with the right folders 

```sh
python main.py --source_dir /path/to/source_dir --base_output_dir /path/to/base_output_dir --pod_config example.yaml --mkdocs_config /path/to/mkdocs.yml
```

# Configuration File Format

The YAML configuration file should follow this structure:

```yaml
pods:
  - pod_name: '01'
    pod_ip: '1'
  - pod_name: '02'
    pod_ip: '2'
  # ... additional PODs
```

Each POD entry will create a directory named `POD{index}` (e.g., POD1, POD2, etc.) and process templates with the corresponding `pod_name` and `pod_ip` variables.

# What the Script Does

1. **Loads Configuration**: Reads POD details from YAML and navigation structure from mkdocs.yml
2. **Creates POD Directories**: For each POD, creates a new directory structure mirroring the source
3. **Processes Templates**: Renders Jinja2 templates in `.md` files with POD-specific variables
4. **Copies Files**: Copies non-template files directly to POD directories
5. **Updates Navigation**: Modifies the original mkdocs.yml to include navigation sections for each POD

