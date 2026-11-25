<?php
declare(strict_types=1);
require __DIR__ . '/cliente-http.php';

$consulta = <<<'GRAPHQL'
mutation AtualizarStatusPedido($numeroPedido: String!, $novoStatus: String!) {
    atualizarStatusPedido(numeroPedido: $numeroPedido, novoStatus: $novoStatus) {
        numero cliente status valorTotal
    }
}
GRAPHQL;
try {
    $dados = executarGraphQL($consulta, [
        'numeroPedido' => $argv[1] ?? 'PED-1001',
        'novoStatus' => $argv[2] ?? 'Em transporte',
    ]);
    imprimirPedido($dados['atualizarStatusPedido']);
} catch (Throwable $erro) {
    fwrite(STDERR, 'Erro: ' . $erro->getMessage() . PHP_EOL);
    exit(1);
}
