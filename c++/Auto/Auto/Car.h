#pragma once
#include <iostream>
#include "restclient-cpp/restclient.h"
#include "restclient-cpp/connection.h"
#include "json/json.h"
using namespace std;
class Car
{  
    private:
        RestClient::Connection* conn;
        int current_speed;
        double position;

        void runStreet(string host, string port, string accessToken); 
        tuple<string,string,string> requestAccess(string destinazione);        
        void doAction(Json::Value action, int start, double position_server);
        Json::Value jsonParse(string r);
    public:
        int speed_max;
        string code;

        Car(int speed_max, string code) {  // Constructor
            this->current_speed = 0;
            this->speed_max = speed_max;
            this->position = 0;
            this->code = code;
        }
        
        Json::Value getDestinations(string address);
        void goToDestination(string destination);
  
};

