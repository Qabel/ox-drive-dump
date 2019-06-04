#!/usr/bin/env python3.7
import argparse
import os
import os.path
import shutil

import click
import mysql.connector
from anytree import Node, LevelOrderIter


def connect(host, user, password, port, database):
    return mysql.connector.connect(
        host=host, user=user, password=password, port=port, database=database)


def parse_args():
    parser = argparse.ArgumentParser(description='Dump the ox drive')
    parser.add_argument('--host', dest='host', default='localhost')
    parser.add_argument('--user', dest='user')
    parser.add_argument('--password', dest='password')
    parser.add_argument('--port', dest='port', default='3306')
    parser.add_argument('--db', dest='db')
    parser.add_argument('--action', choices=['fake', 'hardlink', 'copy'], default='fake')
    parser.add_argument('SOURCE', help='Source folder that contains the "hashed" folder')
    parser.add_argument('TARGET', help='Target folder to copy the files to')

    return parser.parse_args()


def query_folders(db):
    cur = db.cursor()
    cur.execute('SELECT fuid, parent, fname FROM oxfolder_tree ORDER BY parent')
    yield from cur
    cur.close()


def query_files(db):
    cur = db.cursor()
    cur.execute("""
SELECT t.filename,
       t.file_store_location,
       folder_id
 FROM (
                  SELECT d.filename,
                         d.file_store_location,
                         d.version_number,
                         d.infostore_id,
                         ROW_NUMBER() over (
                             PARTITION BY infostore_id ORDER BY version_number
                             ) AS row_num
                  FROM infostore_document AS d
                  WHERE d.file_store_location IS NOT NULL
              ) AS t
JOIN infostore ON t.infostore_id = infostore.id
WHERE t.row_num = 1

    """)
    yield from cur
    cur.close()


def build_file_nodes(rows):
    return (Node(name=filename,
                 fname=filename,
                 location=file_store_location,
                 folder_id=folder_id)
            for filename, file_store_location, folder_id in rows)


def build_nodes(rows):
    return (Node(id=id, name=fname, fname=fname, parent_id=parent_id)
            for id, parent_id, fname in rows)


def build_tree(folder_rows, file_rows):
    root = Node(name='', fname='', id=0, parent_id=-1)
    node_by_id = {node.id: node for node in build_nodes(folder_rows)}
    node_by_id[0] = root
    with click.progressbar(build_file_nodes(file_rows), label='Connecting files') as itr:
        for file in itr:
            folder_node = node_by_id[file.folder_id]
            file.parent = folder_node
    for node in node_by_id.values():
        if node.parent_id is not None:
            node.parent = node_by_id.get(node.parent_id)
    return root


def fake_operation(source, target, _):
    print(source, '->', target)


def copy_operation(source, target, target_folder):
    os.makedirs(target_folder, exist_ok=True)
    shutil.copy(source, target)


def hardlink_operation(source, target, target_folder):
    os.makedirs(target_folder, exist_ok=True)
    os.link(source, target)


def main():
    args = parse_args()
    db = connect(args.host, args.user, args.password, args.port, args.db)
    root = build_tree(list(query_folders(db)), query_files(db))
    paths = []
    for node in LevelOrderIter(root):
        if hasattr(node, 'location'):
            paths.append((os.path.join(*(n.fname for n in node.path[:-1])), node.fname, node.location))

    source_root = args.SOURCE
    target_root = args.TARGET
    operation = {
        'fake': fake_operation,
        'copy': copy_operation,
        'hardlink': hardlink_operation
    }[args.action]
    label = {
        'fake': 'Faking file copy',
        'copy': 'Copying files',
        'hardlink': 'Hard linking files'
    }[args.action]
    with click.progressbar(paths, label=label) as path_itr:
        for folder, filename, source in path_itr:
            target_folder = os.path.join(target_root, folder)
            target_file = os.path.join(target_folder, filename)
            source_path = os.path.join(source_root, source)
            operation(source_path, target_file, target_folder)


if __name__ == '__main__':
    main()

