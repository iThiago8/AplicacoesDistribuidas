import socket
import sys
import threading

HOST = sys.argv[1] if len(sys.argv) > 1 else '0.0.0.0'
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 5000

# Função que roda em paralelo apenas para RECEBER mensagens do cliente
def receber_mensagens(client_socket, client_address):
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                print(f"\n[*] O cliente {client_address[0]} desconectou.")
                break

            print(f"\n[Cliente {client_address[0]}]: {data.decode('utf-8').strip()}")
            print("[Você]: ", end="", flush=True)
        except:
            break

    client_socket.close()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(1)

print(f"[*] Sala de Chat aguardando conexão em {HOST}:{PORT}...")

try:
    # O accept() roda uma única vez para pegar o primeiro cliente que chegar
    client_socket, client_address = server.accept()

    # Passamos o 'client_address' (que contém o IP real) para a Thread usar no print
    print(f"[+] Cliente real conectado do IP: {client_address[0]} (Porta: {client_address[1]})")

    # Inicia a Thread para escutar esse cliente específico em background
    t = threading.Thread(target=receber_mensagens, args=(client_socket, client_address), daemon=True)
    t.start()

    # O loop principal do servidor fica livre apenas para ENVIAR mensagens
    while True:
        mensagem = input("[Você]: ")
        if mensagem.lower() == 'sair':
            break

        client_socket.sendall((mensagem + "\n").encode('utf-8'))

    client_socket.close()
except KeyboardInterrupt:
    print("\n[*] Chat encerrado pelo servidor...")
finally:
    server.close()
