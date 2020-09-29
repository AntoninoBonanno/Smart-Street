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

    //richiesta get, per richiedere le possibili destinazioni
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
    runStreet(host, port, access_token);
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
    //post con la destinazione scelta, mi restitusce un messaggio, un host, una porta e un access token
    RestClient::Response post = conn->post("/", "{\"destinazione\":" + destinazione + ",\"targa\":\"" + code + "\"}");
    if (post.code != 200) {
        cout << "Errore nella richiesta di post" << endl;
        cout << post.code << endl;
        cout << post.body << endl;
        RestClient::disable();
        exit(0);
    }

    RestClient::disable();

    Json::Value response = jsonParse(post.body); //faccio il parse
    cout << response["message"] << endl;

    return make_tuple(response["host"].asString(), response["port"].asString(), response["access_token"].asString());
    
}

/**
* Funzione che crea una connessione socket con l'host e con la porta. Invia i suoi dati e l'access token. Ricevendo un messaggio, uno status e un azione
*
* @param host: L'indirizzo ip dell'host.\n
*        port: la porta a cui fare le richieste
*        accessToken: il token per accedere           
*/
void Car::runStreet(string host, string port, string accessToken) {
    cout << "host: " << host <<"port:" << port <<endl;
    cout << "accessToken:" << accessToken << endl;
    struct addrinfo* result = NULL,
        * res = NULL,
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
    

    // imposto host, port e hints 
    iResult = getaddrinfo(host.c_str(), port.c_str(), &hints, &result);
    //iResult = getaddrinfo("192.168.217.1", "8000", &hints, &result);
    if (iResult != 0) {
        cout <<"getaddrinfo failed: "<<iResult << endl;;
        WSACleanup();
        exit(0);
    }

    SOCKET ConnectSocket = INVALID_SOCKET;
    res = result;
    // Crea una SOCKET per la connessione al server
    ConnectSocket = socket(res->ai_family, res->ai_socktype,res->ai_protocol);
   
    // connect al server.
    iResult = connect(ConnectSocket, res->ai_addr, (int)res->ai_addrlen);
    if (iResult == SOCKET_ERROR) {
        closesocket(ConnectSocket);
        ConnectSocket = INVALID_SOCKET;
    }

    if (ConnectSocket == INVALID_SOCKET) {
        cout << "Unable to connect to server!" << endl;;
        freeaddrinfo(result);
        WSACleanup();
        exit(0);
    }else cout << "Ho stabilito la connessione con " << host << ": " << port << endl;

    // Invio un buffer con access_token e targa per richiedere l'accesso
    string sendbuf = "{\"access_token\":\"" + accessToken + "\",\"targa\":\"" + code + "\"}";
    //cout << sendbuf;
    iResult = send(ConnectSocket, sendbuf.c_str(), sendbuf.size(), 0);
    if (iResult == SOCKET_ERROR) {
        cout << "send failed(1): "<< WSAGetLastError()<< endl;;
        closesocket(ConnectSocket);
        WSACleanup();
        exit(0);
    }

    //printf("Bytes Sent: %ld\n", iResult);
   
    int MAX_BUF_LENGTH = 4096;
    vector<char> rcvbuffer(MAX_BUF_LENGTH);

    int tempo_iniziale=clock(); //tempo in millisecondi
    Json::Value response;
    //inizio scambio messaggi
    while(true) {
        Sleep(50);
        iResult = recv(ConnectSocket, &rcvbuffer[0], rcvbuffer.size(), 0);
        if (iResult > 0){
            //printf("Bytes received: %d\n", iResult);
            string rcv;
            rcv.clear();
            rcv.append(rcvbuffer.cbegin(), rcvbuffer.cend());            
            response=jsonParse(rcv);
            //cout << response <<endl << endl;
            cout <<"Messaggio ricevuto: "<<response["message"]<<endl;
            //cout << response["status"]<<endl; 
            //cout <<"azione: "<< response["action"] << endl;  

            if (response["status"].asString() == "success") {
                
                //cout << "posizione dalla strada: " << response["position"] << endl;
                doAction(response["action"], tempo_iniziale, response["position"].asDouble());

                //se ho finito la strada corrente, chiudo la connessione e proseguo per la successiva
               if (response["action"]["action"].asString() == "next" || response["action"]["action"].asString() == "end") break;
               //se ho raggiunto la destinazione ho finito
               tempo_iniziale = clock();
            }
            else break;            
        }
        

        //invio targa/poszione/velocit�       
        string sendinfo = "{\"targa\":\"" + code + "\",\"position\":" + to_string(position) + ",\"speed\":" + to_string(current_speed) + "}";
        cout <<"Ti invio i miei dati: "<< sendinfo<<endl << endl;
        
        iResult = send(ConnectSocket, sendinfo.c_str(), sendinfo.size(), 0);
        if (iResult == SOCKET_ERROR) {
            cout << "send failed(2): "<< WSAGetLastError()<< endl;;
            closesocket(ConnectSocket);
            WSACleanup();
            exit(0);
        }

    }


    // chiudo la connessione al server
    iResult = shutdown(ConnectSocket, SD_SEND);
    if (iResult == SOCKET_ERROR) {
        cout << "shutdown failed: "<< WSAGetLastError();
        closesocket(ConnectSocket);
        WSACleanup();
        exit(0);
    }else cout << "Ho chiuso la connessione con " << host<<": "<< port << endl;
    closesocket(ConnectSocket);
    WSACleanup();
    
    // richiamo la funzione, per percorrere la nuova strada. 
    if (response["action"]["action"].asString() == "next" && response["action"]["host"].asString() != "" && response["action"]["port"].asString() != "")
        runStreet(response["action"]["host"].asString(), response["action"]["port"].asString(), response["action"]["access_token"].asString()); //potrebbe andare in overflow
}

/**
* Funzione che data un azione, modifica la sua velocit� in base l'azione
*
* @param action: Json con signal, e action
*        start: tempo inziale 
*/
void Car::doAction(Json::Value action,int start,double position_server) {
    static int current_limit = speed_max; 
    
    //cout << "La differenza e':  " << ((clock()-start)/1000.0) << endl;
    position = ((current_speed / 3.6) * ((clock()-start)/1000.0)) + position;
    //cout << "mia posizione: " << position<<endl;
    //if (position_server > position) position = position_server; 

    if (action.size()!= 0) { //
        if (action["signal"].asString() == "speed_limit") current_limit = action["speed_limit"].asInt();
        else if (action["signal"].asString() == "stop") current_limit = speed_max;


        if (action["action"].asString() == "fermati") {
            int speed_to_stop = (action["distance"].asInt() * 10) / 3;
            if (speed_to_stop < current_speed) current_speed = speed_to_stop; //da sistemare, perch� cosi non scendo mai allo 0           
        }
        else if (action["action"].asString() == "rallenta" && current_speed > 20) current_speed = current_speed - (rand() % 10 + 1);        
    }
    if (action.size() == 0 || (action["action"].asString()=="accelera")) { //In questi casi si deve accelerare                      
        if (current_speed> current_limit/2) current_speed = current_speed + 2;
        else current_speed = current_speed + (rand() % 10 + 1);
        if (current_speed > current_limit) current_speed = current_limit;
    }
    
}

/**
* Funzione che effettua il parse da stringa a json
*
* @param r: stringa da convertire in json
* @return Json::Value Json convertito
*/
Json::Value Car::jsonParse(string r) {
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