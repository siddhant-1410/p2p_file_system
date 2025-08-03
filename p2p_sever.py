import socket

# --- Configuration ---
HOST = '0.0.0.0'  # Listen on all available network interfaces
PORT = 65432      # Port to listen on (non-privileged ports are > 1023)
FILE_TO_SHARE = 'shared_file.txt' # The name of the file to share

def start_server():
    """Starts a simple P2P server that shares a single file."""
    print("Starting P2P server...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Bind the socket to the specified host and port
        s.bind((HOST, PORT))
        # Listen for incoming connections
        s.listen()
        print(f"Server is listening on {HOST}:{PORT}")

        # Wait for a client to connect
        conn, addr = s.accept()
        with conn:
            print(f"Connected by {addr}")
            
            try:
                # Open the file and read its contents
                with open(FILE_TO_SHARE, 'rb') as f:
                    file_data = f.read()
                
                # Send the file data to the client
                conn.sendall(file_data)
                print(f"Successfully sent '{FILE_TO_SHARE}' to {addr}")

            except FileNotFoundError:
                print(f"Error: The file '{FILE_TO_SHARE}' was not found.")
            
            except Exception as e:
                print(f"An error occurred: {e}")

if __name__ == "__main__":
    start_server()