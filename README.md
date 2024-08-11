# File-Distribution-Tool

A Python-based file distribution tool designed for efficient and secure file transfer and communication between clients and a server.

### How to run
1. Clone or download the repository
2. Ensure you have Python3 installed. Create and activate a virtual environment inside the project directory. Install the required packages listed in `r.txt`.
    ```
    cd project_directory
    virtualenv venv
    source venv/bin/activate
    pip install -r r.txt
    ```
3. we can generate dummy data for the database for testing purposes.To do so, run `db.py` file once. 
    ```
    cd server
    python3 db.py
    ```
4. Start the server.
   ```
   cd server
   python3 server.py
   ```
5. Start the client. We can run multiple clients and authenticate them with different credentials.
   ```
   cd client
   python3 client.py
   ```
   

### Commands to communicate
#### General Commands (Any user can make)
1. `list-groups`: gives the list of all groups available
2. `join-group {group_name}`: request to join group with name group_name, eg. `join-group group1`
3. `my-groups`: to get the list of groups they're already part of



#### Admin Commands
1. `create-group group_name`: to create a group with name group_name
2. `delete-group group_name`: to delete the group with name group_name, if exists
3. `list-users`: to get the list of all users' emails
4. `view-requests`: to see all the pending group joining requests
5. `add user_email group_name`: to add this particular user to the group named group_name
6. `remove user_email group_name`: to remove this particular user from the group named group_name
7. `clear-requests`: reject all the pending requests
8. `init filename group1 group2 ...`: to initialize sending file named filename to all the users who belong to atleast one of the listed group names

### Authentication (If using dummy data)
1. We have generated an admin with 'admin' as both email and password.
2. Also, we generated 10 users with their emails as user1@gmail.com, user2@gmail.com, etc. And their respective passwords are user1, user2, etc.
3. We also have 5 groups with names group1, group2, and so on. 2 users are assigned to each group.


