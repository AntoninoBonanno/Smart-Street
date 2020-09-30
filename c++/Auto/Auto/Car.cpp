#include "Car.h"
#include <windows.h>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <stdlib.h>
#include <stdio.h>


//public
/**
* Metodo  che data un indirizzo ip crea la connessione con il punto di accesso, ed effettua la get per richiedere le possibili destinazioni
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
* Metodo  che data una destinazione, richiama richiestaAccess e runStreet
* 
* @param destination: destinazione che si vuole raggiungere
*/
void Car::goToDestination(string destination) {

    if (conn == NULL) throw new exception("Recupera la destinazione");   
    string host,port, access_token;
    tie(host,port, access_token) = requestAccess(destination);
    runStreet(host, port, access_token);
}

//private
/**
* Metodo che effettua una richiesta POST al punto di accesso con la destinazione e la sua targa, restituendo host, port e il token di accesso
* 
* @param destinazione: destinazione che si vuole raggiungere
* @return host: indirizzo ip della strada da percorrere
          port: porta a cui fare la richiesta
          access_token: token per l'accesso
*/
tuple<string, string, string> Car::requestAccess(string destinazione) {    
    //post con la destinazione scelta, 
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
    //La post mi restitusce un messaggio, un host, una porta e un access token
    cout << response["message"] << endl<<endl;

    return make_tuple(response["host"].asString(), response["port"].asString(), response["access_token"].asString());
    
}

/**
* Metodo  che crea una connessione socket con l'host e con la porta. Invia i suoi dati. 
* Lo scambio di messaggi viene realizzato in maniera ciclica effettuando prima la recv da parte del server e poi il send per le informazioni del client
* recv ricevo un messaggio,un action,una posizone e uno status
* In base all'azione viene chiamata la funzione doAction().
* la send invia i dati dell'auto quali targa,position e speed
* 
* Al termine viene chiusa la connessione. E richiamata la stessa funzione se ho ricevuto un host,una port e un accesstoken 
* @param host: L'indirizzo ip dell'host.\n
*        port: la porta a cui fare le richieste
*        accessToken: il token per accedere           
*/
void Car::runStreet(string host, string port, string accessToken) {
    //cout << "host: " << host <<"port:" << port <<endl;
    //cout << "accessToken:" << accessToken << endl << endl;
    position = 0;
    current_speed = 0;

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
    if (iResult != 0) {
        cout <<"getaddrinfo failed: "<<iResult << endl;;
        WSACleanup();
        exit(0);
    }

    SOCKET ConnectSocket = INVALID_SOCKET;
    res = result;
    // Crea una socket per la connessione al server
    ConnectSocket = socket(result->ai_family, result->ai_socktype, result->ai_protocol);
   
    // Faccio la connect al server.
    iResult = connect(ConnectSocket, result->ai_addr, (int)result->ai_addrlen);
    if (iResult == SOCKET_ERROR) {
        closesocket(ConnectSocket);
        ConnectSocket = INVALID_SOCKET;
    }

    if (ConnectSocket == INVALID_SOCKET) {
        cout << "Unable to connect to server!" << endl;;
        freeaddrinfo(result);
        WSACleanup();
        exit(0);
    }else cout << "Ho stabilito la connessione con " << host << ":" << port << endl;

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

    vector<char> rcvbuffer(4096);
    int tempo_iniziale=clock(); //tempo in millisecondi
    Json::Value response;
  
    //inizio scambio messaggi
    while(true) {
        Sleep(50);
        iResult = recv(ConnectSocket, &rcvbuffer[0], rcvbuffer.size(), 0);
        if (iResult > 0){ 
            string rcv;
            rcv.clear();
            rcv.append(rcvbuffer.cbegin(), rcvbuffer.cend()); 
            response=jsonParse(rcv);
           
            cout <<"Messaggio ricevuto: "<<response["message"]<<endl;
 
            if (response["status"].asString() == "success") {   //in caso di stato=success svolgi l'azione             
                doAction(response["action"], tempo_iniziale, response["position"].asDouble());

                //se ho finito la strada corrente, esco dal while per chiudere la connessione e proseguire per la successiva strada
               if (response["action"]["action"].asString() == "next" || response["action"]["action"].asString() == "end") break;
               //se ho raggiunto la destinazione ho finito
               tempo_iniziale = clock();
            }
            else { 
                cout<<"recv failed" << WSAGetLastError() << endl;
                WSACleanup();
                break; 
            }
        }

        //invio targa/poszione/velocità       
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

    // richiamo la funzione, per percorrere la nuova strada. 
    if (response["action"]["action"].asString() == "next" && response["action"]["host"].asString() != "" && response["action"]["port"].asString() != "")
        runStreet(response["action"]["host"].asString(), response["action"]["port"].asString(), response["action"]["access_token"].asString()); //potrebbe andare in overflow
}

/**
* Metodo che in base all’azione data modifica la velocità della classe Car, calcolando e modificando la sua posizione nella strada. 
*
* @param action: Json con signal, e action
*        start: tempo inziale 
*        position_server: posizione inviatami dal server
*/
void Car::doAction(Json::Value action,int start,double position_server) {
    static int current_limit;
    if (position == 0) current_limit = speed_max;
    cout << action["action"].asString() << endl;
    position = ((current_speed / 3.6) * ((clock()-start)/1000.0)) + position;

    if (position_server > position) position = position_server; //in caso di crash, riprendo da dove mi dice il server

    if (action.size()!= 0) { 
        if (action["signal"].asString() == "speed_limit") current_limit = action["speed_limit"].asInt();
        else if (action["signal"].asString() == "stop") current_limit = speed_max;


        if (action["action"].asString() == "fermati") {
            int speed_to_stop = (action["distance"].asInt() * 10) / 3;
            if (speed_to_stop < current_speed) current_speed = speed_to_stop;            
        }
        else if (action["action"].asString() == "rallenta" && current_speed > 20) current_speed = current_speed - (rand() % 10 + 1);        
    }
    if (action.size() == 0 || (action["action"].asString()=="accelera")) {                       
        if (current_speed> current_limit/2) current_speed = current_speed + 2;
        else current_speed = current_speed + (rand() % 10 + 1);
        if (current_speed > current_limit) current_speed = current_limit;
    }
    
}

/**
* Metodo che effettua il parse da stringa a json
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