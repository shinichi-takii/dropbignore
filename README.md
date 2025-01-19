# dropbignore

[EN] Set to ignore Dropbox folders<br>
[JP] Dropbox フォルダの同期を「無視」に設定するユーティリティ

- [dropbignore](#dropbignore)
  - [Features](#features)
  - [Reference](#reference)
  - [Supported object type](#supported-object-type)
  - [Requirement](#requirement)
  - [Installation](#installation)
  - [Usage](#usage)
    - [Create an ignore file](#create-an-ignore-file)
    - [Run this utility](#run-this-utility)
  - [License](#license)

-----

## Features

- [EN] Set the Dropbox folder to ignore with the pattern set in the `.dropbignore` file.
- [JP] `.dropbignore` ファイルで設定したパターンで、Dropbox フォルダを「無視」に設定します。


## Reference

- [EN] [How to set a Dropbox file or folder to be ignored | Dropbox Help](https://help.dropbox.com/files-folders/restore-delete/ignored-files)
- [JP] [Dropbox ファイルやフォルダを「無視」に設定する | Dropbox ヘルプ](https://help.dropbox.com/ja-jp/files-folders/restore-delete/ignored-files)


## Supported object type

- [EN] Folder only (File is not support)
- [JP] フォルダのみ (ファイルはサポートしていません)


## Requirement

1. macOS
2. Python >= 3.12
3. [uv package manager](https://github.com/astral-sh/uv)


## Installation

```bash
$ git clone https://github.com/shinichi-takii/dropbignore.git

$ cd dropbignore

$ pip install -r requirements.txt
```


## Usage

### Create an ignore file

- File path: `$HOME/Dropbox/.dropbignore`

```bash
# Example
$ echo '# Python
__pycache__/
.pytest_cache/

# Node.js
node_modules/
' > "$HOME/Dropbox/.dropbignore"
```


### Run this utility

```bash
$ cd dropbignore

$ python dropbignore.py
```


## License

[MIT License](https://github.com/shinichi-takii/dropbignore/blob/main/LICENSE)
