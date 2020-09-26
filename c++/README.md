1-installare restclient-cpp (shell amministratore)
    git clone https://github.com/Microsoft/vcpkg.git
    cd vcpkg
    ./bootstrap-vcpkg.sh
    ./vcpkg integrate install
    ./vcpkg install restclient-cpp
    ./vcpkg install jsoncpp


per avviare 
    cd Progetto-APL\c++\Auto\Release
    Auto.exe