#include <iostream>
#include "restclient-cpp/restclient.h"
#include "restclient-cpp/connection.h"
#include "json/json.h"
using namespace std;
class Car {
    private:
        RestClient::Connection* conn; 
    public:
        double current_speed;
        double speed_max;
        double position;
        string targa;
        Car(double a, double b, double c,string d) {     // Constructor
            current_speed = a;
            speed_max = b;
            position = c;
            targa = d;

        }
        void connetti(string indirizzo);
        Json::Value requestPA(string indirizzo);//connessione PA,chiedo le destinazioni, decido la destinazione  
        void requestStreet(/*indirizzo ip della street*/); //connessione con la strada
        void sendInfo(); //comunico la mia posizone e current_speed alla strada
        void changeSpeed();

};

void Car::connetti(string indirizzo) {
    RestClient::init();// initialize RestClient
    conn = new RestClient::Connection(indirizzo);
    // set headers
    RestClient::HeaderFields headers;
    headers["Accept"] = "application/json";
    conn->SetHeaders(headers);
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

Json::Value Car::requestPA(string indirizzo) {
    //connessione PA,chiedo le destinazioni, decido la destinazione  
    connetti(indirizzo);
    //get
    RestClient::Response request = conn->get("/");
    if (request.code != 200) {
        cout << "Errore nella richiesta di get"<<endl;
        cout << request.code << endl;
        cout << request.body << endl;
        RestClient::disable();
        exit(0);
    }

    const Json::Value response = json_parse(request);
    const Json::Value streets = response["streets"];

    for (int index = 0; index < streets.size(); ++index)
    {
        //cout << mynames[index] << endl;
        cout << streets[index]["id"];
        cout << streets[index]["name"] << endl;
    }

    RestClient::disable();
    return streets;
}



int main(int argc, char* argv[])
{
    Car macchina(1, 2, 3,"ciao");
    Json::Value streets;
    streets = macchina.requestPA("127.0.0.1:5000");
    cout << streets << endl;


    cout << "Scegli la destinazione" << endl;
    //sceglie

    /*
    //vai qua
    //post
    Json::StreamWriterBuilder builder2;
    Json::Value xPost;
    xPost["targa"] = macchina.targa;
    xPost["destinazione"] = streets[0]["id"];
    string json_post = Json::writeString(builder2, xPost);
    cout << json_post;

    RestClient::Response post = conn->post("/", json_post);
    if (post.code != 200) {
        cout << "Errore nella richiesta di post" << endl;
        cout << post.code << endl;
        cout << post.body << endl;
        RestClient::disable();
        exit(0);
    }


    cout << post.body << endl;*/

    //post con targa e destinazione(id della street) 
    //mi restituisce l'address (indirizzo ip della strada destinazione) e l'access token
}




