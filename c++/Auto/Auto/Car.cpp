#include "Car.h"
#include <windows.h>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <stdlib.h>
#include <stdio.h>




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

void Car::goToDestination(string destination) {
    if (conn == NULL) throw new exception("Recupera la destinazione");
    //cout << "Hai scelto la strada: " << StreetList[x] << endl;
    //post con targa e destinazione(id della street)    
    string host,port, access_token;
    tie(host,port, access_token) = richiestaAccess(destination);
    runStreet(host.c_str(), port.c_str(), access_token);
}

//private
void Car::runStreet(string host, string port, string accessToken) {
    cout << "host:" << host <<" port:" << port <<endl;
    cout << "accessToken:" << accessToken << endl;
    //prova socket
    struct addrinfo* result = NULL,
        * ptr = NULL,
        hints;

    WSADATA wsaData;
    // Initialize Winsock
    int iResult = WSAStartup(MAKEWORD(2, 2), &wsaData);
    if (iResult != 0) {
        printf("WSAStartup failed with error: %d\n", iResult);
        exit(0);
    }

    ZeroMemory(&hints, sizeof(hints));
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_protocol = IPPROTO_TCP;
    // Resolve the server address and port
    iResult = getaddrinfo(host.c_str(), port.c_str(), &hints, &result);
    //iResult = getaddrinfo("192.168.217.1", "8080", &hints, &result);
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
    string sendbuf = "{\"access_token\":\"" + accessToken + "\",\"targa\":\"" + code + "\"}";
    cout << sendbuf;
    

    iResult = send(ConnectSocket, sendbuf.c_str(), sendbuf.size(), 0);
    if (iResult == SOCKET_ERROR) {
        printf("send failed: %d\n", WSAGetLastError());
        closesocket(ConnectSocket);
        WSACleanup();
        exit(0);
    }

    printf("Bytes Sent: %ld\n", iResult);

    // Receive data until the server closes the connection
    char recvbuf[512];
    do {
        iResult = recv(ConnectSocket, recvbuf, (int)strlen(recvbuf), 0);
        if (iResult > 0)
            printf("Bytes received: %d\n", iResult);
            //changeSpeed(action);
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

tuple<string, string,string> Car::richiestaAccess(string destinazione) {
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
    string host = response["host"].asString();    //mi restituisce l'address (indirizzo ip della strada destinazione) e l'access token
    string port = response["port"].asString();
    string access_token = response["access_token"].asString();
    return tie(host, port, access_token);
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