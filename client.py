import socket
import threading
import os
import sys
import platform
import traceback
response_code = {1:'200 OK\n',2:'400 Bad Request\n',3:'404 Not Found\n',4:'505 P2P-CI Version Not Supported\n'}

def accept_peer_connection(p2p_server):
	# Listen for incoming connections
	p2p_server.listen(5)
	while True:
		print('Waiting for a connection')
		(connection, peer_address) = p2p_server.accept()
		server_thread = threading.Thread(target = peer_data_transfer,args=(connection, peer_address,),daemon = True)
		server_thread.start()

MAX_FILE_BUFFER = 4096
MAX_DATA_BUFFER = 4096*8

def peer_data_transfer(connection, peer_address):
	try:
		print('Download request from ' + str(peer_address))
		response = 'P2P-CI/1.0 '
		data = connection.recv(MAX_DATA_BUFFER)
		print('Received {!r}'.format(data))
		if data:
			incoming_data = data.decode('utf-8').split('\n')
			method = incoming_data[0].split(' ')[0]
			if method == 'GET':
				rfc_number = incoming_data[0].split(' ')[2]
				rfc_filepath = open(path + "/" + rfc_number, "rb")
				response += response_code[1]
				response += 'OS: ' + str(platform.system()) + str(platform.release())
				response += "\nLast-Modified: "+str(os.path.getmtime(path))
				response += "\nContent-Length: "+str(os.path.getsize(path))
				response += "\nContent-Type: text/text\n"
				message = bytes(response,'utf-8')
				connection.sendall(message)
				#SENT THE APPROPRIATE DATA
				temp_data = rfc_filepath.read(MAX_FILE_BUFFER)			
				while True:
					temp_data = bytes(temp_data,'utf-8')
					connection.send(temp_data)
					if len(temp_data) < MAX_FILE_BUFFER:
						break
					temp_data = rfc_filepath.read(MAX_FILE_BUFFER)
				rfc_filepath.close()
				print('Done sending the file')
				print("ENTER your keyword")
			else:
				print('INCORRECT REQUEST FROM '+ peer_address)
				response += response_code[2]
		else:
			print('No data from '+ peer_address)
			response += response_code[3]
	except Exception as e:
		print(e.with_traceback()) 
	finally:
		# Clean up the connection
		connection.close() 

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
p2p_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


path = input('Enter RFCs directory path\n')	
#path = "/Users/simstudent/Downloads/Project/PROJECT1/CLIENT1"
rfc_files = os.listdir(path)
p2p_port = input('Enter upload p2p port number\n') #Upload port number by user
#p2p_port = "9999"
#host_ip = input('Enter this host IP address\n')	
#server_ip = input('Enter centralised server IP address\n')
host_ip = "127.0.0.1"
server_ip = "127.0.0.1"

p2p_server.bind((host_ip,int(p2p_port)))
connection_thread = threading.Thread(target = accept_peer_connection,args=(p2p_server,),daemon=True)
connection_thread.start()

server_addr = (server_ip, 7734)
print("Connecting to  "+server_ip+" on port "+str(7734))
client.connect(server_addr)

rfc_title_map = {'1':"TITLE1",'3':"TITLE2"}
def getTitle(rfc_number):
	if rfc_number in rfc_title_map:
		return rfc_title_map[rfc_number]
	else:
		return "DEFAULTTITLE"

