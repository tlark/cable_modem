#### 1a. Login (Login request)
curl 'https://192.168.100.1/HNAP1/' \
  -H 'Accept: application/json, text/javascript, */*; q=0.01' \
  -H 'Accept-Language: en-US,en;q=0.9' \
  -H 'Connection: keep-alive' \
  -H 'Content-Type: application/json; charset=UTF-8' \
  -H 'Cookie: Secure; Secure; uid=YHsBPtt%2F; PrivateKey=3FB80FB0603B80287990157DC433C4C0' \
  -H 'HNAP_AUTH: 66829E416684539F1949459D0B9153B7 1660595829630' \
  -H 'Origin: https://192.168.100.1' \
  -H 'Referer: https://192.168.100.1/Login.html' \
  -H 'SOAPAction: "http://purenetworks.com/HNAP1/Login"' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36' \
  -H 'X-Requested-With: XMLHttpRequest' \
  -H 'sec-ch-ua: "Chromium";v="104", " Not A;Brand";v="99", "Google Chrome";v="104"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  --data-raw '{"Login":{"Action":"request","Username":"admin","LoginPassword":"","Captcha":"","PrivateLogin":"LoginPassword"}}' \
  --compressed \
  --insecure ;

#### 1b. Login (Login)
curl 'https://192.168.100.1/HNAP1/' \
  -H 'Accept: application/json, text/javascript, */*; q=0.01' \
  -H 'Accept-Language: en-US,en;q=0.9' \
  -H 'Connection: keep-alive' \
  -H 'Content-Type: application/json; charset=UTF-8' \
  -H 'Cookie: Secure; Secure; uid=pensU5%2Bu; PrivateKey=B98589081FBB010DE05BFB260AF36F79' \
  -H 'HNAP_AUTH: 8338888E40776D6D614BC63DCA20C60B 1660595829754' \
  -H 'Origin: https://192.168.100.1' \
  -H 'Referer: https://192.168.100.1/Login.html' \
  -H 'SOAPAction: "http://purenetworks.com/HNAP1/Login"' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36' \
  -H 'X-Requested-With: XMLHttpRequest' \
  -H 'sec-ch-ua: "Chromium";v="104", " Not A;Brand";v="99", "Google Chrome";v="104"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  --data-raw '{"Login":{"Action":"login","Username":"admin","LoginPassword":"58C1FE468814A03BE09778D84BACD870","Captcha":"","PrivateLogin":"LoginPassword"}}' \
  --compressed \
  --insecure ;

#### 1c. Login (GetHomeConnection, GetHomeAddress)
curl 'https://192.168.100.1/HNAP1/' \
  -H 'Accept: application/json' \
  -H 'Accept-Language: en-US,en;q=0.9' \
  -H 'Connection: keep-alive' \
  -H 'Content-Type: application/json' \
  -H 'Cookie: Secure; Secure; uid=pensU5%2Bu; PrivateKey=B98589081FBB010DE05BFB260AF36F79' \
  -H 'HNAP_AUTH: 0F2D4173602C2395BAA839F5D718BB16 1660595830142' \
  -H 'Origin: https://192.168.100.1' \
  -H 'Referer: https://192.168.100.1/MotoHome.html' \
  -H 'SOAPACTION: "http://purenetworks.com/HNAP1/GetMultipleHNAPs"' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36' \
  -H 'sec-ch-ua: "Chromium";v="104", " Not A;Brand";v="99", "Google Chrome";v="104"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  --data-raw '{"GetMultipleHNAPs":{"GetHomeConnection":"","GetHomeAddress":""}}' \
  --compressed \
  --insecure ;
