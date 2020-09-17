#include <iostream>
#include "restclient-cpp/restclient.h"
#include "restclient-cpp/connection.h"
#include "json/json.h"
class Car {
    public:
        double current_speed;
        double speed_max;
        double position;

        string requestPA (string ip_address) {
            //connessione PA,chiedo le destinazioni, decido la destinazione  
            // initialize RestClient
            RestClient::init();

            // get a connection object
            RestClient::Connection* conn = new RestClient::Connection(ip_address);
            // set headers
            RestClient::HeaderFields headers;
            headers["Accept"] = "application/json";
            conn->SetHeaders(headers);


            RestClient::Response r = conn->get("/");
            if (r.code != 200) {
                //cout << "Errore nella richiesta di get";
                RestClient::disable();
                exit(0);
            }

            RestClient::disable();
            return r.body;
        }

        void requestStreet(/*indirizzo ip della street*/) {
            //connessione con la strada 
        }
        void sendInfo() {
            //comunico la mia posizone e current_speed alla strada
        }
        void changeSpeed() {

        }

};
using namespace std;
int main(int argc, char* argv[])
{
    Car macchina;
    string streets;
    streets=macchina.requestPA("127.0.0.1:5000");
    
    cout << streets;
 
    //per fare il parse
    string errors;
    Json::Value root;
    Json::CharReaderBuilder builder;
    Json::CharReader* reader = builder.newCharReader();

    bool parsingSuccessful = reader->parse(streets.c_str(), streets.c_str() + streets.size(), &root, &errors);
    delete reader;

    if (!parsingSuccessful)
    {
        cout << streets << endl;
        cout << errors << endl;
    }

    const Json::Value mynames = root["streets"];

    for (int index = 0; index < mynames.size(); ++index)
    {
        //cout << mynames[index] << endl;
        cout << mynames[index]["id"] ;
        cout << mynames[index]["name"] << endl;
    }


   
    RestClient::disable();

}