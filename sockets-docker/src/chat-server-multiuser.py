import socket
import sys
import threading

HOST = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 5000

# Dicionário:
# socket -> {"nickname": ..., "endereco": ...}
clientes = {}

# Lock para evitar duas threads alterando o dicionário ao mesmo tempo
clientes_lock = threading.Lock()

servidor_no_chat = True
servidor_ativo = True


def broadcast(mensagem, remetente=None):
    """
    Envia uma mensagem para todos os clientes,
    exceto opcionalmente quem a enviou.
    """

    clientes_desconectados = []

    with clientes_lock:
        lista_clientes = list(clientes.keys())

    for cliente in lista_clientes:
        if cliente == remetente:
            continue

        try:
            cliente.sendall(mensagem.encode("utf-8"))
        except:
            clientes_desconectados.append(cliente)

    for cliente in clientes_desconectados:
        remover_cliente(cliente)


def remover_cliente(client_socket):
    with clientes_lock:
        dados = clientes.pop(client_socket, None)

    if dados:
        nickname = dados["nickname"]
        endereco = dados["endereco"]

        print(f"[-] {nickname} ({endereco[0]}) saiu do chat.")

        try:
            client_socket.close()
        except:
            pass

        broadcast(
            f"\n[SISTEMA]: {nickname} saiu do chat.\n[Você]: "
        )


def listar_usuarios():
    with clientes_lock:
        if not clientes:
            return "Nenhum cliente conectado."

        linhas = []

        for dados in clientes.values():
            nickname = dados["nickname"]
            ip = dados["endereco"][0]

            linhas.append(f"- {nickname} ({ip})")

    return "\n".join(linhas)


def encontrar_cliente_por_nickname(nickname):
    with clientes_lock:
        for client_socket, dados in clientes.items():
            if dados["nickname"].lower() == nickname.lower():
                return client_socket, dados

    return None, None


def gerenciar_cliente(client_socket, endereco):
    try:
        # Primeira mensagem enviada pelo cliente será o nickname
        client_socket.sendall(
            b"NICK\n"
        )

        dados = client_socket.recv(1024)

        if not dados:
            client_socket.close()
            return

        nickname = dados.decode("utf-8").strip()

        # Evita nickname vazio
        if not nickname:
            nickname = f"usuario_{endereco[1]}"

        # Verifica nickname duplicado
        with clientes_lock:
            nicknames = [
                dados_cliente["nickname"].lower()
                for dados_cliente in clientes.values()
            ]

        if nickname.lower() in nicknames:
            client_socket.sendall(
                "ERRO Nickname já está em uso.\n".encode()
            )
            client_socket.close()
            return

        with clientes_lock:
            clientes[client_socket] = {
                "nickname": nickname,
                "endereco": endereco
            }

        ip = endereco[0]

        print(f"[+] {nickname} ({ip}) entrou no chat.")

        client_socket.sendall(
            (
                f"[+] Bem-vindo, {nickname}!\n"
                f"[+] Seu IP no chat: {ip}\n"
                f"[+] Digite 'ajuda' para ver os comandos.\n"
            ).encode()
        )

        broadcast(
            f"\n[SISTEMA]: {nickname} ({ip}) entrou no chat.\n[Você]: ",
            remetente=client_socket
        )

        while True:
            dados = client_socket.recv(1024)

            if not dados:
                break

            mensagem = dados.decode("utf-8").strip()

            if not mensagem:
                continue

            # ---------------------------
            # COMANDO: sair
            # ---------------------------

            if mensagem.lower() == "sair":
                client_socket.sendall(
                    "[SISTEMA]: Você saiu do chat.\n".encode("utf-8")
                )
                break

            # ---------------------------
            # COMANDO: ajuda
            # ---------------------------

            if mensagem.lower() == "ajuda":

                ajuda = (
                    "\n=== COMANDOS DO CLIENTE ===\n"
                    "ajuda     - mostra esta lista\n"
                    "usuarios  - mostra usuários conectados\n"
                    "sair      - sai do chat\n"
                    "===========================\n"
                    "[Você]: "
                )

                client_socket.sendall(
                    ajuda.encode("utf-8")
                )

                continue

            # ---------------------------
            # COMANDO: usuarios
            # ---------------------------

            if mensagem.lower() == "usuarios":

                resposta = (
                    "\n=== USUÁRIOS CONECTADOS ===\n"
                    + listar_usuarios()
                    + "\n============================\n"
                    "[Você]: "
                )

                client_socket.sendall(
                    resposta.encode("utf-8")
                )

                continue

            # ---------------------------
            # MENSAGEM NORMAL
            # ---------------------------

            mensagem_formatada = (
                f"\n[{nickname} - {ip}]: {mensagem}\n"
                f"[Você]: "
            )

            print(
                f"[{nickname} - {ip}]: {mensagem}"
            )

            broadcast(
                mensagem_formatada,
                remetente=client_socket
            )

    except (ConnectionResetError, OSError):
        pass

    except Exception as e:
        print(f"[-] Erro com cliente {endereco}: {e}")

    finally:
        remover_cliente(client_socket)


