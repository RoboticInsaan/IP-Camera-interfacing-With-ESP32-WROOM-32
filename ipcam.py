
import socket,time,string,base64,hashlib,xml.etree.ElementTree as ET

m_Vars = {
    "bufLen" : 1024,
    "defaultServerIp" : "192.168.1.4",
    "defaultServerPort" : 1935,
    "defaultTestUri" : "/video.mp4",
    "defaultUserAgent" : "RTSP Client",
    "defaultUsername" : "admin",
    "defaultPassword" : "Embedded@"
}

def genmsg_DESCRIBE(url,seq,userAgent,authSeq):
    msgRet = "DESCRIBE " + url + " RTSP/1.0\r\n"
    msgRet += "CSeq: " + str(seq) + "\r\n"
    msgRet += "Authorization: " + authSeq + "\r\n"
    msgRet += "User-Agent: " + userAgent + "\r\n"
    msgRet += "Accept: application/sdp\r\n"
    msgRet += "\r\n"
    return msgRet
    
def genmsg_SETUP(url,seq,userAgent,authSeq):
    msgRet = "SETUP " + url + " RTSP/1.0\r\n"
    msgRet += "CSeq: " + str(seq) + "\r\n"
    msgRet += "Authorization: " + authSeq + "\r\n"
    msgRet += "User-Agent: " + userAgent + "\r\n"
    msgRet += "Blocksize: 65535\r\n"
    msgRet += "Transport: RTP/AVP/TCP;unicast\r\n"
    msgRet += "\r\n"
    return msgRet

def genmsg_OPTIONS(url,seq,userAgent,sessionId,authSeq):
    msgRet = "OPTIONS " + url + " RTSP/1.0\r\n"
    msgRet += "CSeq: " + str(seq) + "\r\n"
    msgRet += "User-Agent: " + userAgent + "\r\n"
    msgRet += "Session: " + sessionId + "\r\n"
    msgRet += "\r\n"
    return msgRet

def genmsg_PLAY(url,seq,userAgent,sessionId,authSeq):
    msgRet = "PLAY " + url + " RTSP/1.0\r\n"
    msgRet += "CSeq: " + str(seq) + "\r\n"
    msgRet += "User-Agent: " + userAgent + "\r\n"
    msgRet += "Session: " + sessionId + "\r\n"
    msgRet += "Range: npt=0.000-\r\n"
    msgRet += "\r\n"
    return msgRet

def genmsg_TEARDOWN(url,seq,userAgent,sessionId,authSeq):
    msgRet = "TEARDOWN " + url + " RTSP/1.0\r\n"
    msgRet += "CSeq: " + str(seq) + "\r\n"
    msgRet += "User-Agent: " + userAgent + "\r\n"
    msgRet += "Session: " + sessionId + "\r\n"
    msgRet += "\r\n"
    return msgRet

def decodeControl(bytesContent):
    mapRetInf = {}
    messageStrings = bytesContent.decode('utf-8').split("\n")
    for element in messageStrings:
        a = element.find("rtsp")
        if a >= 0:
            mapRetInf = element[a:]
    return mapRetInf

def decodeSession(strContent):
    mapRetInf = {}
    messageStrings = strContent.decode('utf-8').split("\n")
    for element in messageStrings:
        if "Session" in element:
            a = element.find(":")
            b = element.find(";")
            mapRetInf = element[a+2:b]
    return mapRetInf    

def generateAuthString(username,password,realm,method,uri,nonce):
    mapRetInf = {}
    combined_str1 = username + ":" + realm.decode('utf-8') + ":" + password
    combined_str2 = method + ":" + uri
    m1 = hashlib.md5(combined_str1.encode('utf-8')).hexdigest()
    m2 = hashlib.md5(combined_str2.encode('utf-8')).hexdigest()
    combined_str3 = m1 + ":" + nonce.decode('utf-8') + ":" + m2
    response = hashlib.md5(combined_str3.encode('utf-8')).hexdigest()

    mapRetInf = "Digest "
    mapRetInf += "username=\"" + m_Vars["defaultUsername"] + "\", "
    mapRetInf += "realm=\"" + realm.decode('utf-8') + "\", "
    mapRetInf += "algorithm=\"MD5\", "
    mapRetInf += "nonce=\"" + nonce.decode('utf-8') + "\", "    
    mapRetInf += "uri=\"" + uri + "\", "
    mapRetInf += "response=\"" + response + "\""
    return mapRetInf  
                                
