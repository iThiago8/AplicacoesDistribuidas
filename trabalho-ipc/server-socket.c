#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <ctype.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <sys/select.h>

#define PORT 3490

int main() {
    // server_sockfd: escuta novas conexões | ativo_sockfd: armazena o cliente que está conversando (-1 = livre)
    int server_sockfd, ativo_sockfd = -1;
    struct sockaddr_in server_address, client_address;
    socklen_t client_len;
    int opt = 1;       // Opção usada no setsockopt
    int rodando = 1;   // Flag de controle do loop do servidor

    // Buffers e estruturas para recuperar e diagnosticar os dados do hostname local
    char hostbuffer[256];
    struct addrinfo hints, *res;
    char ipstr[INET_ADDRSTRLEN];
    
    // Conjunto de descritores de arquivos lidos pelo select()
    fd_set read_fds;

    // 1. Recupera o nome de rede deste computador atual (hostname)
    if (gethostname(hostbuffer, sizeof(hostbuffer)) != 0) {
        perror("Erro ao obter hostname");
        exit(EXIT_FAILURE);
    }

    // 2. Define os critérios para traduzir o hostname em um endereço IP IPv4
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_INET;       // Restringe a busca apenas para IPv4
    hints.ai_socktype = SOCK_STREAM; // Restringe a busca para conexões TCP

    // 3. Consulta o sistema operacional buscando os dados de endereço vinculados ao hostname
    if (getaddrinfo(hostbuffer, NULL, &hints, &res) != 0) {
        perror("Erro ao obter endereço IP do host");
        exit(EXIT_FAILURE);
    }

    // 4. Converte o IP binário encontrado em uma string legível para exibição visual
    struct sockaddr_in *ipv4 = (struct sockaddr_in *)res->ai_addr;
    inet_ntop(AF_INET, &(ipv4->sin_addr), ipstr, sizeof(ipstr));

    // Exibe o cabeçalho organizacional do Servidor na inicialização
    printf("=======================================================\n");
    printf(" ߖů؏  SISTEMA INICIADO: Servidor IPC Local\n");
    printf(" Hostname do Computador: [%s]\n", hostbuffer);
    printf(" Endereço IP na Rede...: [%s]\n", ipstr);
    printf(" Porta de Comunicação..: [%d]\n", PORT);
    printf("=======================================================\n");
    printf(" ߑɠDigite 'sair' a qualquer momento para finalizar.\n");
    printf("-------------------------------------------------------\n\n");
    printf("⏳ Aguardando conexões na rede...\n\n");
    fflush(stdout);

    freeaddrinfo(res); // Libera a memória da estrutura alocada pelo getaddrinfo

    // 5. Cria o socket principal do servidor (IPv4, Fluxo TCP de dados)
    server_sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_sockfd < 0) {
        perror("Erro ao criar o socket do servidor");
        exit(EXIT_FAILURE);
    }

    // 6. Configura o socket para liberar a porta 3490 imediatamente caso o programa seja fechado
    if (setsockopt(server_sockfd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0) {
        perror("Erro no setsockopt");
        close(server_sockfd);
        exit(EXIT_FAILURE);
    }

    // 7. Prepara as configurações de vinculação de rede: aceita conexões de qualquer placa local
    memset(&server_address, 0, sizeof(server_address));
    server_address.sin_family = AF_INET;
    server_address.sin_port = htons(PORT);
    server_address.sin_addr.s_addr = INADDR_ANY;

    // 8. Vincula fisicamente a porta 3490 ao socket do nosso programa
    if (bind(server_sockfd, (struct sockaddr *)&server_address, sizeof(server_address)) < 0) {
        perror("Erro no comando bind");
        close(server_sockfd);
        exit(EXIT_FAILURE);
    }

    // 9. Coloca o servidor em modo de escuta ativa na rede
    if (listen(server_sockfd, 1) < 0) { 
        perror("Erro no comando listen");
        close(server_sockfd);
        exit(EXIT_FAILURE);
    }

    // =========================================================================
    // LOOP MULTIPLEXADO NÃO-BLOQUEANTE (SELECT)
    // =========================================================================
    while (rodando) {
        FD_ZERO(&read_fds); // Limpa o conjunto de descritores antes de cada monitoramento

        // Adiciona a Entrada Padrão (Teclado do Servidor - STDIN_FILENO) e o Socket do Servidor
        FD_SET(STDIN_FILENO, &read_fds);
        FD_SET(server_sockfd, &read_fds); 
        
        // Define o limite numérico máximo de descritores para o select() monitorar
        int max_fd = (server_sockfd > STDIN_FILENO) ? server_sockfd : STDIN_FILENO;

        // Se houver um cliente ativo conversando, adicionamos o socket dele na escuta também
        if (ativo_sockfd != -1) {
            FD_SET(ativo_sockfd, &read_fds);
            if (ativo_sockfd > max_fd) max_fd = ativo_sockfd;
        }

        // Bloqueia a execução aqui até que o teclado seja tocado OU a rede receba um sinal
        if (select(max_fd + 1, &read_fds, NULL, NULL, NULL) < 0) {
            perror("Erro no select");
            break;
        }

        // ---------------------------------------------------------------------
        // CANAL 1: Ação vinda do Teclado do Servidor (Comando Administrativo)
        // ---------------------------------------------------------------------
        if (FD_ISSET(STDIN_FILENO, &read_fds)) {
            char comando[50];
            if (fgets(comando, sizeof(comando), stdin) != NULL) {
                comando[strcspn(comando, "\n")] = '\0'; // Remove o caractere \n do final

                if (strcmp(comando, "sair") == 0) {
                    printf("\nߛѠ[SISTEMA]: Comando de desligamento recebido.\n");
                    
                    // Notifica o cliente conectado (caso exista) antes de desligar o programa
                    if (ativo_sockfd != -1) {
                        char *msg_aviso = "Servidor sendo encerrado pelo administrador.\n";
                        write(ativo_sockfd, msg_aviso, strlen(msg_aviso));
                        close(ativo_sockfd);
                    }
                    
                    rodando = 0; // Quebra o while principal
                    continue;
                }
            }
        }

        // ---------------------------------------------------------------------
        // CANAL 2: Ação vinda da Rede (Alguém tentou conectar)
        // ---------------------------------------------------------------------
        if (FD_ISSET(server_sockfd, &read_fds)) {
            struct sockaddr_in nova_address;
            socklen_t nova_len = sizeof(nova_address);
            // Captura o cliente pendente na rede criando um socket temporário para ele
            int novo_sockfd = accept(server_sockfd, (struct sockaddr *)&nova_address, &nova_len);
            
            if (novo_sockfd >= 0) {
                char novo_ip[INET_ADDRSTRLEN];
                inet_ntop(AF_INET, &nova_address.sin_addr, novo_ip, sizeof(novo_ip));

                if (ativo_sockfd == -1) {
                    // Servidor Livre: Registra o novo cliente como oficial
                    ativo_sockfd = novo_sockfd;
                    printf("ߤݠ[CONEXÃO]: Link estabelecido com o cliente [%s].\n", novo_ip);
                    
                    // Envia o byte de Handshake 'Y' (Yes) para liberar a digitação no terminal do cliente
                    char status_ok = 'Y';
                    write(ativo_sockfd, &status_ok, 1);
                } else {
                    // Servidor Ocupado: Dá accept no intruso e executa o close imediatamente
                    // Isso derruba a conexão extra sem congelar o terminal de quem tentou entrar
                    close(novo_sockfd); 
                    printf("⚠️  [ALERTA]: Tentativa de intrusão detectada vinda do IP [%s]!\n", novo_ip);
                    printf("             A conexão foi barrada (Servidor Ocupado).\n");
                }
                fflush(stdout);
            }
        }

        // ---------------------------------------------------------------------
        // CANAL 3: Ação vinda do Cliente Ativo (Digitou algo ou desconectou)
        // ---------------------------------------------------------------------
        if (ativo_sockfd != -1 && FD_ISSET(ativo_sockfd, &read_fds)) {
            char ch;
            int bytes_lidos = read(ativo_sockfd, &ch, 1);

            if (bytes_lidos <= 0) {
                // Se retornou 0 ou menor, significa que o cliente fechou a janela ou caiu
                printf("ߔ̠[DESCONEXÃO]: O cliente encerrou a sessão de forma abrupta.\n");
                printf("⏳ Aguardando novas conexões na rede...\n\n");
                close(ativo_sockfd);
                ativo_sockfd = -1; // Libera a vaga do servidor para o próximo cliente
            } else {
                printf("ߓŠ[DADO] Recebido: '%c'", ch);

                if (toupper((unsigned char)ch) == '.') {
                    ch = '.';
                    printf(" -> Token '.' detectado. Fechando canal.\n");
                    printf("⏳ Aguardando novas conexões na rede...\n\n");
                    
                    // Retorna o ponto, fecha a conexão e limpa a vaga do servidor
                    write(ativo_sockfd, &ch, 1);
                    close(ativo_sockfd);
                    ativo_sockfd = -1; 
                } else {
                    ch++; // Regra principal do projeto: desloca o caractere em +1 (Cifra básica)
                    printf(" -> Processado para: '%c' (Enviando de volta)\n", ch);
                    write(ativo_sockfd, &ch, 1); // Devolve o caractere modificado
                }
            }
            fflush(stdout);
        }
    }

    // Finalização limpa e encerramento do processo administrativo
    printf("ߚʠ[SISTEMA]: Recursos liberados. Aplicação finalizada com sucesso.\n");
    close(server_sockfd);
    return 0;
}