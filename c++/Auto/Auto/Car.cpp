#include "Car.h"
#include <windows.h>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <stdlib.h>
#include <stdio.h>


//public
/**
* Funzione che data un indirizzo ip crea la connessione con il punto di accesso, ed effettua la get per richiedere le destinazioni
* 
* @param address: indirizzo ip del Punto di accesso
* @return streets: lista delle strade
*/
Json::Value Car::getDestinations(string address) {
    
    RestClient::init();// initialize RestClient
    conn = new RestClient::Connection(address);
    // set headers
    RestClient::HeaderFields headers;
    headers["Accept"] = "application/json";
    conn->SetHeaders(headers);
    cout << "Mi sto connettendo al: " + address << endl;

    //get
    RestClient::Response request = conn->get("/");
    if (request.code != 200) {
        cout << "Errore nella richiesta di get" << endl;
        cout << request.code << endl;
        cout << request.body << endl;
        RestClient::disable();
        exit(0);
    }

    const Json::Value response = jsonParse(request.body);
    const Json::Value streets = response["streets"];
    cout << response["message"] << endl;
    cout << streets << endl;
    return streets;
}

/**
* Funzione che data una destinazione, richiama richiestaAccess e runStreet
* 
* @param destination: destinazione che si vuole raggiungere
*/
void Car::goToDestination(string destination) {

    if (conn == NULL) throw new exception("Recupera la destinazione");   
    string host,port, access_token;
    tie(host,port, access_token) = richiestaAccess(destination);
    runStreet(host.c_str(), port.c_str(), access_token);
}

//private
/**
* Funzione che effettua la post al PA con la destinazione e la sua targa, ricevendo host, port e il token d'accesso
* 
* @param destinazione: destinazione che si vuole raggiungere
* @return host: indirizzo ip della strada da percorrere
          port: porta a cui fare la richiesta
          access_token: token per l'accesso
*/
tuple<string, string, string> Car::richiestaAccess(string destinazione) {    
    RestClient::Response post = conn->post("/", "{\"destinazione\":" + destinazione + ",\"targa\":\"" + code + "\"}");
    if (post.code != 200) {
        cout << "Errore nella richiesta di post" << endl;
        cout << post.code << endl;
        cout << post.body << endl;
        RestClient::disable();
        exit(0);
    }

    // cout << "questa e la risposta della post " << post.body << endl;
    RestClient::disable();
    Json::Value response = jsonParse(post.body); //faccio il parse
    //cout << response << endl;
    cout << response["message"] << endl;
    string host = response["host"].asString();    //mi restituisce l'address (indirizzo ip della strada destinazione) e l'access token
    string port = response["port"].asString();
    string access_token = response["access_token"].asString();
    return tie(host, port, access_token);
}

