import socket

PORT = 8800
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
FIXED_SALT = b'\xa3\xd8\x7b\x1c\xe4\x9f\x23\x47\x91\x6e\xc8\x34\x12\xab\xcd\xef'

ADMIN_COMMANDS = ['init', 'create-group', 'delete-group', 'list-users', 'view-requests', 'add', 'remove']
GENERAL_COMMANDS = ['list-groups', 'join-group', 'received-file', 'my-groups']

CHUNK_SIZE = 128 * 1024

MAX_CONCURRENT_TRANSFERS = 5



