# Ox Drive Dump

Copies or hard links all files from an Open-Xchange Drive to a target destination.
Only the newest version of a versioned document is copied/linked, older versions are ignored.

The program scrapes the database and builds the file tree, then copies the files
from the `hashed` directory of ox drive to the target directory into the correct
folder structure. You can either copy the files or create hard links.
The default is a "fake action" which only prints the files that would be copied or linked.

Duplicate files are renamed to `*.dup` and this may lead to filenames like
`./infostore/Deleted files/.DS_Store.dup.dup.dup.dup`.


## Requirements

* Python 3.7 (3.6 probably works, too)
* virtualenv
* MySQL 8+

## Install

* `virtualenv --python=python3 venv --system-site-packages`
* `venv/bin/pip install -r requirements.txt`

## Usage

* Find out the storage folder of ox where the `hashed` folder lives
* `venv/bin/python drive_dump.py --host myhost --user username --password pass --action hard_link ox_storage_folder target_folder`