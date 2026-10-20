package calculadora.comum;

import java.rmi.Remote;
import java.rmi.RemoteException;

// Deve estender Remote
public interface Calculadora extends Remote {
    // Todo método remoto deve lançar RemoteException
    int somar(int a, int b) throws RemoteException;
    int subtrair(int a, int b) throws RemoteException;
    int multiplicar(int a, int b) throws RemoteException;
    double dividir(int a, int b) throws RemoteException;
}