def aceitar_clientes(server):
    global servidor_ativo

    while servidor_ativo:
        try:
            client_socket, endereco = server.accept()

            thread = threading.Thread(
                target=gerenciar_cliente,
                args=(client_socket, endereco),
                daemon=True
            )

            thread.start()

        except OSError:
            break


# ------------------------------------------------
# SOCKET PRINCIPAL
# ------------------------------------------------

server = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)

server.setsockopt(
    socket.SOL_SOCKET,
    socket.SO_REUSEADDR,
    1
)

server.bind((HOST, PORT))

# Exercício pede até 10 conexões
server.listen(10)

print(
    f"[*] Servidor de chat rodando em {HOST}:{PORT}"
)

print(
    "[*] Aguardando clientes..."
)

# Thread fica responsável apenas pelos accept()
thread_accept = threading.Thread(
    target=aceitar_clientes,
    args=(server,),
    daemon=True
)

thread_accept.start()


def mostrar_ajuda_servidor():
    print(
        """
=== COMANDOS DO SERVIDOR ===

ajuda
    Mostra esta lista.

usuarios
    Lista os usuários conectados.

sair
    Servidor sai da conversa, mas continua
    recebendo e encaminhando mensagens.

entrar
    Servidor volta a participar da conversa.

kick <nickname>
    Expulsa um cliente.

encerrar
    Encerra todo o servidor e desconecta
    todos os clientes.

============================
"""
    )


mostrar_ajuda_servidor()


# ------------------------------------------------
# CONSOLE DO SERVIDOR
# ------------------------------------------------

try:

    while servidor_ativo:

        comando = input("[Servidor]: ").strip()

        if not comando:
            continue

        # AJUDA

        if comando.lower() == "ajuda":
            mostrar_ajuda_servidor()
            continue

        # USUARIOS

        if comando.lower() == "usuarios":

            print("\n=== USUÁRIOS CONECTADOS ===")
            print(listar_usuarios())
            print("============================\n")

            continue

        # SERVIDOR SAI DA CONVERSA

        if comando.lower() == "sair":

            if servidor_no_chat:
                servidor_no_chat = False

                print(
                    "[*] Servidor saiu da conversa."
                )

                print(
                    "[*] O encaminhamento continua ativo."
                )

                broadcast(
                    "\n[SISTEMA]: Servidor saiu da conversa.\n"
                    "[Você]: "
                )

            else:
                print("[*] Servidor já está fora da conversa.")

            continue

        # SERVIDOR ENTRA NOVAMENTE

        if comando.lower() == "entrar":

            if not servidor_no_chat:
                servidor_no_chat = True

                print(
                    "[*] Servidor entrou novamente na conversa."
                )

                broadcast(
                    "\n[SISTEMA]: Servidor entrou na conversa.\n"
                    "[Você]: "
                )

            else:
                print("[*] Servidor já está na conversa.")

            continue

        # KICK

        if comando.lower().startswith("kick "):

            nickname = comando[5:].strip()

            if not nickname:
                print(
                    "[!] Uso correto: kick <nickname>"
                )
                continue

            cliente, dados_cliente = \
                encontrar_cliente_por_nickname(nickname)

            if cliente is None:
                print(
                    f"[!] Usuário '{nickname}' não encontrado."
                )
                continue

            try:
                cliente.sendall(
                    (
                        "\n[SISTEMA]: Você foi expulso "
                        "pelo administrador.\n"
                    ).encode("utf-8")
                )

                cliente.shutdown(socket.SHUT_RDWR)

            except:
                pass

            cliente.close()

            remover_cliente(cliente)

            print(
                f"[*] Usuário {nickname} foi expulso."
            )

            continue

        # ENCERRAR

        if comando.lower() == "encerrar":

            print("[*] Encerrando o chat...")

            servidor_ativo = False

            broadcast(
                "\n[SISTEMA]: O servidor encerrou o chat.\n"
            )

            with clientes_lock:
                lista_clientes = list(clientes.keys())

            for cliente in lista_clientes:
                try:
                    cliente.shutdown(socket.SHUT_RDWR)
                except:
                    pass

                try:
                    cliente.close()
                except:
                    pass

            break

        # MENSAGEM NORMAL DO SERVIDOR

        if servidor_no_chat:

            mensagem = (
                f"\n[Servidor]: {comando}\n"
                f"[Você]: "
            )

            broadcast(mensagem)

        else:
            print(
                "[!] O servidor está fora da conversa."
            )

            print(
                "[!] Digite 'entrar' para voltar ao chat."
            )

except KeyboardInterrupt:
    print("\n[*] Ctrl+C detectado.")

finally:

    servidor_ativo = False

    try:
        server.close()
    except:
        pass

    with clientes_lock:
        lista_clientes = list(clientes.keys())

    for cliente in lista_clientes:
        try:
            cliente.close()
        except:
            pass

    print("[*] Servidor finalizado.")