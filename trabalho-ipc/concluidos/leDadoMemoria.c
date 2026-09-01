#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/ipc.h>
#include <sys/shm.h>

#define SHM_SIZE 1024      // 1KB de memória compartilhada

int main() {
	int shmid;
	char *data;
	long senha;

	printf("Digite a senha: ");
	scanf("%ld",&senha);

	// conecta e cria o segmento
	shmid = shmget(senha, SHM_SIZE, 0666);

	// anexa ao segmento para definir um ponteiro para ele
	data = shmat(shmid, (void *)0, 0);

	// imprime o conteúdo da memória compartilhada
	printf("segmento contém: \"%s\"\n", data);

	// desconecta do segmento
	shmdt(data);
}