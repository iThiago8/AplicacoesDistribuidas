import socket
import sys
import threading

HOST = sys.argv[1] if len(sys.argv) > 1 else '127.0.0.1'
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 5000


def receber_mensagens(client_socket):
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                print("\n[*] Você foi desconectado do servidor central.")
                break

            # O servidor já manda a mensagem formatada com o IP/Porta de quem enviou
            print(data.decode('utf-8'), end="", flush=True)
        except:
            break
    client_socket.close()


client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    print(f"[*] Conectando ao Servidor de Broadcast em {HOST}:{PORT}...")
    client.connect((HOST, PORT))
    print("[+] Conectado à sala global! Todos os alunos verão suas mensagens.\n")
    print("Digite suas mensagens livremente. Digite 'sair' para encerrar.")
    print("-" * 50)

    # A Thread de recebimento garante que as mensagens dos outros alunos
    # apareçam na tela imediatamente, mesmo se este aluno estiver digitando
    t = threading.Thread(target=receber_mensagens, args=(client,), daemon=True)
    t.start()

    while True:
        mensagem = input("[Você]: ")
        mensagem_limpa = mensagem.strip()

        if not mensagem_limpa:
            continue

        if mensagem_limpa.lower() == 'sair':
            client.sendall("sair\n".encode('utf-8'))
            break

        client.sendall((mensagem_limpa + "\n").encode('utf-8'))
except KeyboardInterrupt:
    print("\n[*] Você saiu da sala (Ctrl+C).")
except ConnectionRefusedError:
    print(f"[-] Erro: O servidor de broadcast não está rodando em {HOST}:{PORT}.")
finally:
    client.close()
    print("[*] Programa finalizado.")
