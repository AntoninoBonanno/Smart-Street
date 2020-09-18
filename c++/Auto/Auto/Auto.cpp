#include <iostream>
#include "restclient-cpp/restclient.h"
#include "restclient-cpp/connection.h"
#include "json/json.h"
using namespace std;
Json::Value json_parse(RestClient::Response r);

class Car {
private:
    RestClient::Connection* conn;
public:
    double current_speed;
    double speed_max;
    double position;
    string code;
   
    Car(double speed_max, string code) {     // Constructor
        this->current_speed = 0;
        this->speed_max = speed_max;
        this->position = 0;
        this->code = code;
    }

    void connetti(string address);
    Json::Value requestPA(string address);//connessione PA,chiedo le destinazioni, decido la destinazione  
    tuple<string, string> selectDestination(Json::Value StreetList);
    void requestStreet(string address, string accessToken); //connessione con la strada
    void sendInfo(); //comunico la mia posizone e current_speed alla strada
    void changeSpeed();

};


void Car::connetti(string address) {
    RestClient::init();// initialize RestClient
    conn = new RestClient::Connection(address);
    // set headers
    RestClient::HeaderFields headers;
    headers["Accept"] = "application/json";
    conn->SetHeaders(headers);
    cout << "Mi sono connesso al: " + address << endl;
}

Json::Value Car::requestPA(string address) {
    //connessione PA,chiedo le destinazioni, decido la destinazione  
    connetti(address);
    //get
    RestClient::Response request = conn->get("/");
    if (request.code != 200) {
        cout << "Errore nella richiesta di get" << endl;
        cout << request.code << endl;
        cout << request.body << endl;
        RestClient::disable();
        exit(0);
    }

    const Json::Value response = json_parse(request);
    const Json::Value streets = response["streets"];

    /*for (int index = 0; index < streets.size(); ++index) //per stampare
    {
        //cout << mynames[index] << endl;
        cout << streets[index]["id"];
        cout << streets[index]["name"] << endl;
    }*/

    
    return streets;
}

tuple<string, string> Car::selectDestination(Json::Value StreetList) {
    int x=0;   
    cout << StreetList << endl;
    do {
        cout << "Scegli la tua destinazione[id]" << endl;        
        cin >> x;
    } while (x == 0); 
    x = --x;
    cout << "Hai scelto la strada: " << StreetList[x] << endl;

    //post con targa e destinazione(id della street) 
    Json::StreamWriterBuilder writer;
    Json::Value xPost;
    xPost["destinazione"] = StreetList[x]["id"];
    xPost["targa"] = code;

    string json_post = Json::writeString(writer, xPost);
    cout << "questa e la richiesta post fatta "<<endl << json_post << endl;

  
    RestClient::Response post = conn->post("/", json_post);
    if (post.code != 200) {
        cout << "Errore nella richiesta di post" << endl;
        cout << post.code << endl;
        cout << post.body << endl;
        RestClient::disable();
        exit(0);
    }


    cout << "questa e la risposta della post " << post.body << endl;
    RestClient::disable();
    Json::Value response = json_parse(post); //faccio il parse
    cout << response["message"] << endl;
    string address = response["address"].asString();  //mi restituisce l'address (indirizzo ip della strada destinazione) e l'access token
    string access_token = response["access_token"].asString();
    return { address, access_token };
}

void Car::requestStreet(string address,string accessToken) {
    connetti(address);

    RestClient::Response request = conn->post("/", "{\"accessToken\":\""+ accessToken +"\"}");
    if (request.code != 200) {
        cout << "Errore nella richiesta di get" << endl;
        cout << request.code << endl;
        cout << request.body << endl;
        RestClient::disable();
        exit(0);
    }


    RestClient::disable();
}

int main(int argc, char* argv[])
{
    Car macchina(2,"EZ769FY");
    string address, access_token;
    Json::Value streets;
    //streets = macchina.requestPA("93.37.178.159:5000");
    streets = macchina.requestPA("127.0.0.1:5000");
    tie(address, access_token)=macchina.selectDestination(streets);
    cout << address;
    cout << access_token;
    macchina.requestStreet(address, access_token);

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


