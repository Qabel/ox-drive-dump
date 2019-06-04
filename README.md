# Ox Drive Dump

Copies or hard links all files from an Open XChange Drive to a target destination.
Only the newest version of a versioned document is copied/linked, older versions are ignored.

The program scrapes the database and builds the file tree, then copies the files
from the `hashed` directory of ox drive to the target directory into the correct
folder structure.

Duplicate files are renamed to `*.dup` and this may lead to filenames like
`./infostore/Deleted files/.DS_Store.dup.dup.dup.dup`.


## Requirements

* Python 3.7 (3.6 probably works, too)
* MySQL 8+

## Install

* `virtualenv --python=python3 venv --system-site-packages`
* `venv/bin/pip install -r requirements.txt`