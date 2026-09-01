import socket
import sys
import threading

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 5000

cliente_ativo = True


def receber_mensagens(client_socket):
    global cliente_ativo

    while cliente_ativo:

        try:
            dados = client_socket.recv(1024)

            if not dados:
                print(
                    "\n[*] O servidor encerrou a conexão."
                )
                cliente_ativo = False
                break

            mensagem = dados.decode("utf-8")

            # Servidor solicita nickname
            if mensagem.strip() == "NICK":
                continue

            print(
                mensagem,
                end="",
                flush=True
            )

        except (ConnectionResetError, OSError):

            if cliente_ativo:
                print(
                    "\n[*] Conexão com o servidor encerrada."
                )

            cliente_ativo = False
            break


client = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)

try:

    print(
        f"[*] Conectando ao servidor {HOST}:{PORT}..."
    )

    client.connect((HOST, PORT))

    # Servidor envia NICK
    solicitacao = client.recv(1024)

    if solicitacao.decode("utf-8").strip() != "NICK":
        print("[!] Protocolo inválido.")
        sys.exit(1)

    nickname = input(
        "Digite seu nickname: "
    ).strip()

    if not nickname:
        print("[!] Nickname não pode ser vazio.")
        sys.exit(1)

    client.sendall(
        nickname.encode("utf-8")
    )

    # Thread dedicada ao recebimento
    thread = threading.Thread(
        target=receber_mensagens,
        args=(client,),
        daemon=True
    )

    thread.start()

    while cliente_ativo:

        try:
            mensagem = input("[Você]: ").strip()

        except EOFError:
            break

        if not mensagem:
            continue

        client.sendall(
            (mensagem + "\n").encode("utf-8")
        )

        if mensagem.lower() == "sair":
            cliente_ativo = False
            break

except ConnectionRefusedError:

    print(
        f"[-] Não foi possível conectar "
        f"ao servidor {HOST}:{PORT}."
    )

except KeyboardInterrupt:

    print("\n[*] Saindo...")

    try:
        client.sendall(
            "sair\n".encode("utf-8")
        )
    except:
        pass

except Exception as e:

    print(f"[-] Erro: {e}")

finally:

    cliente_ativo = False

    try:
        client.close()
    except:
        pass

    print("[*] Cliente finalizado.")