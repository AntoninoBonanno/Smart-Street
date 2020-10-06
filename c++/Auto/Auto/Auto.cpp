#include <iostream>
#include "json/json.h"
#include "Car.h"
#include <regex>

using namespace std;

int main(int argc, char* argv[])
{
    string targa, hostPA;
    int speed_max;
    Json::Value streets;
    int destinazione = 0;
    
    cout << "Inserisci targa: ";
    cin >> targa;
    cout << "Inserisci speed_max [km/h]: ";
    cin >> speed_max;

    Car macchina(speed_max, targa); //istanza della classe Car

    cout << "Inserisci indirizzo punto d'accesso: ";
    cin >> hostPA;

    regex r("(^http?://(www.)?)"); 
    hostPA = regex_replace(hostPA, r, ""); 

    streets=macchina.getDestinations(hostPA); //Recupero le possibili destinazioni, contattando il Punto d'accesso
    
    do {
        cout << "Scegli la tua destinazione[id]" << endl;
        cin >> destinazione;
    } while (destinazione == 0 || destinazione >streets.size());

    macchina.goToDestination(to_string(destinazione)); //Seleziono la destinazione e inizio il mio percorso

    system("PAUSE");
}





