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

void gravar(t_nodo *inicio_lista) {
  FILE *arq;  
  t_nodo *atual = inicio_lista;

  arq = fopen("cadastro_binario_aloc_estatica.bin", "wb"); 
  if (arq == NULL) {
    printf("\nErro ao abrir arquivo para gravação!");
    return; 
  }

  while(atual != NULL) {
    printf("%d - %s - %d - R$ %.2f\n", atual->dados.codigo,
                                       atual->dados.nome,
                                       atual->dados.idade,
                                       atual->dados.salario);

    fwrite(&(atual->dados), sizeof(t_pessoa), 1, arq); 

    atual = atual->proximo; 
  }
  fclose(arq); 

  printf("\nDados gravados com sucesso!\n");
}

int main() {
    t_nodo ze, maria, joao;

    ze.dados.codigo = 1;
    ze.dados.idade = 42;
    ze.dados.salario = 1000.5;
    strcpy(ze.dados.nome, "ze da silva");

    maria.dados.codigo = 2;
    maria.dados.idade = 18;
    maria.dados.salario = 2000.5;
    strcpy(maria.dados.nome, "maria da silva");

    joao.dados.codigo = 3;
    joao.dados.idade = 20;
    joao.dados.salario = 3000.5;
    strcpy(joao.dados.nome, "joao da silva");

    ze.proximo = &maria;
    maria.proximo = &joao;
    joao.proximo = NULL;

    t_nodo *agenda = &ze;
    gravar(agenda);

    return 0;
}