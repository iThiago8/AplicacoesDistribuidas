#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct pessoa {
    int codigo;
    char nome[40];
    int idade;
    float salario;
} t_pessoa;

typedef struct nodo {
    t_pessoa dados;
    struct nodo *proximo;
} t_nodo;

// A função agora recebe o nome do arquivo como parâmetro
void carregar_e_exibir(const char *nome_arquivo) {
    FILE *arq;
    t_pessoa p; 

    // Abre o arquivo passado por parâmetro em modo de leitura binária
    arq = fopen(nome_arquivo, "rb");
    if (arq == NULL) {
        printf("Erro: Nao foi possivel abrir o arquivo '%s'!\n", nome_arquivo);
        return;
    }

    printf("\n------------------------------------------------");
    printf("\n%-15s | %-6s | %-10s", "Nome", "Idade", "Salario");
    printf("\n------------------------------------------------");

    while (fread(&p, sizeof(t_pessoa), 1, arq) == 1) {
        printf("\n%-15s | %-6d | R$ %-9.2f", p.nome, p.idade, p.salario);
    }
    printf("\n------------------------------------------------\n");

    fclose(arq);
}

int main(int argc, char *argv[])
{
    // Verifica se o usuário informou o nome do arquivo na linha de comando
    if (argc < 2) {
        printf("Erro: Nome do arquivo nao informado!\n");
        printf("Uso correto: %s <nome_do_arquivo.bin>\n", argv[0]);
        return 1; // Retorna erro
    }

    // O primeiro argumento (argv[1]) é o nome do arquivo digitado pelo usuário
    printf("\nLendo e exibindo os dados gravados no arquivo: %s\n", argv[1]);
    carregar_e_exibir(argv[1]);

    printf("\nPressione [Enter] para fechar o programa...");
    getchar(); 
    
    return 0;
}