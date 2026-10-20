package calculadora.servidor;

import calculadora.comum.Calculadora;
import java.rmi.RemoteException;
import java.rmi.server.RemoteServer;
import java.rmi.server.ServerNotActiveException;
import java.rmi.server.UnicastRemoteObject;

public class CalculadoraImpl extends UnicastRemoteObject implements Calculadora {
    public CalculadoraImpl() throws RemoteException {
        super(1099);
    }

    // Registra no console qual calculadora.cliente pediu qual operação
    private void registrarPedido(String operacao, String simbolo, int a, int b) {
        String origem;
        try {
            // Captura o IP ou Hostname do calculadora.cliente que chamou este método
            origem = RemoteServer.getClientHost();
        } catch (ServerNotActiveException e) {
            // Caso o método seja chamado localmente (fora do RMI), cai aqui
            origem = "Local";
        }
        System.out.println("[" + origem + "] Pedido de " + operacao + " recebido: " + a + " " + simbolo + " " + b);
    }

    @Override
    public int somar(int a, int b) throws RemoteException {
        registrarPedido("soma", "+", a, b);
        return a + b;
    }

    @Override
    public int subtrair(int a, int b) throws RemoteException {
        registrarPedido("subtração", "-", a, b);
        return a - b;
    }

    @Override
    public int multiplicar(int a, int b) throws RemoteException {
        registrarPedido("multiplicação", "*", a, b);
        return a * b;
    }

    @Override
    public double dividir(int a, int b) throws RemoteException {
        registrarPedido("divisão", "/", a, b);
        // A exceção é serializada e relançada no calculadora.cliente
        if (b == 0) {
            throw new ArithmeticException("Divisão por zero não é permitida");
        }
        return (double) a / b;
    }
}