/**
* Funzione che crea una connessione socket con l'host e con la porta. Invia i suoi dati e l'access token. Ricevendo un messaggio, uno status e un azione
*
* @param host: L'indirizzo ip dell'host.\n
*        port: la porta a cui fare le richieste
*        accessToken: il token per accedere           
*/
void Car::runStreet(string host, string port, string accessToken) {
    //cout << "host: " << host <<"port:" << port <<endl;
    //cout << "accessToken:" << accessToken << endl;
    struct addrinfo* result = NULL,
        * ptr = NULL,
        hints;

    WSADATA wsaData;
    // Initialize Winsock
    int iResult = WSAStartup(MAKEWORD(2, 2), &wsaData);
    if (iResult != 0) {
        cout << "WSAStartup failed with error: " << iResult << endl;
        exit(0);
    }

    ZeroMemory(&hints, sizeof(hints));
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_protocol = IPPROTO_TCP;

    // Resolve the server address and port
    iResult = getaddrinfo(host.c_str(), port.c_str(), &hints, &result);
    //iResult = getaddrinfo("192.168.217.1", "8000", &hints, &result);
    if (iResult != 0) {
        cout <<"getaddrinfo failed: "<<iResult << endl;;
        WSACleanup();
        exit(0);
    }

    SOCKET ConnectSocket = INVALID_SOCKET;
    ptr = result;
    // Create a SOCKET for connecting to server
    ConnectSocket = socket(ptr->ai_family, ptr->ai_socktype,ptr->ai_protocol);
   
    // Connect to server.
    iResult = connect(ConnectSocket, ptr->ai_addr, (int)ptr->ai_addrlen);
    if (iResult == SOCKET_ERROR) {
        closesocket(ConnectSocket);
        ConnectSocket = INVALID_SOCKET;
    }

    if (ConnectSocket == INVALID_SOCKET) {
        cout << "Unable to connect to server!" << endl;;
        freeaddrinfo(result);
        WSACleanup();
        exit(0);
    }

    // Invio un buffer con access_token e targa per richiedere l'accesso
    string sendbuf = "{\"access_token\":\"" + accessToken + "\",\"targa\":\"" + code + "\"}";
    //cout << sendbuf;
  
    iResult = send(ConnectSocket, sendbuf.c_str(), sendbuf.size(), 0);
    if (iResult == SOCKET_ERROR) {
        cout << "send failed: "<< WSAGetLastError()<< endl;;
        closesocket(ConnectSocket);
        WSACleanup();
        exit(0);
    }

    //printf("Bytes Sent: %ld\n", iResult);
    // Receive data until the server closes the connection
   
    int MAX_BUF_LENGTH = 4096;
    vector<char> rcvbuffer(MAX_BUF_LENGTH);

    
    int tempo_iniziale=clock(); //tempo in millisecondi


    while(true) {
        Sleep(1000);
        iResult = recv(ConnectSocket, &rcvbuffer[0], rcvbuffer.size(), 0);
        if (iResult > 0){
            //printf("Bytes received: %d\n", iResult);
           
            string rcv;
            rcv.clear();
            rcv.append(rcvbuffer.cbegin(), rcvbuffer.cend());            
            Json::Value response=jsonParse(rcv);
            //cout << response <<endl << endl;
            cout <<"Messaggio ricevuto: "<<response["message"]<<endl;
            //cout << response["status"]<<endl; 
            //cout <<"azione: "<< response["action"] << endl;            
            if (response["status"].asString() == "success") {
                //cout << "posizione dalla strada: " << response["position"] << endl;
               doAction(response["action"], tempo_iniziale);
                
            }
            else break;            
        }

        //invio targa/poszione/velocit�       
        string sendinfo = "{\"targa\":\"" + code + "\",\"position\":" + to_string(position) + ",\"speed\":" + to_string(current_speed) + "}";
        cout <<"Ti invio i miei dati: "<< sendinfo<<endl << endl;
        tempo_iniziale = clock();
        iResult = send(ConnectSocket, sendinfo.c_str(), sendinfo.size(), 0);
        if (iResult == SOCKET_ERROR) {
            cout << "send failed: "<< WSAGetLastError()<< endl;;
            closesocket(ConnectSocket);
            WSACleanup();
            exit(0);
        }

    }

    // shutdown the send half of the connection since no more data will be sent
    iResult = shutdown(ConnectSocket, SD_SEND);
    if (iResult == SOCKET_ERROR) {
        cout << "shutdown failed: "<< WSAGetLastError();
        closesocket(ConnectSocket);
        WSACleanup();
        exit(0);
    }
    // cleanup
    closesocket(ConnectSocket);
    WSACleanup();

}

/**
* Funzione che data un azione, modifica la sua velocit� in base l'azione
*
* @param action: Json con signal, e action
*        start: tempo inziale 
*/
void Car::doAction(Json::Value action,int start) {
    static int current_limit = speed_max; //aggiungere il limite

    //cout << "La differenza e':  " << ((clock()-start)/1000.0) << endl;
    position = ((current_speed / 3.6) * ((clock()-start)/1000.0)) + position;


    if (action.size()!= 0) {
        if (action["signal"].asString() == "speed_limit") current_limit = action["speed_limit"].asInt();
        else if (action["signal"].asString() == "stop") current_limit = speed_max;


        if (action["action"].asString() == "fermati") {
            int speed_to_stop = (action["distance"].asInt() * 10) / 3;
            if (speed_to_stop < current_speed) current_speed = speed_to_stop;            
        }
        else if (action["action"].asString() == "rallenta" && current_speed > 20) current_speed = current_speed - (rand() % 10 + 1);        
    }
    if (action.size() == 0 || (action["action"].asString()=="accelera" && action["signal"].asString()!="speed_limit")) { //devi accellerare                       
        if (current_speed> current_limit/2) current_speed = current_speed + 1;
        else current_speed = current_speed + (rand() % 10 + 1);
    }
    if (current_speed > current_limit) current_speed = current_limit;
    //calcolare la speed in base alla velocit� 
    //cout << "la posizione dovrebbe essere: " << position << endl;
    //cout << "la velocit� dovrebbe essere: " << current_speed << endl;
    
}

/**
* Funzione che effettua il parse da stringa a json
*
* @param r: stringa da convertire in json
* @return Json::Value Json convertito
*/
Json::Value Car::jsonParse(string r) {
    //per fare il parse
    string errors;
    Json::Value root;
    Json::CharReaderBuilder builder;
    Json::CharReader* reader = builder.newCharReader();

    bool parsingSuccessful = reader->parse(r.c_str(), r.c_str() + r.size(), &root, &errors);
    delete reader;

    if (!parsingSuccessful)
    {
        cout << r << endl;
        cout << errors << endl;
    }

    return root;
}