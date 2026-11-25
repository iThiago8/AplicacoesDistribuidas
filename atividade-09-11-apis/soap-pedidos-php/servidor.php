<?php
// O WSDL descreve o contrato; esta classe implementa a consulta.
class PedidoDTO
{
    public $numero;
    public $cliente;
    public $status;
    public $valorTotal;
}

class PedidoSoapService
{
    private $pedidos = [
        'PED-1001' => ['numero' => 'PED-1001', 'cliente' => 'Ana Souza',
            'status' => 'Em separação', 'valorTotal' => '159.90'],
        'PED-1002' => ['numero' => 'PED-1002', 'cliente' => 'Carlos Lima',
            'status' => 'Enviado', 'valorTotal' => '89.50'],
    ];

    public function consultarPedido($numeroPedido)
    {
        if (!isset($this->pedidos[$numeroPedido])) {
            throw new SoapFault('Client', "Pedido {$numeroPedido} não encontrado.");
        }
        $pedido = new PedidoDTO();
        foreach ($this->pedidos[$numeroPedido] as $campo => $valor) {
            $pedido->$campo = $valor;
        }
        return $pedido;
    }
}

$servidor = new SoapServer(__DIR__ . '/pedido.wsdl', [
    'classmap' => ['Pedido' => PedidoDTO::class],
    'cache_wsdl' => WSDL_CACHE_NONE,
]);
$servidor->setClass(PedidoSoapService::class);
$servidor->handle();
