<?php
declare(strict_types=1);
require __DIR__ . '/cliente-http.php';

function consultarPedidoGraphQL(string $numeroPedido, array $campos): ?array
{
    $permitidos = ['numero', 'cliente', 'status', 'valorTotal'];
    if ($campos === [] || array_diff($campos, $permitidos) !== []) {
        throw new InvalidArgumentException('Informe campos válidos para a consulta.');
    }
    $selecao = implode(' ', array_unique($campos));
    $consulta = 'query ConsultarPedido($numeroPedido: String!) {'
        . ' pedido(numeroPedido: $numeroPedido) { ' . $selecao . ' } }';
    return executarGraphQL($consulta, ['numeroPedido' => $numeroPedido])['pedido'];
}

try {
    foreach ([
        'Consulta completa' => ['numero', 'cliente', 'status', 'valorTotal'],
        'Consulta resumida' => ['numero', 'status'],
    ] as $descricao => $campos) {
        echo PHP_EOL . "=== {$descricao} ===" . PHP_EOL;
        imprimirPedido(consultarPedidoGraphQL($argv[1] ?? 'PED-1001', $campos));
    }
} catch (Throwable $erro) {
    fwrite(STDERR, 'Erro: ' . $erro->getMessage() . PHP_EOL);
    exit(1);
}
