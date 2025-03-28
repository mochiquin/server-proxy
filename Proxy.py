# Include the libraries for socket and system calls
import socket
import sys
import os
import argparse
import re

# 1MB buffer size
BUFFER_SIZE = 1000000

# Get the IP address and Port number to use for this web proxy server
parser = argparse.ArgumentParser()
parser.add_argument('hostname', help='the IP Address Of Proxy Server')
parser.add_argument('port', help='the port number of the proxy server')
args = parser.parse_args()
proxyHost = args.hostname
proxyPort = int(args.port)

# Create a server socket, bind it to a port and start listening
try:
  # Create a server socket
  # ~~~~ INSERT CODE ~~~~
  serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  # ~~~~ END CODE INSERT ~~~~
  print ('Created socket')
except:
  print ('Failed to create socket')
  sys.exit()

try:
  # Bind the the server socket to a host and port
  # ~~~~ INSERT CODE ~~~~
  serverSocket.bind((proxyHost, proxyPort))
  # ~~~~ END CODE INSERT ~~~~
  print ('Port is bound')
except:
  print('Port is already in use')
  sys.exit()

try:
  # Listen on the server socket
  # ~~~~ INSERT CODE ~~~~
  serverSocket.listen(5)
  # ~~~~ END CODE INSERT ~~~~
  print ('Listening to socket')
except:
  print ('Failed to listen')
  sys.exit()

