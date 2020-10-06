#include "Car.h"
#include <windows.h>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <stdio.h>
#include <iomanip>


//public
/**
* Metodo che dato un indirizzo ip (address) va ad inizializzare un RestClient, permettendo di effettuare una connessione Rest con il punto di accesso specificato. Successivamente effettua la GET per richiedere le possibili destinazioni.
* 
* @param address: indirizzo ip del Punto di accesso
* @return streets: lista delle strade
*/
Json::Value Car::getDestinations(string address) {

    RestClient::init(); // initialize RestClient
    conn = new RestClient::Connection(address);
    // set headers
    RestClient::HeaderFields headers;
    headers["Accept"] = "application/json";
    conn->SetHeaders(headers);
    cout << endl<< "Mi sto connettendo al: " + address << endl;

    //richiesta get, per richiedere le possibili destinazioni
    RestClient::Response request = conn->get("/");
    if (request.code != 200) {
        cout << "Errore nella richiesta di recupero destinazione" << endl;
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
* Metodo che data una destinazione, richiama requestAccess() per andare a recuperare l’indirizzo e l’access_token della strada dal punto di accesso. Successivamente passeremo tali valori al metodo runStreet()
* 
* @param destination: destinazione che si vuole raggiungere
*/
void Car::goToDestination(string destination) {

    if (conn == NULL) throw new exception("Recupera la destinazione");   
    string host,port, access_token;
    int errors=0;
    
    while(errors<2){ //se ho degli errori rieffetuo la richiesta al Punto di accesso al max 2 volte
        try {
            tie(host, port, access_token) = requestAccess(destination);
            runStreet(host, port, access_token);            
            break;
        }
        catch(string e) {
            errors++;
            cout << endl << "\033[31m" << "Tentativo " << errors << ": " << e << "\033[0m" << endl << endl;

            /*HANDLE hConsole = GetStdHandle(STD_OUTPUT_HANDLE);
            SetConsoleTextAttribute(hConsole, 12);
            cout << endl << "Tentativo " << errors << ": " << e << endl << endl;
            SetConsoleTextAttribute(hConsole, 15);   */    
        }
    }

    RestClient::disable();
  
}

//private
/**
* Metodo che effettua una richiesta POST al punto di accesso con la destinazione e la sua targa. Restituendo host, port e il token di accesso
* 
* @param destinazione: destinazione che si vuole raggiungere
* @return host: indirizzo ip della strada da percorrere
* @return port: porta a cui fare la richiesta
* @return access_token: token per l'accesso
*/
tuple<string, string, string> Car::requestAccess(string destinazione) {    
    //post con la destinazione scelta, 
    RestClient::Response post = conn->post("/", "{\"destinazione\":" + destinazione + ",\"targa\":\"" + this->code + "\"}");
    if (post.code != 200) {
        cout << "Errore nella richiesta di accesso" << endl;
        cout << post.code << endl;
        cout << post.body << endl;
        RestClient::disable();
        exit(0);
    }
    
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
* la send invia i dati dell'auto quali targa,this->position e speed
* 
* Al termine viene chiusa la connessione. E richiamata la stessa funzione se ho ricevuto un host,una port e un accesstoken 
* @param host: L'indirizzo ip dell'host.\n
* @param port: la porta a cui fare le richieste
* @param accessToken: il token per accedere
*/
void Car::runStreet(string host, string port, string accessToken) {
    
    this->position = 0;
    this->current_speed = 0;

    struct addrinfo* result = NULL,        
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
        cout <<"Impossibile contattare la strada: "<< iResult << endl;
        WSACleanup();
        throw string("Impossibile contattare la strada");
    }

    SOCKET ConnectSocket = INVALID_SOCKET;
    // Crea una socket per la connessione al server
    ConnectSocket = socket(result->ai_family, result->ai_socktype, result->ai_protocol);
   
    // Faccio la connect al server.
    iResult = connect(ConnectSocket, result->ai_addr, (int)result->ai_addrlen);
    if (iResult == SOCKET_ERROR) {
        closesocket(ConnectSocket);
        ConnectSocket = INVALID_SOCKET;
    }

    if (ConnectSocket == INVALID_SOCKET) {
        cout << "Impossibile contattare la strada!" << endl;
        freeaddrinfo(result);
        WSACleanup();
        throw string("Impossibile contattare la strada");
    }
    else cout << "Ho stabilito la connessione con la strada: " << host << ":" << port << endl;

    // Invio un buffer con access_token e targa per richiedere l'accesso
    string sendbuf = "{\"access_token\":\"" + accessToken + "\",\"targa\":\"" + this->code + "\"}";

    iResult = send(ConnectSocket, sendbuf.c_str(), sendbuf.size(), 0);
    if (iResult == SOCKET_ERROR) {
        cout << "Richiesta di accesso fallita: "<< WSAGetLastError()<< endl;;
        closesocket(ConnectSocket);
        WSACleanup();
        throw string("Richiesta di accesso fallita");
    }

    vector<char> rcvbuffer(4096);
    int tempo_iniziale=clock(); //tempo in millisecondi
    Json::Value response;
    string rcv;
  
    //inizio scambio messaggi
    while(true) {

        Sleep(150); //effettuiamo lo scambio di messaggi ogni 150 ms
        //ricevo i dati dalla strada
        iResult = recv(ConnectSocket, &rcvbuffer[0], rcvbuffer.size(), 0);
        if (iResult > 0){ //se ho ricevuto dei dati 

            rcv.clear(); 
            rcv.append(rcvbuffer.cbegin(), rcvbuffer.cend()); 
            response=jsonParse(rcv); //lo scambio di messaggi avviene tramite costrutti JSON                       
 
            if (response["status"].asString() == "success") {   //in caso di stato=success svolgi l'azione             
                doAction(response["action"], tempo_iniziale, response["position"].asDouble());

                //se ho finito la strada corrente, esco dal while per chiudere la connessione e proseguire per la successiva strada
               if (response["action"]["action"].asString() == "next" || response["action"]["action"].asString() == "end") break;
              
               tempo_iniziale = clock(); //Per calcolare la nuova posizione in base al tempo trascorso
            }
            else { 
                cout<<"Errore da parte della strada: " << response["message"] << endl;
                closesocket(ConnectSocket);
                WSACleanup();
                throw string("Errore da parte della strada");
            }

            cout << fixed << setprecision(2) <<"Posizione: " << this->position << " m - Velocita': " << this->current_speed <<" km/h - Targa: " << this->code << endl;
            cout<<response["message"] << endl<<endl;

        }

        //invio targa/poszione/velocità       
        string sendinfo = "{\"targa\":\"" + this->code + "\",\"position\":" + to_string(this->position) + ",\"speed\":" + to_string(this->current_speed) + "}";      
        
        iResult = send(ConnectSocket, sendinfo.c_str(), sendinfo.size(), 0);
        if (iResult == SOCKET_ERROR) {
            cout << "Invio dati fallito: "<< WSAGetLastError()<< endl;;
            closesocket(ConnectSocket);
            WSACleanup();
            throw string("Invio dati fallito");
        }

    }


    // chiudo la connessione con la strada
    iResult = shutdown(ConnectSocket, SD_SEND);
    if (iResult == SOCKET_ERROR) {
        cout << "Disconnessione fallita: "<< WSAGetLastError();
        closesocket(ConnectSocket);
        WSACleanup();
        exit(0);
    }else cout << "Ho chiuso la connessione con la strada: " << host<<": "<< port << endl;

    // Se esiste una strada successiva (ricevo next) richiamo la funzione, per percorrere la nuova strada. 
    if (response.size() == 0) throw string("Non ho ricevuto nulla dalla strada");
    if (response["action"]["action"].asString() == "next" && response["action"]["host"].asString() != "" && response["action"]["port"].asString() != "")
        runStreet(response["action"]["host"].asString(), response["action"]["port"].asString(), response["action"]["access_token"].asString()); 
}

/**
* Metodo che in base all’azione data, modifica la velocità della classe Car, calcolando e modificando la sua posizione nella strada.
* 
* @param action: Json con signal, e action
* @param start: tempo inziale 
* @param position_server: posizione inviatami dal server
*/
void Car::doAction(Json::Value action,int start,double position_server) {
    static int current_limit;
    if (this->position == 0) current_limit = this->speed_max; //se sono all'inzio della strada il limite corrente è il mio this->speed_max
    
    //calcolo della posizione in base al tempo trascorso
    this->position = ((this->current_speed / 3.6) * ((int(clock())-start)/1000.0)) + this->position;

    if (position_server > this->position) this->position = position_server; //in caso di crash, riprendo dalla posizione indicatami dalla strada
    
    if (action.size()!= 0) { //se ho delle azioni da fare
        if (action["signal"].asString() == "speed_limit") current_limit = action["speed_limit"].asInt(); //aggiorno il limite

        if (action["action"].asString() == "fermati") {
            int speed_to_stop = (action["distance"].asInt() * 10) / 3; //calcolo lo spazio di arresto in base alla distanza dell'ostacolo
            if (speed_to_stop < this->current_speed) this->current_speed = speed_to_stop; //rallentando fino a fermarmi            
        }
        else if (action["action"].asString() == "rallenta" && this->current_speed > 20) this->current_speed = this->current_speed - (rand() % 10 + 1);
    }
    //se non ho action oppure l'azione da effettuare è accelera
    if (action["action"].asString() == "" || (action["action"].asString()=="accelera")) {
        if (this->current_speed> current_limit/2) this->current_speed = this->current_speed + 2; //incremento lo speed di poco se sono quasi al limite
        else this->current_speed = this->current_speed + (rand() % 10 + 1); //incremento lo speed
        if (this->current_speed > current_limit) this->current_speed = current_limit; //limito il mio speed fino al massimo consentito
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