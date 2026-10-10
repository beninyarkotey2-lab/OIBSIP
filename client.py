import socket
import threading

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


def receive_messages(client_socket, initial_buffer=b""):
    buffer = initial_buffer
    while True:
        try:
            chunk = client_socket.recv(1024)
            if not chunk:
                if buffer:
                    try:
                        print(buffer.decode("utf-8"))
                    except UnicodeDecodeError:
                        print("Received an invalid message from the server.")
                print("Server disconnected.")
                return
            buffer += chunk

            while b"\n" in buffer:
                raw_message, buffer = buffer.split(b"\n", 1)
                try:
                    message = raw_message.rstrip(b"\r").decode("utf-8")
                except UnicodeDecodeError:
                    print("Received an invalid message from the server.")
                    return
                print("\n" + message)
        except OSError:
            return


def main():
    while True:
        try:
            username = input("Enter your username: ").strip()
        except EOFError:
            return
        if username:
            break
        print("Username cannot be empty.")

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((host, port))
        client_socket.sendall((username + "\n").encode("utf-8"))
        response, initial_buffer = receive_line(client_socket)
    except (OSError, UnicodeDecodeError) as error:
        print(f"Could not connect to the chat server: {error}")
        client_socket.close()
        return

    if response != "OK":
        print(response or "Server disconnected before accepting the username.")
        client_socket.close()
        return

    print("Connected to server!")
    threading.Thread(
        target=receive_messages,
        args=(client_socket, initial_buffer),
        daemon=True,
    ).start()

    try:
        while True:
            message = input("You: ")
            if not message:
                continue
            client_socket.sendall((message + "\n").encode("utf-8"))
    except EOFError:
        pass
    except OSError:
        print("Connection closed.")
    finally:
        client_socket.close()


if __name__ == "__main__":
    main()
