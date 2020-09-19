#include "Car.h"
# include <winsock2.h>



//public
Json::Value Car::getDestinations(string address) {
    RestClient::init();// initialize RestClient
    conn = new RestClient::Connection(address);
    // set headers
    RestClient::HeaderFields headers;
    headers["Accept"] = "application/json";
    conn->SetHeaders(headers);
    cout << "Mi sono connesso al: " + address << endl;

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
    cout << response["message"] << endl;
    cout << streets << endl;
    return streets;
}

void Car::goToDestination(const Json::Value streetList, int destination) {
    if (conn == NULL) throw new exception("Recupera la destinazione");
    //cout << "Hai scelto la strada: " << StreetList[x] << endl;
    //post con targa e destinazione(id della street)    
    string destinazione = streetList[destination]["id"].asString();
    string address, access_token;
    tie(address, access_token) = richiestaAccess(destinazione);
    runStreet(address, access_token);
}

//private
void Car::runStreet(string address, string accessToken) {
    /*
    //prova socket
    struct addrinfo* result = NULL,
        * ptr = NULL,
        hints;

    ZeroMemory(&hints, sizeof(hints));
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_protocol = IPPROTO_TCP;

    // Resolve the server address and port
    int iResult = getaddrinfo("server address", "server port", &hints, &result);
    if (iResult != 0) {
        printf("getaddrinfo failed: %d\n", iResult);
        WSACleanup();
        exit(0);
    }

    SOCKET ConnectSocket = INVALID_SOCKET;
    ptr = result;
    // Create a SOCKET for connecting to server
    ConnectSocket = socket(ptr->ai_family, ptr->ai_socktype,
    ptr->ai_protocol);
   
    // Connect to server.
    iResult = connect(ConnectSocket, ptr->ai_addr, (int)ptr->ai_addrlen);
    if (iResult == SOCKET_ERROR) {
        closesocket(ConnectSocket);
        ConnectSocket = INVALID_SOCKET;
    }

    if (ConnectSocket == INVALID_SOCKET) {
        printf("Unable to connect to server!\n");
        freeaddrinfo(result);
        WSACleanup();
        exit(0);
    }
    
    
    // Send an initial buffer
    char* sendbuf;
    iResult = send(ConnectSocket, sendbuf, (int)strlen(sendbuf), 0);
    if (iResult == SOCKET_ERROR) {
        printf("send failed: %d\n", WSAGetLastError());
        closesocket(ConnectSocket);
        WSACleanup();
        exit(0);
    }

    printf("Bytes Sent: %ld\n", iResult);

    // Receive data until the server closes the connection
    char* recvbuf;
    do {
        iResult = recv(ConnectSocket, recvbuf, (int)strlen(recvbuf), 0);
        if (iResult > 0)
            printf("Bytes received: %d\n", iResult);
        else if (iResult == 0)
            printf("Connection closed\n");
        else
            printf("recv failed: %d\n", WSAGetLastError());
    } while (iResult > 0);

    // shutdown the send half of the connection since no more data will be sent
    iResult = shutdown(ConnectSocket, SD_SEND);
    if (iResult == SOCKET_ERROR) {
        printf("shutdown failed: %d\n", WSAGetLastError());
        closesocket(ConnectSocket);
        WSACleanup();
        exit(0);
    }
    // cleanup
    closesocket(ConnectSocket);
    WSACleanup();


    */

    /*RestClient::Response post = conn->post("/", "{\"accessToken\":\"" + accessToken + "\",\"targa\":\"" + code + "\"}");
    if (post.code != 200) {
        cout << "Errore nella richiesta di post" << endl;
        cout << post.code << endl;
        cout << post.body << endl;
        RestClient::disable();
        exit(0);
    }

    sendInfo();*/
}

tuple<string, string> Car::richiestaAccess(string destinazione) {
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
    Json::Value response = json_parse(post); //faccio il parse
    cout << response["message"] << endl;
    string address = response["address"].asString();  //mi restituisce l'address (indirizzo ip della strada destinazione) e l'access token
    string access_token = response["access_token"].asString();
    return tie(address, access_token);
}

void Car::sendInfo() {
   /* while (true) {
        RestClient::Response post = conn->post("/", "{\"current_speed\":\"" + current_speed + "\",\"position\":\"" + position + "\"}");
        if (post.code != 200) {
            cout << "Errore nella richiesta di post" << endl;
            cout << post.code << endl;
            cout << post.body << endl;
            RestClient::disable();
            exit(0);
        }
        Json::Value response = json_parse(post);
        string azione=response["azione"]
        changeSpeed(azione);
        if(response["Cambia ip"].asString()==cambia strada) { 
            
            break;
        }
    }

    */
    RestClient::disable();
}

void Car::changeSpeed(string action) {
    if (action == "") { //o con switch se action è un numero (?)
        current_speed++;
    }
    else current_speed--;
}