# continuously accept connections
while True:
  print ('Waiting for connection...')
  clientSocket = None

  # Accept connection from client and store in the clientSocket
  try:
    # ~~~~ INSERT CODE ~~~~
    clientSocket, clientAddress = serverSocket.accept()
    # ~~~~ END CODE INSERT ~~~~
    print ('Received a connection')
  except:
    print ('Failed to accept connection')
    sys.exit()

  # Get HTTP request from client
  # and store it in the variable: message_bytes
  # ~~~~ INSERT CODE ~~~~
  message_bytes = clientSocket.recv(BUFFER_SIZE)
  # ~~~~ END CODE INSERT ~~~~
  message = message_bytes.decode('utf-8')
  print ('Received request:')
  print ('< ' + message)

  # Extract the method, URI and version of the HTTP client request 
  requestParts = message.split()
  method = requestParts[0]
  URI = requestParts[1]
  version = requestParts[2]

  print ('Method:\t\t' + method)
  print ('URI:\t\t' + URI)
  print ('Version:\t' + version)
  print ('')

  # Get the requested resource from URI
  # Remove http protocol from the URI
  URI = re.sub('^(/?)http(s?)://', '', URI, count=1)

  # Remove parent directory changes - security
  URI = URI.replace('/..', '')

  # Split hostname from resource name
  resourceParts = URI.split('/', 1)
  hostname = resourceParts[0]
  resource = '/'

  if len(resourceParts) == 2:
    # Resource is absolute URI with hostname and resource
    resource = resource + resourceParts[1]

  print ('Requested Resource:\t' + resource)

  # Check if resource is in cache
  try:
    cacheLocation = './' + hostname + resource
    if cacheLocation.endswith('/'):
        cacheLocation = cacheLocation + 'default'

    print ('Cache location:\t\t' + cacheLocation)
    cacheLocation = cacheLocation.replace('?', '_').replace('&', '_').replace('=', '_').replace(':', '_')

    fileExists = os.path.isfile(cacheLocation)
    
    # Check wether the file is currently in the cache
    cacheFile = open(cacheLocation, "rb")
    cacheData = cacheFile.readlines()

    print ('Cache hit! Loading from cache file: ' + cacheLocation)
    # ProxyServer finds a cache hit
    # Send back response to client 
    # ~~~~ INSERT CODE ~~~~
    clientSocket.sendall(b"".join(cacheData) if isinstance(cacheData[0], bytes) else "".join(cacheData).encode())
    # ~~~~ END CODE INSERT ~~~~
    cacheFile.close()
    print ('Sent to the client:')
    print ('> ' + cacheData)
  except:
    # cache miss.  Get resource from origin server
    originServerSocket = None
    # Create a socket to connect to origin server
    # and store in originServerSocket
    # ~~~~ INSERT CODE ~~~~
    originServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # ~~~~ END CODE INSERT ~~~~

    print ('Connecting to:\t\t' + hostname + '\n')
    try:
      # Get the IP address for a hostname
      address = socket.gethostbyname(hostname)
      # Connect to the origin server
      # ~~~~ INSERT CODE ~~~~
      originServerSocket.connect((address, 80))
      # ~~~~ END CODE INSERT ~~~~
      print ('Connected to origin Server')

      originServerRequest = ''
      originServerRequestHeader = ''
      # Create origin server request line and headers to send
      # and store in originServerRequestHeader and originServerRequest
      # originServerRequest is the first line in the request and
      # originServerRequestHeader is the second line in the request
      # ~~~~ INSERT CODE ~~~~
      originServerRequest = method + " " + resource + " " + "HTTP/1.1"
      originServerRequestHeader = "Host: " + hostname
      # ~~~~ END CODE INSERT ~~~~

      # Construct the request to send to the origin server
      request = originServerRequest + '\r\n' + originServerRequestHeader + '\r\n\r\n'

      # Request the web resource from origin server
      print ('Forwarding request to origin server:')
      for line in request.split('\r\n'):
        print ('> ' + line)

      try:
        originServerSocket.sendall(request.encode() )
      except socket.error:
        print ('Forward request to origin failed')
        sys.exit()

      print('Request sent to origin server\n')

      # Get the response from the origin server
      # ~~~~ INSERT CODE ~~~~
      response_bytes = b""
      originServerSocket.settimeout(10) #seting the timeout to 10 seconds
      try:
        while True:
          data = originServerSocket.recv(BUFFER_SIZE)
          if len(data) > 0:
            response_bytes += data
          else:
            break
      except socket.timeout:  
        print('Timeout error')
      # ~~~~ END CODE INSERT ~~~~
      # Send the response to the client
      # ~~~~ INSERT CODE ~~~~
      # check the response code is a 302 redirect
      is_404 = False
      is_redirect = False
      redirect_url = None

      try:
        response_text = response_bytes.decode('utf-8')
        response_lines = response_text.split("\r\n")
        if len(response_lines) > 0:
          status_line = response_lines[0]
          print("status line: " + status_line)
          if"302" in status_line:
            is_redirect=True
            print("302 Found")
            clientSocket.sendall(response_bytes) #send the response to the client
          elif "404 Not Found" in status_line:
            is_404 = True
            print("404 Not Found")
            clientSocket.sendall(response_bytes)
          else:
            clientSocket.sendall(response_bytes)
      except Exception as e:  
        print("Error decoding response: " + str(e))
        
        clientSocket.sendall(response_bytes)

      # ~~~~ END CODE INSERT ~~~~

      # Create a new file in the cache for the requested file.
      cacheDir, file = os.path.split(cacheLocation)
      print ('cached directory ' + cacheDir)
      if not os.path.exists(cacheDir):
        os.makedirs(cacheDir)
      cacheFile = open(cacheLocation, 'wb')

      # Save origin server response in the cache file
      # ~~~~ INSERT CODE ~~~~
      #check the status code and decide whether to cache the response

      need_cache = True
      try:
        response_text = response_bytes.decode('utf-8', errors='ignore')
        response_lines = response_text.split('\r\n')
        
        # get the status code
        status_code = None
        if len(response_lines) > 0:
          status_line = response_lines[0]
          match = re.search(r'HTTP/\d\.\d (\d+)', status_line)
          if match:
            status_code = int(match.group(1))
        
        # check the cache control header
        cache_control = None
        for line in response_lines:
          if line.lower().startswith('cache-control:'):
            cache_control = line[14:].strip().lower()
            break
        
        # based on the code and headers, decide whether to cache the response
        if status_code not in (200, 203, 204, 206, 300, 301, 404, 405, 410, 414, 501):
          need_cache = False
        # check Cache-Control header
        elif cache_control:
          if 'no-store' in cache_control:
            need_cache = False
          elif 'max-age' in cache_control:
            max_age_match = re.search(r'max-age=(\d+)', cache_control)
            if max_age_match and int(max_age_match.group(1)) == 0:
              need_cache = False
        
        print(f"Cache decision: need_cache = {need_cache}")
        
        # when the need_cache is True, write the response to the cache file
        if need_cache and not is_redirect:
          cacheDir, _ = os.path.split(cacheLocation)
          if not os.path.exists(cacheDir):
            try:
              os.makedirs(cacheDir)
            except Exception as e:
              print(f"Error creating cache directory: {str(e)}")
          
          # write the response to the cache file
          try:
            cacheFile.write(response_bytes)
            print(f"Response cached in {cacheLocation}")
            if is_404:
              print("Cached a 404 Not Found response")
          except Exception as e:
            print(f"Error writing to cache file: {str(e)}")
        else:
          print(f"Response not cached due to: need_cache={need_cache}, is_redirect={is_redirect}")
          
      except Exception as e:
        print(f"Error processing cache logic: {str(e)}")
        # when an error occurs, do not cache the response
        need_cache = False
        
      # ~~~~ END CODE INSERT ~~~~
      cacheFile.close()
      print ('cache file closed')

      # finished communicating with origin server - shutdown socket writes
      print ('origin response received. Closing sockets')
      originServerSocket.close()
       
      clientSocket.shutdown(socket.SHUT_WR)
      print ('client socket shutdown for writing')
    except OSError as err:
      print ('origin server request failed. ' + err.strerror)

  try:
    clientSocket.close()
  except:
    print ('Failed to close client socket')
