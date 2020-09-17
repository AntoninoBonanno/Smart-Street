#include <iostream>
#include "restclient-cpp/restclient.h"
#include "restclient-cpp/connection.h"

using namespace std;
int main(int argc, char* argv[])
{
    // initialize RestClient
    RestClient::init();

    // get a connection object
    RestClient::Connection* conn = new RestClient::Connection("127.0.0.1:5000");
    // set headers
    RestClient::HeaderFields headers;
    headers["Accept"] = "application/json";
    conn->SetHeaders(headers);


    RestClient::Response r = conn->get("/");
    if (r.code != 200) {
        cout << "Errore nella richiesta di get";
        RestClient::disable();
        exit(0);
    }
    cout << r.body;
    
    RestClient::disable();

}