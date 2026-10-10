import socket
import threading
from datetime import datetime

clients = set()
usernames = {}
clients_lock = threading.Lock()

host = "localhost"
port = 5000


def receive_line(client_socket, buffer=b""):
    while b"\n" not in buffer:
        chunk = client_socket.recv(1024)
        if not chunk:
            return None, buffer
        buffer += chunk

    line, buffer = buffer.split(b"\n", 1)
    return line.rstrip(b"\r").decode("utf-8"), buffer


def remove_client(client_socket):
    with clients_lock:
        clients.discard(client_socket)
        usernames.pop(client_socket, None)


def reject_client(client_socket, reason):
    try:
        client_socket.sendall((reason + "\n").encode("utf-8"))
    except OSError:
        pass
    finally:
        client_socket.close()


def broadcast(message, sender_socket=None):
    with clients_lock:
        recipients = clients.copy()

    for client_socket in recipients:
        if client_socket == sender_socket:
            continue
        try:
            client_socket.sendall(message)
        except OSError:
            remove_client(client_socket)
            client_socket.close()


def handle_client(client_socket, username, initial_buffer=b""):
    buffer = initial_buffer

    try:
        while True:
            chunk = client_socket.recv(1024)
            if not chunk:
                break
            buffer += chunk

            while b"\n" in buffer:
                raw_message, buffer = buffer.split(b"\n", 1)
                try:
                    message = raw_message.rstrip(b"\r").decode("utf-8")
                except UnicodeDecodeError:
                    return

                if not message.strip():
                    continue

                timestamp = datetime.now().strftime("%H:%M")
                formatted_message = f"[{timestamp}] {username}: {message}\n"
                broadcast(formatted_message.encode("utf-8"), client_socket)
    except OSError:
        pass
    finally:
        with clients_lock:
            was_connected = client_socket in clients
            clients.discard(client_socket)
            usernames.pop(client_socket, None)

        client_socket.close()
        if was_connected:
            timestamp = datetime.now().strftime("%H:%M")
            disconnect_message = f"[{timestamp}] {username} has disconnected.\n"
            broadcast(disconnect_message.encode("utf-8"), client_socket)


def serve(server_socket, stop_event=None):
    print("Server is listening...")
    server_socket.settimeout(0.5)

    while stop_event is None or not stop_event.is_set():
        try:
            client_socket, address = server_socket.accept()
        except socket.timeout:
            continue

        try:
            username, initial_buffer = receive_line(client_socket)
            if username is None:
                client_socket.close()
                continue
        except (OSError, UnicodeDecodeError):
            client_socket.close()
            continue
        username = username.strip()
        if not username:
            reject_client(client_socket, "Username cannot be empty.")
            continue

        with clients_lock:
            username_taken = username in usernames.values()
            if not username_taken:
                clients.add(client_socket)
                usernames[client_socket] = username

        if username_taken:
            reject_client(client_socket, "Username already taken. Please choose a different username.")
            continue

        try:
            client_socket.sendall(b"OK\n")
        except OSError:
            remove_client(client_socket)
            client_socket.close()
            continue

        timestamp = datetime.now().strftime("%H:%M")
        join_message = f"[{timestamp}] {username} has joined the chat.\n"
        broadcast(join_message.encode("utf-8"), client_socket)
        print("Client connected:", address)
        threading.Thread(
            target=handle_client,
            args=(client_socket, username, initial_buffer),
            daemon=True,
        ).start()


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        server_socket.listen(5)
        serve(server_socket)


if __name__ == "__main__":
    main()
