import sqlite3
from utils import hash_password, verify_password
from utils import derive_key_from_password

DB_FILE = "database.db"


def raise_db_error(message):
    print("DB ERROR: ", message)


class Database:
    conn = None

    def __init__(self, db_file=DB_FILE):
        try:
            self.conn = sqlite3.connect(db_file, check_same_thread=False)
        except sqlite3.Error as e:
            print(e)

    def initiate_tables(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS users
                              (id INTEGER PRIMARY KEY , 
                               email VARCHAR(255) UNIQUE NOT NULL, 
                               password VARCHAR(255), 
                               private_key VARCHAR(255),
                               is_admin BOOLEAN DEFAULT false)
                               ''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS groups 
                            (id INTEGER PRIMARY KEY ,
                            group_name VARCHAR(100) UNIQUE NOT NULL,
                            description TEXT)
                            ''')

            self.conn.commit()

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS groups_users 
                (user_id INTEGER,
                group_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (group_id) REFERENCES groups(id),
                PRIMARY KEY (user_id, group_id))
                ''')

            cursor.execute('''
                        CREATE TABLE IF NOT EXISTS pending_files (
                        user_id INTEGER,
                        filename VARCHAR(255), 
                        FOREIGN KEY (user_id) REFERENCES users(id)
                        PRIMARY KEY (user_id, filename))
                        ''')

            cursor.execute('''
                        CREATE TABLE IF NOT EXISTS group_join_requests 
                        (user_id INTEGER,
                        group_id INTEGER,
                        FOREIGN KEY (user_id) REFERENCES users(id),
                        FOREIGN KEY (group_id) REFERENCES groups(id),
                        PRIMARY KEY (user_id, group_id))
                        ''')

            self.conn.commit()
        except sqlite3.Error as e:
            print(e)

    """ ---CREATE--- """

    def insert_user(self, email, password):
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM users WHERE email = ?', (email,))
            email_exists = cursor.fetchone()[0] > 0
            if email_exists:
                return False

            hashed_password = hash_password(password)
            key = derive_key_from_password(password)
            user_data = (email, hashed_password, key)
            sql = f''' INSERT INTO users(email, password, private_key) VALUES( ?, ?, ?) '''
            cursor = self.conn.cursor()
            cursor.execute(sql, user_data)
            self.conn.commit()
            return True
        except Exception as e:
            raise_db_error(e)
            return False

    def insert_group(self, group_name, description=""):
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM groups WHERE group_name = ?', (group_name,))
            group_exists = cursor.fetchone()[0] > 0
            if group_exists:
                return False
            sql = '''INSERT INTO groups(group_name, description) VALUES(?, ?)'''
            cursor = self.conn.cursor()
            cursor.execute(sql, (group_name, description))
            self.conn.commit()
            return True
        except Exception as e:
            raise_db_error(e)
            return False

    def add_user_to_group(self, email, group_name):
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            result = cursor.fetchone()

            if result is None:
                return False

            user_id = result[0]

            cursor.execute('SELECT id FROM groups WHERE group_name = ?', (group_name,))
            result = cursor.fetchone()
            if result is None:
                return False

            group_id = result[0]
            cursor.execute('''
                DELETE FROM group_join_requests
                WHERE user_id = ? AND group_id = ?
            ''', (user_id, group_id))

            cursor.execute('''
                INSERT OR IGNORE INTO groups_users (user_id, group_id)
                VALUES (?, ?)
            ''', (user_id, group_id))

            self.conn.commit()
            return True
        except Exception as e:
            raise_db_error(e)
            return False

    def add_pending_file(self, email, filename):
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            result = cursor.fetchone()
            if result is None:
                return False
            user_id = result[0]

            cursor.execute('''
                                INSERT OR IGNORE INTO pending_files (user_id, filename)
                                VALUES (?, ?)
                                ''', (user_id, filename))

            self.conn.commit()
            return True
        except Exception as e:
            raise_db_error(e)
            return False

    def create_super_user(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users WHERE email = ?', ("admin",))
        admin_exists = cursor.fetchone()[0] > 0
        if admin_exists:
            return
        password = "admin"
        hashed_password = hash_password(password)
        key = derive_key_from_password(password)
        user_data = ("admin", hashed_password, key, True)
        sql = f''' INSERT INTO users(email, password, private_key, is_admin) VALUES( ?, ?, ?, ?) '''
        cursor = self.conn.cursor()
        cursor.execute(sql, user_data)
        self.conn.commit()
        return cursor.lastrowid

    def create_join_request(self, email, group_name):
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            result = cursor.fetchone()

            if result is None:
                return False

            user_id = result[0]

            cursor.execute('SELECT id FROM groups WHERE group_name = ?', (group_name,))
            result = cursor.fetchone()

            if result is None:
                return False

            group_id = result[0]

            cursor.execute('''
                                SELECT 1 FROM groups_users WHERE user_id = ? AND group_id = ?
                                ''', (user_id, group_id))

            if cursor.fetchone() is not None:
                return False

            cursor.execute('''
                                INSERT OR IGNORE INTO group_join_requests (user_id, group_id)
                                VALUES (?, ?)
                                ''', (user_id, group_id))

            self.conn.commit()
            return True

        except:
            return False

    """ ---QUERY--- """

    def get_users_list(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT (email) FROM users")
            users = cursor.fetchall()
            result = []
            for user in users:
                result.append(user[0])
            return result
        except Exception as e:
            raise_db_error(e)
            return []

    def get_groups_list(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT (group_name) FROM groups")
            groups = cursor.fetchall()
            result = []
            for group in groups:
                result.append(group[0])
            return result
        except Exception as e:
            raise_db_error(e)
            return []

    def verify_user(self, email, password):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''SELECT password  FROM users WHERE email = ?''', (email,))
            data = cursor.fetchone()
            if not data:
                return False
            hashed_password = data[0]
            if hashed_password:
                if verify_password(password, hashed_password):
                    return True
                else:
                    return False
            else:
                return False
        except Exception as e:
            raise_db_error(e)
            return False

    def is_admin(self, email):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''SELECT is_admin FROM users WHERE email = ?''', (email,))
            data = cursor.fetchone()
            if data:
                return data[0]
            else:
                return False
        except Exception as e:
            raise_db_error(e)
            return False

    def get_user_private_key(self, email):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''SELECT private_key FROM users WHERE email = ?''', (email,))
            key = cursor.fetchone()[0]
            return key
        except Exception as e:
            raise_db_error(e)
            return "invalid email"

    def get_all_users_from_groups(self, groups):
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id FROM groups WHERE group_name IN ({seq})'.format(
                seq=','.join(['?'] * len(groups))),
                tuple(groups)
            )

            result = cursor.fetchall()
            if not result:
                return []

            group_ids = [group_id[0] for group_id in result]

            cursor.execute('''
                SELECT DISTINCT user_id
                FROM groups_users
                WHERE group_id IN ({seq})
            '''.format(seq=','.join(['?'] * len(group_ids))),
                           tuple(group_ids)
                           )

            result = cursor.fetchall()
            if not result:
                return []
            user_ids = [user_id[0] for user_id in result]
            cursor.execute('''
                SELECT (email)
                FROM users
                WHERE id IN ({seq})
            '''.format(seq=','.join(['?'] * len(user_ids))),
                           tuple(user_ids)
                           )
            result = cursor.fetchall()
            emails = [user[0] for user in result]
            return emails
        except Exception as e:
            raise_db_error(e)
            return []

    def get_pending_filenames(self, email):
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            result = cursor.fetchone()

            if result is None:
                print("User not found.")
                return []

            user_id = result[0]
            cursor.execute('''
                SELECT filename
                FROM pending_files
                WHERE user_id = ?
            ''', (user_id,))

            filenames = cursor.fetchall()

            filenames = [filename[0] for filename in filenames]

            return filenames
        except:
            return []

    def get_user_groups(self, email):
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            result = cursor.fetchone()

            if result is None:
                return []

            user_id = result[0]
            cursor.execute('''
                SELECT groups.group_name
                FROM groups
                JOIN groups_users ON groups.id = groups_users.group_id
                WHERE groups_users.user_id = ?
            ''', (user_id,))

            result = cursor.fetchall()
            groups = [group_name[0] for group_name in result]
            return groups
        except:
            return []

    def get_join_requests(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT users.email, groups.group_name
            FROM group_join_requests
            JOIN users ON group_join_requests.user_id = users.id
            JOIN groups ON group_join_requests.group_id = groups.id
        ''')

        result = cursor.fetchall()
        requests = [
            {"email": row[0], "group_name": row[1]}
            for row in result
        ]
        return requests

    """ ---DELETE--- """

    def remove_pending_file(self, email, filename):
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            result = cursor.fetchone()

            if result is None:
                return True

            user_id = result[0]
            cursor.execute('''
                DELETE FROM pending_files
                WHERE user_id = ? AND filename = ?
            ''', (user_id, filename))
            self.conn.commit()
            return True
        except Exception as e:
            raise_db_error(e)
            return False

    def remove_user_from_group(self, email, group_name):
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            result = cursor.fetchone()
            if result is None:
                return True

            user_id = result[0]

            cursor.execute('SELECT id FROM groups WHERE group_name = ?', (group_name,))
            result = cursor.fetchone()
            if result is None:
                return True

            group_id = result[0]

            cursor.execute('''
                DELETE FROM groups_users
                WHERE user_id = ? AND group_id = ?
            ''', (user_id, group_id))

            self.conn.commit()
            return True
        except Exception as e:
            raise_db_error(e)
            return False

    def delete_group(self, group_name):
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id FROM groups WHERE group_name = ?', (group_name,))
            result = cursor.fetchone()

            if result is None:
                return True

            group_id = result[0]
            cursor.execute('DELETE FROM groups_users WHERE group_id = ?', (group_id,))
            cursor.execute('DELETE FROM groups WHERE id = ?', (group_id,))
            self.conn.commit()
            return True
        except:
            return False


def generate_dummy_data():
    conn = Database()
    conn.initiate_tables()
    conn.create_super_user()

    users = [[f"user{i}@gmail.com", f'user{i}'] for i in range(1, 11)]
    groups = [f'group{i}' for i in range(1, 6)]

    users_count = 0
    groups_count = 0
    relations_count = 0

    for user in users:
        users_count += conn.insert_user(user[0], user[1])
    for group_name in groups:
        groups_count += conn.insert_group(group_name)

    print(f"{users_count} users generated.")
    print(f"{groups_count} groups generated.")

    for i in range(5):
        relations_count += conn.add_user_to_group(users[i][0], groups[i])
        relations_count += conn.add_user_to_group(users[i + 5][0], groups[i])

    print(f"{relations_count} relations generated.")
    print("DATABASE DUMMY ENTRIES GENERATED SUCCESSFULLY!")

if __name__ == "__main__":
    generate_dummy_data()
