# Auto

The Client was written entirely in C ++, using the following support libraries: restclient-cpp, jsoncpp and winsock2

Specifications:

- Ask the access point for possible destinations, and choose one.
- Contact a street via the provided IP address and token.
- It periodically communicates with the road by communicating its position, current speed and license plate.
- It modulates the speed according to the information it receives from the road

## Dependencies

* [restclient-cpp](https://github.com/mrtazz/restclient-cpp)
* [jsoncpp](https://github.com/open-source-parsers/jsoncpp)


## Installation

1) Install restclient-cpp and jsoncpp

    Open cmd as administrator

    `> git clone https://github.com/Microsoft/vcpkg.git`

    `> cd vcpkg`

    `> ./bootstrap-vcpkg.sh`

    `> ./vcpkg integrate instal`

    `> ./vcpkg install restclient-cpp`

    `> ./vcpkg install jsoncpp`


## Execution

Run this command:

`> cd c++\Auto\Release`

`> Auto.exe`


## Authors

[Biuso Mario](https://github.com/Mariobiuso)
