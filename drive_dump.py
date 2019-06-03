import argparse
import itertools

import mysql.connector
from anytree import Node


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

    return parser.parse_args()


def query(db, parent):
    cur = db.cursor()
    cur.execute('SELECT fuid, parent, fname FROM oxfolder_tree WHERE parent=%s', (parent,))
    yield from cur
    cur.close()


def build_tree(db):
    def find_children(parent):
        return [Node(id=id, name=fname, parent_id=parent_id)
                for id, parent_id, fname in query(db, parent)]

    def recur(node):
        node.children = find_children(node.id)
        for child in node.children:
            recur(child)

    root = Node(name='', id=0)
    recur(root)
    return root

def main():
    args = parse_args()
    db = connect(args.host, args.user, args.password, args.port, args.db)
    root = build_tree(db)
    print(root)


if __name__ == '__main__':
    main()

