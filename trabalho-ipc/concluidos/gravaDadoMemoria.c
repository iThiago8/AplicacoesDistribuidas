#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/ipc.h>
#include <sys/shm.h>

#define SHM_SIZE 1024      // 1KB de memória compartilhada

int main(int argc, char *argv[]) {
	key_t key;
	int shmid;
	char *data;
	int mode;

	if(argc > 2) {
		fprintf(stderr, "uso: gravaDadoMemoria [dado_a_escrever]\n");
		exit(1);
	} else {
		printf("Processo: %d\n", getpid());
	}

	// cria a chave ("key")
	if((key=ftok("gravaDadoMemoria", 'R')) == -1) {
		perror("ftok");
		exit(1);
	}

	printf("senha: %ld\n", key);

	// conecta e cria o segmento
	if((shmid=shmget(key, SHM_SIZE, 0644|IPC_CREAT)) == -1) {
		perror("shmget");
		exit(1);
	}

	// anexa ao segmento para definir um ponteiro para ele
	data=shmat(shmid, (void *)0, 0);
	if(data == (char *)(-1)) {
		perror("shmat");
		exit(1);
	}

	// lê ou modifica o segmento, dependendo da linha de comando
	if(argc == 2) {
		printf("escrevendo no segmento: \"%s\"\n", argv[1]);
		strncpy(data, argv[1], SHM_SIZE);
	} else {
		printf("segmento contém: \"%s\"\n", data);
	}

	// desconecta do segmento
	if(shmdt(data) ==- 1) {
		perror("shmdt");
		exit(1);
	}
	return(0);
}