import socket

# --- Configuration ---
# Use the loopback address '127.0.0.1' to connect to a server on the same laptop
SERVER_HOST = '127.0.0.1' 
SERVER_PORT = 65432       
DOWNLOADED_FILE = 'downloaded_file.txt' 

def start_client():
    """Starts a simple P2P client to download a file from a server."""
    print("Starting P2P client...")
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print(f"Connecting to {SERVER_HOST}:{SERVER_PORT}...")
        try:
            s.connect((SERVER_HOST, SERVER_PORT))
            print("Connection successful.")
            
            file_data = b""
            while True:
                chunk = s.recv(1024)
                if not chunk:
                    break
                file_data += chunk
            
            with open(DOWNLOADED_FILE, 'wb') as f:
                f.write(file_data)
                
            print(f"File successfully downloaded and saved as '{DOWNLOADED_FILE}'.")
            
        except ConnectionRefusedError:
            print(f"Error: Connection to {SERVER_HOST}:{SERVER_PORT} was refused. "
                  "Please ensure the server is running.")
        
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    start_client()