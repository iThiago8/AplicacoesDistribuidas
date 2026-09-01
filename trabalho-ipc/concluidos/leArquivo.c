#include <stdio.h>
#include <stdlib.h>

int main() {
	FILE *arquivo;
	char caractere;

	printf("Abrindo o arquivo 'OlaMundo.txt' em modo de leitura...\n\n");
	arquivo = fopen("OlaMundo.txt", "rt"); /* abre o arquivo de texto para leitura */

	if(arquivo == NULL) {
		printf("Erro abrindo arquivo\n");
		exit(1);
	} else {
		printf("Lendo o arquivo e exibindo seu conteúdo...\n\n");
		while((caractere = getc(arquivo)) != EOF) {
			printf("%c", caractere);
		}
	}

	printf("\nFechando o arquivo...\n");
	fclose(arquivo);

	return 0;
}