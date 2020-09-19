#include <iostream>
#include "restclient-cpp/restclient.h"
#include "restclient-cpp/connection.h"
#include "json/json.h"
#include "Car.h"
using namespace std;

int main(int argc, char* argv[])
{
    Car macchina(2,"EZ769FY");
    int x = 0;
    Json::Value streets;
    streets=macchina.getDestinations("127.0.0.1:5000");
    do {
        cout << "Scegli la tua destinazione[id]" << endl;
        cin >> x;
    } while (x == 0);
    x = --x;
    macchina.goToDestination(streets,x);
   
    

}


Json::Value json_parse(RestClient::Response r) {
    //per fare il parse
    string errors;
    Json::Value root;
    Json::CharReaderBuilder builder;
    Json::CharReader* reader = builder.newCharReader();

    bool parsingSuccessful = reader->parse(r.body.c_str(), r.body.c_str() + r.body.size(), &root, &errors);
    delete reader;

    if (!parsingSuccessful)
    {
        cout << r.body << endl;
        cout << errors << endl;
    }

    return root;
}


