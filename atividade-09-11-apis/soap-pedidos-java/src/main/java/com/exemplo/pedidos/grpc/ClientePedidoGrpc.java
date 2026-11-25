package com.exemplo.pedidos.grpc;

import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import io.grpc.StatusRuntimeException;
import java.util.concurrent.TimeUnit;

public class ClientePedidoGrpc {
    public static void main(String[] args) throws InterruptedException {
        String numero = args.length > 0 ? args[0] : "PED-1001";
        String host = System.getenv().getOrDefault("GRPC_HOST", "127.0.0.1");
        int porta = Integer.parseInt(System.getenv().getOrDefault("GRPC_PORT", "50051"));
        ManagedChannel canal = ManagedChannelBuilder.forAddress(host, porta).usePlaintext().build();
        int codigo = 0;
        try {
            var cliente = PedidoServiceGrpc.newBlockingStub(canal).withDeadlineAfter(10, TimeUnit.SECONDS);
            Pedido pedido = cliente.consultarPedido(
                    ConsultarPedidoRequest.newBuilder().setNumeroPedido(numero).build());
            System.out.println("Pedido recebido pelo gRPC:");
            System.out.println("Número: " + pedido.getNumero());
            System.out.println("Cliente: " + pedido.getCliente());
            System.out.println("Status: " + pedido.getStatus());
            System.out.printf("Valor total: R$ %.2f%n", pedido.getValorTotal());
        } catch (StatusRuntimeException erro) {
            System.err.println("Falha na chamada gRPC:");
            System.err.println("Código: " + erro.getStatus().getCode());
            System.err.println("Detalhe: " + erro.getStatus().getDescription());
            codigo = 1;
        } finally {
            canal.shutdownNow();
            canal.awaitTermination(5, TimeUnit.SECONDS);
        }
        if (codigo != 0) {
            System.exit(codigo);
        }
    }
}
