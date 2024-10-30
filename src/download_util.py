import os
import stat

import requests

# class DownloadUtil:
def download_file(url: str, local_filename: str):
    # STEP - make sure target path exists
    local_path = os.path.dirname(local_filename)
    if not os.path.exists(local_path):
        os.makedirs(local_path)
    if os.path.exists(local_filename):
        return False
    # STEP - Download the file
    tmp = local_filename + ".tmp"
    with requests.get(url, stream=True) as resp:
        resp.raise_for_status()  # This will raise an error for unsuccessful requests
        with open(tmp, 'wb') as file:
            for data in resp.iter_content(chunk_size=1024):
                file.write(data)
    os.rename(tmp, local_filename)
    # if local_filename.endswith(".rpm"):
    #     chmod_plus_exec(local_filename) # maybe future do this in the Dockerfile
    return True

def chmod_plus_exec(filename):
    permissions = os.stat(filename)
    os.chmod(filename, permissions.st_mode | stat.S_IEXEC)

def write_template(src: str, dest: str, chmod: bool = False, replace=None):
    if replace is None:
        replace = {}
    with open(src, 'r') as file:
        content = file.read()
    for k,v in replace.items():
        content = content.replace(k, v)
    with open(dest, "w", newline="\n") as f: # make sure we use Linux-style line endings, even on windows
        f.writelines(content)
    if chmod:
        chmod_plus_exec(dest)

def download_json(url: str):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()
