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
python main.py --source_dir /path/to/source_dir --base_output_dir /path/to/base_output_dir --pod_config example.yaml
```

