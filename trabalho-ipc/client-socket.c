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

#define PORT 3490

// Função auxiliar para interpretar de forma elegante o motivo do erro
void exibir_erro_conexao(int bytes_lidos, char status_servidor) {
    printf("\n=======================================================\n");
    if (bytes_lidos == 0) {
        printf(" ❌ CONEXÃO RECUSADA: O servidor rejeitou a chamada.\n");
        printf(" Motivo: O servidor está ocupado tratando outro cliente.\n");
        printf(" Sugestão: Aguarde alguns instantes e tente novamente.\n");
    } else if (bytes_lidos < 0) {
        printf(" ⚠️ ERRO DE REDE: Falha crítica na comunicação inicial.\n");
        printf(" Motivo: Instabilidade no link ou queda do socket remoto.\n");
    } else if (status_servidor != 'Y') {
        printf(" ߛo؏ PROTOCOLO INVÁLIDO: Resposta desconhecida do host.\n");
        printf(" Motivo: O servidor remoto não pertence a esta aplicação IPC.\n");
    }
    printf("=======================================================\n\n");
}

int main(int argc, char *argv[]) {
    int client_sockfd;
    struct sockaddr_in server_address;
    char ch, resposta_ch;

    // Buffers para resolução de nome/IP
    struct addrinfo hints, *res;

    // 1. Valida se o IP ou Hostname do servidor foi passado como argumento
    if (argc != 2) {
        printf("Uso correto: %s <ip_ou_hostname_do_servidor>\n", argv[0]);
        printf("Exemplo: %s 192.168.0.38\n", argv[0]);
        printf("Exemplo: %s udesc-lts-virtual-machine\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    // 2. Configura os critérios para buscar o endereço (aceita IP ou Hostname)
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_INET;       // Força IPv4 para compatibilidade
    hints.ai_socktype = SOCK_STREAM; // TCP

    // 3. Resolve o nome do servidor (converte hostname ou string de IP em dados de rede)
    printf("ߔ͠Resolvendo endereço de '%s'...\n", argv[1]);
    if (getaddrinfo(argv[1], NULL, &hints, &res) != 0) {
        printf("❌ Erro: Não foi possível resolver o endereço '%s'.\n", argv[1]);
        exit(EXIT_FAILURE);
    }

    // 4. Cria o socket IP v4 / TCP do cliente
    client_sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (client_sockfd < 0) {
        perror("Erro ao criar o socket do cliente");
        freeaddrinfo(res);
        exit(EXIT_FAILURE);
    }

    // 5. Copia a estrutura de endereço resolvida para a configuração do servidor
    struct sockaddr_in *ipv4 = (struct sockaddr_in *)res->ai_addr;
    memset(&server_address, 0, sizeof(server_address));
    server_address.sin_family = AF_INET;
    server_address.sin_port = htons(PORT);
    server_address.sin_addr = ipv4->sin_addr;

    freeaddrinfo(res); // Libera a memória alocada pelo getaddrinfo após copiar o IP

    // Exibe o IP final que o cliente vai tentar se conectar (para fins de teste)
    char ip_resolvido[INET_ADDRSTRLEN];
    inet_ntop(AF_INET, &server_address.sin_addr, ip_resolvido, sizeof(ip_resolvido));
    printf("ߌРTentando conectar ao servidor no IP [%s]...\n", ip_resolvido);

    // 6. Executa a conexão física de rede (Three-Way Handshake TCP)
    if (connect(client_sockfd, (struct sockaddr *)&server_address, sizeof(server_address)) < 0) {
        printf("\n❌ Falha física de conexão. O servidor está offline ou a porta %d está fechada.\n\n", PORT);
        close(client_sockfd);
        exit(EXIT_FAILURE);
    }

    // Mecanismo de handshake de validação (otimização para servidor ocupado)
    char status_servidor = '\0';
    // Aguarda o byte de autorização enviado pelo servidor ('Y')
    int bytes_lidos = read(client_sockfd, &status_servidor, 1);

    // Se o canal fechou imediatamente (bytes_lidos <= 0) ou o caractere não for 'Y'
    if (bytes_lidos <= 0 || status_servidor != 'Y') {
        exibir_erro_conexao(bytes_lidos, status_servidor);
        close(client_sockfd);
        return 0; // Finaliza a aplicação de forma limpa e educada
    }

    // Se passou do teste anterior, a conexão foi aceita de fato pelo servidor!
    printf("ߚ [STATUS]: Conectado com sucesso e homologado pelo servidor!\n\n");

    // Loop principal de comunicação
    while (1) {
        printf("ߑɠDigite um caractere e tecle <Enter> (. para sair): ");
        fflush(stdout);
        
        // Lê o caractere digitado pelo usuário no terminal do cliente
        if (scanf(" %c", &ch) != 1) {
            break;
        }

        printf("Caractere enviado = %c\n", ch);
        
        // Envia o caractere de 1 byte para o servidor processar
        if (write(client_sockfd, &ch, 1) <= 0) {
            printf("❌ Erro: A conexão com o servidor foi interrompida.\n"); break;
        }

        // Aguarda e lê o caractere de resposta retornado pelo servidor
        if (read(client_sockfd, &resposta_ch, 1) <= 0) {
            printf("ߓɠConexão fechada pelo servidor remoto.\n"); break;
        }

        // Avalia se o comando digitado foi o token de encerramento (.)
        if (ch == '.') {
            printf("ߑˠSessão finalizada com sucesso por comando do usuário.\n"); break;
        }

        printf("ߓŠCaractere retornado do servidor = %c\n\n", resposta_ch);
    }

    // 7. Fecha o socket do cliente de forma segura antes de sair
    close(client_sockfd);
    return 0;
}  