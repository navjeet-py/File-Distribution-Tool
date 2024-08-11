import socket
import sys
import threading
from utils import derive_key_from_password, decrypt_file
import tqdm
from constants import PORT, SERVER, FORMAT, CHUNK_SIZE

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER, PORT))
print("Initialising Connection...\n")

global key


def refresh_input_line():
    print(">>> ", end='')
    sys.stdout.flush()


def verify_credentials(email, password):
    credentials = f"{email}:{password}"
    client_socket.sendall(credentials.encode(FORMAT))
    response = client_socket.recv(1024).decode(FORMAT)
    print(f"Server response: {response}\n")
    if "Connection Established" not in response:
        return {'connected': False, 'is_admin': False}
    if "Admin Access Granted" not in response:
        return {'connected': True, 'is_admin': False}
    return {'connected': True, 'is_admin': True}


def receive_messages():
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            print(f"[MESSAGE FROM SERVER]: {message}\n")


            message = list(message.split())
            if message[0] != 'file':
                continue

            assert len(message) == 4
            assert message[2] == '-size'

            filename = message[1]
            filesize = int(message[3])
            print(f"[PREPARING TO RECEIVE FILE: {filename}\n")

            file_bytes = bytearray()
            progress = tqdm.tqdm(unit='B', unit_scale=True, unit_divisor=True, total=filesize)
            done = False

            length = 0

            while not done:
                data = client_socket.recv(CHUNK_SIZE)
                if b'<END>' in data:
                    end_marker_index = data.index(b'<END>')
                    file_bytes.extend(decrypt_file(data[:end_marker_index], key))
                    file = open(filename, 'wb')
                    file.write(file_bytes)
                    file.close()
                    remaining_bytes = filesize - length + len(b'<END>')
                    progress.update(remaining_bytes)
                    break

                file_bytes.extend(decrypt_file(data, key))
                length += len(data)
                progress.update(len(data))
            progress.close()
            print('\n')
            file.close()
            print(f"[FILE {filename} RECEIVED SUCCESSFULLY]\n")
            client_socket.send(f"received-file {filename}".encode(FORMAT))
            refresh_input_line()

        except:
            continue
    client_socket.close()


def send_messages():
    try:
        while True:
            request = input(">>> ")
            client_socket.send(request.encode(FORMAT))
            continue
    except Exception as e:
        print("Disconnected from server!\n", e)
        client_socket.close()


if __name__ == '__main__':
    email = input("Enter username: ")
    password = input("Enter password: ")
    status = verify_credentials(email, password)

    if not status['connected']:
        print("Connection Failed!\n")
        client_socket.close()
        exit(0)

    key = derive_key_from_password(password)

    thread_send = threading.Thread(target=send_messages, args=())
    thread_send.start()

    thread_receive = threading.Thread(target=receive_messages, args=())
    thread_receive.start()

