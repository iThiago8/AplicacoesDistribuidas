package calculadora.servidor;

import calculadora.comum.Calculadora; // <- Importa a interface
import java.rmi.registry.LocateRegistry;
import java.rmi.registry.Registry;

public class Servidor {
    public static void main(String[] args) {
        try {
            String ipServidor = (args.length > 0) ? args[0] : "localhost";
            System.setProperty("java.rmi.server.hostname", ipServidor);

            Registry registry = LocateRegistry.createRegistry(1099);
            Calculadora calc = new CalculadoraImpl();
            registry.rebind("ServicoCalculadora", calc);

            System.out.println("Servidor pronto no IP [" + ipServidor + "] aguardando conexões...");
        } catch (Exception e) {
            System.err.println("Erro no calculadora.servidor: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
