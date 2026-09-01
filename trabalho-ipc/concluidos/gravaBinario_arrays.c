#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_PESSOAS 3

typedef struct pessoa {
    int codigo;
    char nome[40];
    int idade;
    float salario;
} t_pessoa;

// Função alterada para receber o array e a quantidade de elementos
void gravar(t_pessoa lista[], int tamanho) {
    FILE *arq;

    arq = fopen("cadastro_binario_arrays.bin", "wb");
    if (arq == NULL) {
        printf("\nErro ao abrir arquivo para gravação!");
        return;
    }

    for (int i = 0; i < tamanho; i++) {
        printf("%d - %s - %d - R$ %.2f\n", lista[i].codigo,
                                           lista[i].nome,
                                           lista[i].idade,
                                           lista[i].salario);

        // Grava a estrutura atual no arquivo
        fwrite(&lista[i], sizeof(t_pessoa), 1, arq);
    }

    fclose(arq);
    printf("\nDados gravados com sucesso!\n");
}

int main() {    
    t_pessoa agenda[MAX_PESSOAS];		// Criação do array de estruturas

    // Preenchimento dos dados no array
    agenda[0].codigo = 1;
    agenda[0].idade = 42;
    agenda[0].salario = 1000.5;
    strcpy(agenda[0].nome, "ze da silva");

    agenda[1].codigo = 2;
    agenda[1].idade = 18;
    agenda[1].salario = 2000.5;
    strcpy(agenda[1].nome, "maria da silva");

    agenda[2].codigo = 3;
    agenda[2].idade = 20;
    agenda[2].salario = 3000.5;
    strcpy(agenda[2].nome, "joao da silva");

    // Chama a função passando o array e o tamanho dele
    gravar(agenda, MAX_PESSOAS);

    return 0;
}