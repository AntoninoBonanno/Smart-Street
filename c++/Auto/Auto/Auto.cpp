#include <iostream>
#include "restclient-cpp/restclient.h"
#include "restclient-cpp/connection.h"
#include "json/json.h"
#include "Car.h"
using namespace std;

int main(int argc, char* argv[])
{
    /*cout << "Inserisci targa: ";
    cin >> argv[0];
    Car macchina(2, argv[0]);*/
    Car macchina(100,"EZ769FY");
    Json::Value streets;
    streets=macchina.getDestinations("127.0.0.1:5000");
    int x = 0;
    do {
        cout << "Scegli la tua destinazione[id]" << endl;
        cin >> x;
    } while (x == 0 || x>streets.size());
    macchina.goToDestination(to_string(x));
}





