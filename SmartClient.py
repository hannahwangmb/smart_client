import socket as s
import sys
import ssl
import re


HTTP2_SUPPORT = False
PROTECTED = False
MAX_REDIRECTIONS = 5
redirection_counter = 0

def main():
    
    if len(sys.argv) != 2:
        print("\nInvalid input \nUsage: python3 SmartClient.py <URI>\n")
        sys.exit(1)
    else:
        uri = sys.argv[1]
        protocol, host, port, path = parse_user_input(uri)
        if host is None:
            print("Invalid input 2\nUsage: python3 SmartClient.py <URI>")
            sys.exit(1)
            
    # connect and get response from the server
    response = connect_server(protocol, host, port, path)
    header = response.split("\r\n\r\n",1)[0]
    if response is None:
        print("\nError: Cannot connect to the server")
        sys.exit(1)
    else:
        # print out the response from the server, marking the header
        # print("Connection: Keep-Alive")
        print("\n--FINAL RESULT---\n")
        print("website: "+ host)
        
        if http2_checker(host)=='h2':
            HTTP2_SUPPORT = True
            print("1. Supports http2: Yes")
        else:
            print("1. Supports http2: No")
        
        # print out cookie name, expire time, domain name
        print("2. List of Cookies: ", end='')
        cookie(header)
        
        # print out if the website is password-protected
        if PROTECTED:
            print("\n3. Password-protected: Yes")
        else:
            print("\n3. Password-protected: No")

# connect to the server and get response
def connect_server(protocol, host, port, path):
    # check protocol and port
    global redirection_counter
    if port is None:
        if protocol == "https":
            ports = [443]
        elif protocol == "http":
            ports = [80]
        elif protocol is None:
            ports = [443,80]
    else:
        ports = [port]

    for p in ports:
        wrapped_sock = None
        if p == 443:
            protocol = "https"
        elif p == 80:
            protocol = "http"

        try:
            if p == 443:
                context = ssl.create_default_context()
                wrapped_sock = context.wrap_socket(
                    s.socket(s.AF_INET), server_hostname=host
                )
            else:
                wrapped_sock = s.socket(s.AF_INET)
                
            wrapped_sock.settimeout(10)
            wrapped_sock.connect((host, p))
            print(f"Connected to {host} on port {p}\n")
            print(f"URI: Protocol: {protocol}, Host: {host}, Port: {port}, Path: {path}")
            request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: Keep-Alive\r\n\r\n"
            print("\n---Request begin---\n" + request)
            wrapped_sock.send(request.encode('utf-8'))
            print("\n---Request End---")
            print("HTTP request sent, awaiting response...")
            response = wrapped_sock.recv(2048)
            status_line = response.split(b"\r\n")[0]
            header = response.split(b"\r\n\r\n",1)[0]
            print("\n---Response header---")
            print(header.decode('utf-8'))
            
            # check the reponse status code
            if status_line.startswith(b"HTTP/1.1 2") or status_line.startswith(b"HTTP/1.0 2"):
                # success
                return response.decode('utf-8')
            elif status_line.startswith(b"HTTP/1.1 3") or status_line.startswith(b"HTTP/1.0 3"):
                # redirection
                location_header = re.findall(b"(?i)location: (.*?)\n", response)
                if location_header:
                    new_location = location_header[0].decode('utf-8').strip()
                    print("\nRedirecting to: " + new_location)
                    if redirection_counter < MAX_REDIRECTIONS:
                        redirection_counter += 1
                        print(f"Redirection count: {redirection_counter}")
                        protocol, host, port, path = parse_user_input(new_location)
                        print(f"New URI:Protocol: {protocol}, Host: {host}, Port: {port}, Path: {path}")
                        response = connect_server(protocol, host, port, path)
                        return response
                    else:
                        print(f"Exceeded maximum redirections ({MAX_REDIRECTIONS}). Exiting.")
                        sys.exit(1)
            elif status_line.startswith(b"HTTP/1.1 401") or status_line.startswith(b"HTTP/1.0 401"):
                # password-protected
                global PROTECTED
                PROTECTED = True
                
                
            return response.decode('utf-8')
            # more status code to be added
            


        except ConnectionRefusedError:
            pass
        
        finally:
            if wrapped_sock:
                wrapped_sock.close()
    print("Error: Failed to connect to the server")
    sys.exit(1)


def cookie(header):
    # get the cookie name, expire time, domain name
    cookies = []
    cookie_list = re.findall(r"Set-Cookie: (.*?)\n", header)
    # print(cookie_list)
    for c in cookie_list:
        cookie_parts = c.split('; ')
        # print(cookie_parts)
        cookie_info = {}

        # Extract cookie name
        name = cookie_parts[0].split('=')[0]
        cookie_info['Name'] = name

        # Extract domain and expires, if available
        for part in cookie_parts[1:]:
            part = part.strip()
            if part.startswith('domain='):
                cookie_info['Domain'] = part[7:]
            elif part.startswith('expires='):
                cookie_info['Expires'] = part[8:]

        cookies.append(cookie_info)
        # print(cookies)
    
    # print in format
    for c in cookies:
        print()
        print(f"cookie name: {c['Name']}", end='')
        if 'Domain' in c:
            print(f", domain name: {c['Domain']}", end='')
        if 'Expires' in c:
            print(f", expires time: {c['Expires']}", end='')

    return cookies
    
    
def http2_checker(host):
    # check if the server supports http2
    
    context = ssl.create_default_context()
    context.set_alpn_protocols(['http/1.1', 'h2'])
    sock = context.wrap_socket(s.socket(s.AF_INET, s.SOCK_STREAM), server_hostname=host)
    sock.connect((host, 443))
    sock.send(f"GET / HTTP/1.1\r\nHost: {host}\r\n\r\n".encode())
    negotiated_protocol = sock.selected_alpn_protocol()
    # print("\n"+negotiated_protocol)
    sock.close()
    return negotiated_protocol

def parse_user_input(uri):
    # Define the regular expression pattern
    uri_pattern = r"^((\w+):\/\/)?([^\/:]+)(:(\d+))?(\/.*)?$"

    # Match the URI against the pattern
    match = re.match(uri_pattern, uri)

    if match:
        protocol = match.group(2) if match.group(2) else None
        host = match.group(3) if match.group(3) else None
        port = match.group(5) if match.group(5) else None
        path = match.group(6) if match.group(6) else "/"

        return protocol, host, port, path
    else:
        print("\nInvalid URI \n")
        sys.exit(1)
    
    
    
if __name__ == "__main__":
    main()