lookup_list = {}
try:
	for rfc_file in rfc_files:
		print(rfc_file)
		send_rfc_metadata = 'ADD RFC ' + rfc_file + ' P2P-CI/1.0\n'+'Host: '+ host_ip +'\nPort: '+ str(p2p_port) + '\nTitle: '+ getTitle(rfc_file)
		print('Sending '+send_rfc_metadata)
		message = bytes(send_rfc_metadata,'utf-8')
		client.sendall(message)
		data = client.recv(MAX_DATA_BUFFER)
		print('Server Response: {!r}'.format(data))
	while True:
		user_input = input('Enter your keyword\n')
		message = bytes(user_input,'utf-8')
		if message == b'LOOKUP':
			rfc_number = input('Enter RFC number to lookup\n')
			send_lookup_data = 'LOOKUP RFC ' + str(rfc_number) + ' P2P-CI/1.0\n'+'Host: '+ host_ip +'\nPort: '+ p2p_port
			msg = bytes(send_lookup_data,'utf-8')
			print('Sending {!r}'.format(msg))
			client.sendall(msg)
			data = client.recv(MAX_DATA_BUFFER)
			reply = data.decode('utf-8')
			if "OK" in reply:
				lines = reply.split('\n')
				lookup_list[rfc_number] = []
				for line in lines[1:]:
					temp = line.split(" ")
					if len(temp) >= 5:
						#if rfc_number not in lookup_list:
						#	lookup_list[rfc_number] = []
						lookup_list[rfc_number].append((temp[2], temp[3], temp[4]))
				if len(lookup_list[rfc_number]) == 0:
					del lookup_list[rfc_number]
		elif message == b'LIST':
			send_listall_query = 'LIST ALL P2P-CI/1.0\n'+'Host: '+ host_ip +'\nPort: '+ p2p_port
			msg = bytes(send_listall_query,'utf-8')
			print('Sending {!r}'.format(msg))
			client.sendall(msg)
			data = client.recv(MAX_DATA_BUFFER)
		elif message == b'GET':
			rfc_number = input('Enter RFC number to download the RFC file\n')
			if rfc_number not in lookup_list or len(lookup_list[rfc_number]) == 0:
				print("Please do RFC lookup first and check if this file exists. If it exists then reenter GET to download the file")
				continue;
			print("Please note that the Download might not work if the lookup is expired. In which case, you are requested to do lookup")
			peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   #peer_client
			rfc_title = lookup_list[rfc_number][0][0]
			peer_ip = lookup_list[rfc_number][0][1]
			peer_port = lookup_list[rfc_number][0][2]
			send_get_data = 'GET RFC ' + rfc_number + ' P2P-CI/1.0\nHost:' + host_ip  + '\nOS: ' + platform.system() + platform.release() 
			msg = bytes(send_get_data,'utf-8')
			peer_address = (peer_ip, int(peer_port) )
			print('Connecting to {} port {}'.format(*peer_address))
			peer_socket.connect(peer_address)
			print('Sending {!r}'.format(msg))
			peer_socket.sendall(msg)
			#NEED TO PROCESS STARTING DATA HERE
			data = peer_socket.recv(MAX_DATA_BUFFER)
			print('Server Response: {}'.format(data.decode('utf-8')))
			#PROCESSED STARTING DATA HERE
			fp = open(path + "/" + rfc_number, "w")
			while True:
				data = peer_socket.recv(MAX_DATA_BUFFER).decode('utf-8')
				fp.write(data)
				if len(data) < MAX_DATA_BUFFER:
					break
			fp.close()
			print('file received \n')	
			send_rfc_metadata = 'ADD RFC ' + rfc_number + ' P2P-CI/1.0\n'+'Host: '+ host_ip +'\nPort: '+ p2p_port + '\nTitle: '+ getTitle(str(rfc_number))
			msg = bytes(send_rfc_metadata,'utf-8')
			print('Sending {!r}'.format(msg))
			client.sendall(msg)
			data = client.recv(MAX_DATA_BUFFER)
		elif message == b'EXIT':
			uinput = 'EXIT P2P-CI/1.0\n'+'Host: '+ host_ip +'\nPort: '+ p2p_port
			msg = bytes(uinput,'utf-8')
			print('Sending {!r}'.format(msg))
			client.sendall(msg)
			data = client.recv(MAX_DATA_BUFFER)
		elif message == b'PRINT':
			print(str(lookup_list))
#			print('Sending {!r}'.format(message))
#			client.sendall(message)
#			data = client.recv(MAX_DATA_BUFFER)
		print('Server Response: {}'.format(data.decode('utf-8')))
		if message == b'EXIT':
			print("closing the server connection")
			break
except Exception as e:
	print(e.with_traceback)
	traceback.print_exc()
	print(e)
finally:
	print('closing socket')
	client.close()
	sys.exit()