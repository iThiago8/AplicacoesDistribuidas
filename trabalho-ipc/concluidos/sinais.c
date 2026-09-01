#include <stdio.h>     /* funções de E/S padrão                               */
#include <unistd.h>    /* funções padrão unix, como getpid()                  */
#include <sys/types.h> /* várias definições de tipos, como pid_t              */
#include <signal.h>    /* macros com nome de sinais e o protótipo de signal() */

void trata_int1(int);
void trata_int2(int);

/* para começar, eis aqui o manipulador de sinal */
void trata_int1(int sig_num) {
    /* redefina o manipulador de sinal novamente para trata_int, para a próxima vez */
    signal(SIGINT, trata_int2);

    /* e imprima a mensagem */
    printf("Não faça isso\n");
    fflush(stdout);
}

/*  outro manipulador de sinal */
void trata_int2(int sig_num) {
    /* redefine para o primeiro manipulador */
    signal(SIGINT, trata_int1);

    /* e imprime a mensagem */
    printf("Não adianta pressionar Ctrl-C, você não entendeu ainda?\n");
    fflush(stdout);
}

int main() {
	/* define o manipulador de sinal INT (Ctrl-C) para 'trata_int' */
	signal(SIGINT, trata_int1);

	/* agora, vamos entrar em um laço infinito que não faz nada */
	for ( ;; ) pause();
}