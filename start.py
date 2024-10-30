import socket
from dnslib import DNSRecord, DNSQuestion, DNSHeader, QTYPE, A, RR
import logging
import copy

UPSTREAM_DNS_SERVER = "223.5.5.5"
LISTEN_PORT = 53
logging.basicConfig(level = logging.INFO)

def forward_dns(query):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(query.pack(), (UPSTREAM_DNS_SERVER, 53))
        response_data, _ = sock.recvfrom(1024)
        response = DNSRecord.parse(response_data)
        return response
    except Exception as e:
        logging.error("Error in forward_dns: %s", e)
        return None

def handle_dns_request(data):
    try:
        query = DNSRecord.parse(data)
        response = forward_dns(query)
        if response:
            if query.q.qtype == QTYPE.AAAA:
                query.q.qtype = QTYPE.A
                new_response = forward_dns(query)
                if new_response:
                    for rr in new_response.rr:
                        if rr.rtype == QTYPE.A:
                            p_response = response
                            p_response.rr = [rr for rr in p_response.rr if rr.rtype!= QTYPE.AAAA]
                            return p_response.pack()
                    return response.pack()
                else:
                    return response.pack()
            else:
                return response.pack()
        else:
            return None
                    
    except Exception as e:
        logging.error("Error in handle_dns_request: %s", e)
        return None

if __name__ == "__main__":
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(("0.0.0.0", LISTEN_PORT))
    logging.info("DNS forwarder is running on port %d", LISTEN_PORT)
    while True:
        data, addr = server_socket.recvfrom(1024)
        response_data = handle_dns_request(data)
        if response_data:
            server_socket.sendto(response_data, addr)

