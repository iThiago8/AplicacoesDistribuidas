package com.exemplo.pedidos.grpc;

import io.grpc.Server;
import io.grpc.ServerBuilder;
import io.grpc.Status;
import io.grpc.stub.StreamObserver;
import java.io.IOException;
import java.util.Map;
import java.util.concurrent.TimeUnit;

public class ServidorPedido {
    public static void main(String[] args) throws IOException, InterruptedException {
        int porta = args.length > 0 ? Integer.parseInt(args[0]) : 50051;
        Server servidor = ServerBuilder.forPort(porta)
                .addService(new ServicoPedidos()).build().start();
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            servidor.shutdown();
            try {
                if (!servidor.awaitTermination(5, TimeUnit.SECONDS)) {
                    servidor.shutdownNow();
                }
            } catch (InterruptedException erro) {
                servidor.shutdownNow();
                Thread.currentThread().interrupt();
            }
        }));
        System.out.println("Servidor gRPC ativo na porta " + porta + ".");
        servidor.awaitTermination();
    }

    static class ServicoPedidos extends PedidoServiceGrpc.PedidoServiceImplBase {
        private final Map<String, Pedido> pedidos = Map.of(
                "PED-1001", Pedido.newBuilder()
                        .setNumero("PED-1001").setCliente("Ana Souza")
                        .setStatus("Em separação").setValorTotal(159.90).build(),
                "PED-1002", Pedido.newBuilder()
                        .setNumero("PED-1002").setCliente("Carlos Lima")
                        .setStatus("Enviado").setValorTotal(89.50).build());

        @Override
        public void consultarPedido(ConsultarPedidoRequest requisicao, StreamObserver<Pedido> resposta) {
            String numero = requisicao.getNumeroPedido();
            Pedido pedido = pedidos.get(numero);
            if (pedido == null) {
                resposta.onError(Status.NOT_FOUND
                        .withDescription("Pedido " + numero + " não encontrado.")
                        .asRuntimeException());
                return;
            }
            resposta.onNext(pedido);
            resposta.onCompleted();
        }
    }
}
