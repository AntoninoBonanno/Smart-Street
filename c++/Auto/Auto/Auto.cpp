#include <iostream>
#include "json/json.h"
#include "Car.h"

using namespace std;

int main(int argc, char* argv[])
{
    string targa= "EZ769FY";
    int speed_max=100;
    
    cout << "Inserisci targa: ";
    cin >> targa;
    cout << "Inserisci speed_max [km/h]: ";
    cin >> speed_max;

    Car macchina(speed_max, targa);
    
    Json::Value streets;
    streets=macchina.getDestinations("127.0.0.1:5000"); //indirizzo PA
    int destinazione = 0;
    do {
        cout << "Scegli la tua destinazione[id]" << endl;
        cin >> destinazione;
    } while (destinazione == 0 || destinazione >streets.size());
    macchina.goToDestination(to_string(destinazione));
}





