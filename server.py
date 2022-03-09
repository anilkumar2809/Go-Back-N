import socket
import threading
import time
import copy

rfc_list = {}
active_peer_list = {}
response_code = {1:'200 OK\n',2:'400 Bad Request\n',3:'404 Not Found\n',4:'505 P2P-CI Version Not Supported\n'}
BUFFER_SIZE = 4096

def peer_connection(clientsocket, clientaddress):
    print("Request to connect from "+str(clientaddress))
    try:
        active_peer_list[clientaddress] = "ALIVE"
        while True:
            response = 'P2P-CI/1.0 '
            try:
                data = clientsocket.recv(BUFFER_SIZE)
            except Exception as e:
                print("Connection Exception occured from CLient"+str(clientaddress))
                del active_peer_list[clientaddress]
                rfc_list_temp = copy.copy(rfc_list)
                for rfc_number in rfc_list_temp:
                    for x in rfc_list_temp[rfc_number]:
                        print(x)
                        if clientaddress[0] == x[3] and clientaddress[1] == x[4]:
                            rfc_list[rfc_number].remove(x)
                            if len(rfc_list[rfc_number]) == 0 or rfc_list[rfc_number] == [] :
                                del rfc_list[rfc_number]
                print("Termination to CLient "+str(clientaddress)+" success")
            if data:
                incoming_data = data.decode('utf-8').split('\n')
                LINE1 = incoming_data[0].split(' ')
                method = LINE1[0]
                version = LINE1[len(LINE1)-1]
                #print(incoming_data)
                #print(method)
                #print(version)
                if version != 'P2P-CI/1.0':
                    response = response + response_code[4]
                elif method == 'ADD':
                    response = response  + response_code[1]
                    rfc_number = incoming_data[0].split(' ')[2]
                    host = incoming_data[1].split(': ')[1]
                    port = incoming_data[2].split(': ')[1]
                    title = incoming_data[3].split(': ')[1]
                    if rfc_number not in rfc_list:
                        rfc_list[rfc_number] = []
                    insert_data = (host,port,title,clientaddress[0],clientaddress[1])
                    rfc_list[rfc_number].append(insert_data)
                elif  method == 'LOOKUP':
                    rfc_number = incoming_data[0].split(' ')[2]
                    if rfc_number in rfc_list:
                        response = response  + response_code[1]
                        for x in rfc_list[rfc_number]:
                            response+= 'RFC '+rfc_number+' '+x[2]+' '+x[0]+' '+x[1]+'\n'
                    else:
                        response = response  + response_code[3]
                elif  method == 'LIST':
                    response+=response_code[1]
                    for rfc_number in rfc_list:
                        for x in rfc_list[rfc_number]:
                            response+= 'RFC '+rfc_number+' '+x[2]+' '+x[0]+' '+x[1]+'\n'
                elif method == 'LEAVE' or method == 'EXIT' or method == 'END':
                    del active_peer_list[clientaddress]
                    rfc_list_temp = copy.copy(rfc_list)
                    for rfc_number in rfc_list_temp:
                        for x in rfc_list_temp[rfc_number]:
                            if clientaddress[0] == x[3] and clientaddress[1] == x[4]:
                                rfc_list[rfc_number].remove(x)
                                if len(rfc_list[rfc_number]) == 0 or rfc_list[rfc_number] ==[]:
                                    del rfc_list[rfc_number]
                    response = response + response_code[1]+ "TERMINATION SUCCESS : "+str(clientaddress)
                    reply = bytes(response,'utf-8')
                    clientsocket.sendall(reply)
                    time.sleep(1)
                    break
                else:
                    response = response + response_code[2]
            else:
                response = response + response_code[2]
            if clientaddress in active_peer_list:
                print("Sending  to client "+str(clientaddress)+" Reply = "+response)
                reply = bytes(response,'utf-8')
                clientsocket.sendall(reply)
            time.sleep(1)
    except Exception as e:
        print(e.with_traceback()) 

#https://docs.python.org/3/howto/sockets.html
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.bind(('0.0.0.0', 7734))
serversocket.listen(5)

while True:
    (clientsocket, clientaddress) = serversocket.accept()
    print(clientaddress)
    server_socket = threading.Thread(target = peer_connection,args=(clientsocket, clientaddress,))
    server_socket.start()