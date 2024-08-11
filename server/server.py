import socket
import threading
import logging
import os
import concurrent.futures
from time import sleep

from db import Database
from utils import encrypt_file, parse_request, numerize_list
from constants import PORT, SERVER, ADDR, FORMAT, MAX_CONCURRENT_TRANSFERS, CHUNK_SIZE

import zipfile


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

database = Database()
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

online = {}

executor = concurrent.futures.ThreadPoolExecutor(MAX_CONCURRENT_TRANSFERS)


def apply_pending_files(conn, user):
    try:
        logging.info(f"[CHECKING PENDING FILES FOR {user['email']}]")
        pending_files = database.get_pending_filenames(user['email'])
        for filename in pending_files:
            sleep(0.5)
            send_file_to_client(conn, filename, user)
    except:
        return


def remove_connection(email):
    if email in online.keys():
        del online[email]
        return True



def send_file_to_client(conn, filename, user):
    try:
        logging.info(f"[SENDING {filename} TO {user['email']}]")
        file_size = os.path.getsize(filename)
        # sleep(0.5)
        conn.send(f"file {filename} -size {str(file_size)}".encode(FORMAT))
        with open(filename, 'rb') as file:
            while True:
                chunk = file.read(CHUNK_SIZE)
                if not chunk:
                    conn.sendall(b'<END>')
                    break
                encrypted_chunk = encrypt_file(chunk, user['key'])
                conn.sendall(encrypted_chunk)
    except:
        logging.error(f"[ERROR SENDING {filename} to {user['email']}]")
        return



def handle_admin_request(request, conn, sender):
    if request['request_type'] == 'create-group':
        group_name = request['param']
        verdict = database.insert_group(group_name)
        if verdict:
            conn.send(f"Group {group_name} created successfully!".encode(FORMAT))
        else:
            conn.send(f"Group {group_name} creation failed!".encode(FORMAT))
        return

    if request['request_type'] == 'delete-group':
        group_name = request['param']
        verdict = database.delete_group(group_name)
        if verdict:
            conn.send(f"Group {group_name} deleted successfully!".encode(FORMAT))
        else:
            conn.send(f"Group {group_name} deletion failed!".encode(FORMAT))
        return

    if request['request_type'] == 'list-users':
        users = database.get_users_list()
        conn.send(numerize_list(users).encode(FORMAT))
        return

    if request['request_type'] == 'view-requests':
        join_requests = database.get_join_requests()
        conn.send(numerize_list(join_requests).encode(FORMAT))
        return

    if request['request_type'] == 'add':
        email = request['param'][0]
        group_name = request['param'][1]
        verdict = database.add_user_to_group(email, group_name)
        if verdict:
            conn.send(f"{email} added to group {group_name}".encode(FORMAT))
        else:
            conn.send(f"{email} couldn't be added to {group_name}".encode(FORMAT))
        return

    if request['request_type'] == 'remove':
        email = request['param'][0]
        group_name = request['param'][1]
        verdict = database.remove_user_from_group(email, group_name)
        if verdict:
            conn.send(f"{email} removed from group {group_name}".encode(FORMAT))
        else:
            conn.send(f"{email} couldn't be removed from {group_name}".encode(FORMAT))
        return

    if request['request_type'] == 'init':
        filename = request['param']
        if not os.path.isfile(filename):
            conn.send(f"FILE NOT FOUND: {filename}".encode(FORMAT))
            return
        groups = request['groups']
        emails = database.get_all_users_from_groups(groups)

        for user in emails:
            database.add_pending_file(user, filename)

        for email in emails:
            if email in online:
                user = online[email]
                executor.submit(send_file_to_client, user['conn'], filename, user['user'])

        conn.send(f"Initiated {filename} to {', '.join(groups)}".encode(FORMAT))


def handle_regular_request(request, conn, sender):
    if request['request_type'] == 'list-groups':
        groups = database.get_groups_list()
        conn.send(numerize_list(groups).encode(FORMAT))
        return

    if request['request_type'] == 'my-groups':
        groups = database.get_user_groups(sender['email'])
        conn.send(numerize_list(groups).encode(FORMAT))
        return

    if request['request_type'] == 'join-group':
        if sender['is_admin']:
            conn.send("Admin cannot join groups!".encode(FORMAT))
            return
        group_name = request['param']
        verdict = database.create_join_request(sender['email'], group_name)
        if verdict:
            conn.send(f"Requested to join group {group_name}".encode(FORMAT))
        else:
            conn.send(f"Request to join {group_name} failed".encode(FORMAT))

    if request['request_type'] == 'received-file':
        if sender['is_admin']:
            conn.send("Admin cannot receive files!".encode(FORMAT))
            return
        filename = request['param']
        verdict = database.remove_pending_file(sender['email'], filename)
        if verdict:
            print(f"[UPDATE: {filename} RECEIVED BY {sender['email']}]")
        return


def handle_client(conn, addr):
    user = {
        "email": "",
        "is_admin": False,
        "key": ""
    }

    try:
        data = conn.recv(1024).decode(FORMAT)
        if not data:
            conn.close()
            return

        email, password = data.split(':')

        print(f"Verifying authentication request from {email}...")
        if not database.verify_user(email=email, password=password):
            print(f"Authentication request from {email} failed.")
            conn.sendall(b'Invalid credentials!')
            conn.close()
            return

        logging.info(f"[{email} ONLINE]")

        user["email"] = email
        user['key'] = database.get_user_private_key(email)
        user["is_admin"] = database.is_admin(email=email)

        if user["is_admin"]:
            conn.sendall(b"Connection Established. Admin Access Granted!")
        else:
            online[email] = {'conn': conn, 'user': user}
            conn.sendall(b'Connection Established.')
            executor.submit(apply_pending_files, conn, user)


        while True:
            client_message = conn.recv(1024).decode(FORMAT)
            if not client_message:
                remove_connection(email)
                conn.close()
                return

            print(f"[MESSAGE] {email}: {client_message}")
            parsed = parse_request(client_message)
            if not parsed['valid']:
                conn.sendall(b'Message Received. Not a Command!')
                continue

            if parsed['admin-only']:
                if not user['is_admin']:
                    conn.sendall(b'Invalid Command!')
                else:
                    handle_admin_request(parsed, conn, user)
            else:
                handle_regular_request(parsed, conn, user)
    except:
        conn.sendall(b"Invalid Request!")
        remove_connection(user['email'])
        conn.close()
        return


def start_server():
    server.listen()
    logging.info(f"[SERVER LISTENING ON {SERVER}:{PORT}]")

    while True:
        conn, addr = server.accept()
        client_thread = threading.Thread(target=handle_client, args=(conn, addr))
        client_thread.start()


if __name__ == '__main__':
    start_server()
