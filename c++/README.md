# Auto

The Client was written entirely in C ++, using the following support libraries:
restclient-cpp, jsoncpp and winsock2

Specifications:

- Ask the access point for possible destinations, and choose one.
- Contact a street via the provided IP address and token.
- It periodically communicates with the road by communicating its position, current speed and license plate.
- It modulates the speed according to the information it receives from the road

## Dependencies

* [restclient-cpp](https://github.com/mrtazz/restclient-cpp)
* [jsoncpp](https://github.com/open-source-parsers/jsoncpp)


## Installation

If you want to make changes or the .exe file won't start (else skip this step)

1) Install restclient-cpp and jsoncpp

    Open cmd as administrator or powershell, make sure you have installed the English language pack on Visual Studio.

    `> git clone https://github.com/Microsoft/vcpkg.git`

    `> cd vcpkg`

    `> ./bootstrap-vcpkg.sh`

    `> ./vcpkg integrate install`

    `> ./vcpkg install restclient-cpp` or  `> ./vcpkg install restclient-cpp:x64-windows`

    `> ./vcpkg install jsoncpp` or `> ./vcpkg install jsoncpp:x64-windows`

## Building 
 
If you want to make changes or the .exe file won't start (else skip this step)

Go in c++\Auto and open Auto.sln with Visual Studio 2019, then build with release

## Execution

Run this command:

`> c++\Auto\Release\Auto.exe`

When required insert a license plate and max speed for the Car, and the address of the Access Point.

Then insert the desired destination. 

## Authors

[Biuso Mario](https://github.com/Mariobiuso)
