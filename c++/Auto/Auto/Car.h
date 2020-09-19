#pragma once
#include <iostream>
#include "restclient-cpp/restclient.h"
#include "restclient-cpp/connection.h"
#include "json/json.h"
using namespace std;
Json::Value json_parse(RestClient::Response r);
class Car
{  
    private:
        RestClient::Connection* conn;
        void runStreet(string address, string accessToken); //connessione con la strada
        tuple<string,string> richiestaAccess(string destinazione);
        void sendInfo(); //comunico la mia posizone e current_speed e la targa alla strada
        void changeSpeed(string action);
    public:
        double current_speed;
        double speed_max;
        double position;
        string code;

        Car(double speed_max, string code) {  // Constructor
            this->current_speed = 0;
            this->speed_max = speed_max;
            this->position = 0;
            this->code = code;
        }
        
        Json::Value getDestinations(string address);//connessione PA,chiedo le destinazioni 
        void goToDestination(Json::Value street_list, int destination);
  
};