s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.connect((m_Vars["defaultServerIp"],m_Vars["defaultServerPort"]))  
seq  = 1

url = "rtsp://" + m_Vars["defaultServerIp"] + m_Vars["defaultTestUri"]

isDigest = False
authSeq = base64.b64encode((m_Vars["defaultUsername"] + ":" + m_Vars["defaultPassword"]).encode("ascii"))
authSeq = "Basic " + authSeq.decode("ascii")


print(genmsg_DESCRIBE(url,seq,m_Vars["defaultUserAgent"],authSeq))
s.send(genmsg_DESCRIBE(url, seq, m_Vars["defaultUserAgent"], authSeq).encode('utf-8'))
print("\n")
print("\n")
msg1 = s.recv(m_Vars["bufLen"])
print(msg1)
print("\n")
print("\n")
seq = seq + 1

if msg1.find(b"Unauthorized") > 1:
    isDigest = True

    # New DESCRIBE with digest authentication
    start = msg1.find(b"realm")
    begin = msg1.find(b"\"", start)
    end = msg1.find(b"\"", begin + 1)
    realm = msg1[begin+1:end]

    start = msg1.find(b"nonce")
    begin = msg1.find(b"\"", start)
    end = msg1.find(b"\"", begin + 1)
    nonce = msg1[begin+1:end]

    authSeq = generateAuthString(m_Vars["defaultUsername"],m_Vars["defaultPassword"],realm,"DESCRIBE",m_Vars["defaultTestUri"],nonce)
    
    print(genmsg_DESCRIBE(url,seq,m_Vars["defaultUserAgent"],authSeq))
    s.send(genmsg_DESCRIBE(url, seq, m_Vars["defaultUserAgent"], authSeq).encode('utf-8'))
    print("\n")
    print("\n")
    msg1 = s.recv(m_Vars["bufLen"])
    print(msg1)
    print("\n")
    print("\n")
    seq = seq + 1

control = decodeControl(msg1)

if isDigest == True:
    authSeq = generateAuthString(m_Vars["defaultUsername"],m_Vars["defaultPassword"],realm,"SETUP",m_Vars["defaultTestUri"],nonce)

print(genmsg_SETUP(control,seq,m_Vars["defaultUserAgent"],authSeq))
s.send(genmsg_SETUP(control, seq, m_Vars["defaultUserAgent"], authSeq).encode('utf-8'))
print("\n")
print("\n")
msg1 = s.recv(m_Vars["bufLen"])
print(msg1)  
print("\n")
print("\n")
seq = seq + 1

sessionId = decodeSession(msg1)

print (genmsg_OPTIONS(url,seq,m_Vars["defaultUserAgent"],sessionId,authSeq))
s.send(genmsg_OPTIONS(url,seq,m_Vars["defaultUserAgent"],sessionId,authSeq).encode('utf-8'))
print("\n")
print("\n")
msg1 = s.recv(m_Vars["bufLen"])
print (msg1)
print("\n")
print("\n")
seq = seq + 1

print (genmsg_PLAY(url + "/",seq,m_Vars["defaultUserAgent"],sessionId,authSeq))
print("\n")
print("\n")
s.send(genmsg_PLAY(url + "/",seq,m_Vars["defaultUserAgent"],sessionId,authSeq).encode('utf-8'))
msg1 = s.recv(m_Vars["bufLen"])
print (msg1)  
print("\n")
print("\n")
seq = seq + 1

starttime = time.time()

while True :

    # Send a new RTSP OPTION command to keep the stream alive
    now = time.time()
    if (now - starttime) > 50:

        print (genmsg_OPTIONS(url,seq,m_Vars["defaultUserAgent"],sessionId,authSeq))
        s.send(genmsg_OPTIONS(url,seq,m_Vars["defaultUserAgent"],sessionId,authSeq))
        msg1 = s.recv(m_Vars["bufLen"])
        print (msg1)
        
        starttime = time.time()

    msgRcv = s.recv(m_Vars["bufLen"])
    

seq = seq + 1
print (genmsg_TEARDOWN(url,seq,m_Vars["defaultUserAgent"],sessionId,authSeq))
s.send(genmsg_TEARDOWN(url,seq,m_Vars["defaultUserAgent"],sessionId,authSeq))
msg1 = s.recv(m_Vars["bufLen"])
print (msg1)  

s.close()