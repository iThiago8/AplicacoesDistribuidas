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

  arq = fopen("cadastro_binario_aloc_dinamica.bin", "wb"); 
  if (arq == NULL) {
    printf("\nErro ao abrir arquivo para gravação!");
    return; // Evita travar o programa se o arquivo não abrir
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

void liberar_lista(t_nodo *inicio_lista) {
    t_nodo *atual = inicio_lista;
    while (atual != NULL) {
        t_nodo *proximo = atual->proximo; // Salva o endereço do próximo antes de apagar o atual
        free(atual);                      // Deleta o nó atual da memória heap
        atual = proximo;                  // Avança para o próximo nó salvo
    }
}

int main() {
    t_nodo *ze = (t_nodo *) malloc(sizeof(t_nodo));
    t_nodo *maria = (t_nodo *) malloc(sizeof(t_nodo));
    t_nodo *joao = (t_nodo *) malloc(sizeof(t_nodo));

    if (ze == NULL || maria == NULL || joao == NULL) {
        printf("Erro ao alocar memória!\n");
        return 1;
    }

    // Preenchimento dos dados
    ze->dados.codigo = 1; 
    strcpy(ze->dados.nome, "ze da silva");
    ze->dados.idade = 42;
    ze->dados.salario = 1000.5;

    maria->dados.codigo = 2;
    strcpy(maria->dados.nome, "maria da silva");
    maria->dados.idade = 18;
    maria->dados.salario = 2000.5;
    
    joao->dados.codigo = 3; 
    strcpy(joao->dados.nome, "joao da silva"); 
    joao->dados.idade = 20; 
    joao->dados.salario = 3000.5;

    // Encadeamento direto (sem usar o '&')
    ze->proximo = maria;
    maria->proximo = joao;
    joao->proximo = NULL;

    t_nodo *agenda = ze;
    gravar(agenda);

    // Libera memória (obrigatório em alocação dinâmica)
    liberar_lista(agenda); 

    return 0;
}