#### 2. Press Advanced (GetMotoStatusSoftware, GetMotoStatusXXX)
curl 'https://192.168.100.1/HNAP1/' \
  -H 'Accept: application/json' \
  -H 'Accept-Language: en-US,en;q=0.9' \
  -H 'Connection: keep-alive' \
  -H 'Content-Type: application/json' \
  -H 'Cookie: Secure; Secure; uid=pensU5%2Bu; PrivateKey=B98589081FBB010DE05BFB260AF36F79' \
  -H 'HNAP_AUTH: 6CFF4A27C06BD6734A0CC58A7CBCDFCC 1660595885447' \
  -H 'Origin: https://192.168.100.1' \
  -H 'Referer: https://192.168.100.1/MotoStatusSoftware.html' \
  -H 'SOAPACTION: "http://purenetworks.com/HNAP1/GetMultipleHNAPs"' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36' \
  -H 'sec-ch-ua: "Chromium";v="104", " Not A;Brand";v="99", "Google Chrome";v="104"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  --data-raw '{"GetMultipleHNAPs":{"GetMotoStatusSoftware":"","GetMotoStatusXXX":""}}' \
  --compressed \
  --insecure ;
#### 3a. Press Connection (GetMotoStatusStartupSequence, GetMotoStatusConnectionInfo, GetMotoStatusDownstreamChannelInfo, GetMotoStatusUpstreamChannelInfo, GetMotoLagStatus)
curl 'https://192.168.100.1/HNAP1/' \
  -H 'Accept: application/json' \
  -H 'Accept-Language: en-US,en;q=0.9' \
  -H 'Connection: keep-alive' \
  -H 'Content-Type: application/json' \
  -H 'Cookie: Secure; Secure; uid=pensU5%2Bu; PrivateKey=B98589081FBB010DE05BFB260AF36F79' \
  -H 'HNAP_AUTH: 921D014FBA7D46335296F2BCAF9508EA 1660596012489' \
  -H 'Origin: https://192.168.100.1' \
  -H 'Referer: https://192.168.100.1/MotoStatusConnection.html' \
  -H 'SOAPACTION: "http://purenetworks.com/HNAP1/GetMultipleHNAPs"' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36' \
  -H 'sec-ch-ua: "Chromium";v="104", " Not A;Brand";v="99", "Google Chrome";v="104"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  --data-raw '{"GetMultipleHNAPs":{"GetMotoStatusStartupSequence":"","GetMotoStatusConnectionInfo":"","GetMotoStatusDownstreamChannelInfo":"","GetMotoStatusUpstreamChannelInfo":"","GetMotoLagStatus":""}}' \
  --compressed \
  --insecure ;
#### 3b. Press Connection (GetMotoStatusDownstreamChannelInfo, GetMotoStatusUpstreamChannelInfo)
curl 'https://192.168.100.1/HNAP1/' \
  -H 'Accept: application/json' \
  -H 'Accept-Language: en-US,en;q=0.9' \
  -H 'Connection: keep-alive' \
  -H 'Content-Type: application/json' \
  -H 'Cookie: Secure; Secure; uid=pensU5%2Bu; PrivateKey=B98589081FBB010DE05BFB260AF36F79' \
  -H 'HNAP_AUTH: 870A54A35D3AEA85D93EB10DC0C7D068 1660596017722' \
  -H 'Origin: https://192.168.100.1' \
  -H 'Referer: https://192.168.100.1/MotoStatusConnection.html' \
  -H 'SOAPACTION: "http://purenetworks.com/HNAP1/GetMultipleHNAPs"' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36' \
  -H 'sec-ch-ua: "Chromium";v="104", " Not A;Brand";v="99", "Google Chrome";v="104"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  --data-raw '{"GetMultipleHNAPs":{"GetMotoStatusDownstreamChannelInfo":"","GetMotoStatusUpstreamChannelInfo":""}}' \
  --compressed \
  --insecure ;

#### 4a. Press Event Log (GetMotoStatusLog, GetMotoStatusLogXXX)
curl 'https://192.168.100.1/HNAP1/' \
  -H 'Accept: application/json' \
  -H 'Accept-Language: en-US,en;q=0.9' \
  -H 'Connection: keep-alive' \
  -H 'Content-Type: application/json' \
  -H 'Cookie: Secure; Secure; uid=pensU5%2Bu; PrivateKey=B98589081FBB010DE05BFB260AF36F79' \
  -H 'HNAP_AUTH: D2D8255737E011FCB24B26C4DE5D0DA9 1660596212785' \
  -H 'Origin: https://192.168.100.1' \
  -H 'Referer: https://192.168.100.1/MotoStatusLog.html' \
  -H 'SOAPACTION: "http://purenetworks.com/HNAP1/GetMultipleHNAPs"' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36' \
  -H 'sec-ch-ua: "Chromium";v="104", " Not A;Brand";v="99", "Google Chrome";v="104"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  --data-raw '{"GetMultipleHNAPs":{"GetMotoStatusLog":"","GetMotoStatusLogXXX":""}}' \
  --compressed \
  --insecure ;

