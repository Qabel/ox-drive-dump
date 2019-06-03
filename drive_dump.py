import argparse
import shutil
from os import makedirs
from os import path

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
    files_itr = build_file_nodes(file_rows)
    for file in files_itr:
        folder_node = node_by_id[file.folder_id]
        file.parent = folder_node
    for node in node_by_id.values():
        if node.parent_id is not None:
            node.parent = node_by_id.get(node.parent_id)
    return root


def main():
    args = parse_args()
    db = connect(args.host, args.user, args.password, args.port, args.db)
    root = build_tree(list(query_folders(db)), query_files(db))
    paths = []
    for node in LevelOrderIter(root):
        if hasattr(node, 'location'):
            paths.append((path.join(*(n.fname for n in node.path[:-1])), node.fname, node.location))

    source_root = args.SOURCE
    target_root = args.TARGET
    for folder, filename, source in paths:
        target_folder = path.join(target_root, folder)
        target_file = path.join(target_folder, filename)
        source_path = path.join(source_root, source)
        makedirs(target_folder, exist_ok=True)
        shutil.copy(source_path, target_file)


if __name__ == '__main__':
    main()

