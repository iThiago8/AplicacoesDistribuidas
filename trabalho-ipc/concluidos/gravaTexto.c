#include <stdio.h>

int main() {
  FILE *arquivo; /* declara um ponteiro para um tipo FILE */

  printf("Criando o arquivo 'OlaMundo.txt'...\n\n");
  arquivo = fopen("OlaMundo.txt", "wt"); /* cria um arquivo de texto */

  if(arquivo == NULL) {
    printf("Erro: não consigo criar o arquivo 'OlaMundo.txt'.\n");

    return -1;
  } else {
    printf("Arquivo 'OlaMundo.txt' criado com sucesso!\n\n");

    printf("Gravando a mensagem 'Aula na Unoesc!' no arquivo\n\n");
    fprintf(arquivo, "Aula na Unoesc!\n");

    printf("Fechando o arquivo...\n\n");
    fclose(arquivo);

    return 0;
  }
}