#### 5a. Press Security (GetMotoStatusSecAccount, GetMotoStatusSecXXX)
curl 'https://192.168.100.1/HNAP1/' \
  -H 'Accept: application/json' \
  -H 'Accept-Language: en-US,en;q=0.9' \
  -H 'Connection: keep-alive' \
  -H 'Content-Type: application/json' \
  -H 'Cookie: Secure; Secure; uid=pensU5%2Bu; PrivateKey=B98589081FBB010DE05BFB260AF36F79' \
  -H 'HNAP_AUTH: 3A6F6D5CAB2377A4EDADB1C16C919251 1660596280163' \
  -H 'Origin: https://192.168.100.1' \
  -H 'Referer: https://192.168.100.1/MotoStatusSecurity.html' \
  -H 'SOAPACTION: "http://purenetworks.com/HNAP1/GetMultipleHNAPs"' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36' \
  -H 'sec-ch-ua: "Chromium";v="104", " Not A;Brand";v="99", "Google Chrome";v="104"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  --data-raw '{"GetMultipleHNAPs":{"GetMotoStatusSecAccount":"","GetMotoStatusSecXXX":""}}' \
  --compressed \
  --insecure ;

#### 6a. Press Reboot (SetStatusSecuritySettings: {MotoStatusSecurityAction: "1", MotoStatusSecXXX: "XXX"})
curl 'https://192.168.100.1/HNAP1/' \
  -H 'Accept: application/json' \
  -H 'Accept-Language: en-US,en;q=0.9' \
  -H 'Connection: keep-alive' \
  -H 'Content-Type: application/json' \
  -H 'Cookie: Secure; Secure; uid=pensU5%2Bu; PrivateKey=B98589081FBB010DE05BFB260AF36F79' \
  -H 'HNAP_AUTH: B64E5955C28618D861E389B46EBF9EEC 1660596378326' \
  -H 'Origin: https://192.168.100.1' \
  -H 'Referer: https://192.168.100.1/MotoStatusSecurity.html' \
  -H 'SOAPACTION: "http://purenetworks.com/HNAP1/SetStatusSecuritySettings"' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36' \
  -H 'sec-ch-ua: "Chromium";v="104", " Not A;Brand";v="99", "Google Chrome";v="104"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  --data-raw '{"SetStatusSecuritySettings":{"MotoStatusSecurityAction":"1","MotoStatusSecXXX":"XXX"}}' \
  --compressed \
  --insecure ;

#### 6b. Press Reboot (GetMotoStatusSecAccount, GetMotoStatusSecXXX)
curl 'https://192.168.100.1/HNAP1/' \
  -H 'Accept: application/json' \
  -H 'Accept-Language: en-US,en;q=0.9' \
  -H 'Connection: keep-alive' \
  -H 'Content-Type: application/json' \
  -H 'Cookie: Secure; Secure; uid=pensU5%2Bu; PrivateKey=B98589081FBB010DE05BFB260AF36F79' \
  -H 'HNAP_AUTH: 10356B6CD774119BBF0DE9644CDD96B8 1660596378412' \
  -H 'Origin: https://192.168.100.1' \
  -H 'Referer: https://192.168.100.1/MotoStatusSecurity.html' \
  -H 'SOAPACTION: "http://purenetworks.com/HNAP1/GetMultipleHNAPs"' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36' \
  -H 'sec-ch-ua: "Chromium";v="104", " Not A;Brand";v="99", "Google Chrome";v="104"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  --data-raw '{"GetMultipleHNAPs":{"GetMotoStatusSecAccount":"","GetMotoStatusSecXXX":""}}' \
  --compressed
