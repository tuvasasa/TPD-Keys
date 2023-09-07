import base64

from pywidevine.cdm import Cdm
from pywidevine.device import Device
from pywidevine.pssh import PSSH
from base64 import b64encode

import requests
import json
import random
import uuid
import httpx
import DRMHeaders

MyWVD = ""


class Settings:
    def __init__(self, userCountry: str = None, randomProxy: bool = False) -> None:
        self.randomProxy = randomProxy
        self.userCountry = userCountry
        self.ccgi_url = "https://client.hola.org/client_cgi/"
        self.ext_ver = self.get_ext_ver()
        self.ext_browser = "chrome"
        self.user_uuid = uuid.uuid4().hex
        self.user_agent = "Mozilla/5.0 (X11; Fedora; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"
        self.product = "cws"
        self.port_type_choice: str
        self.zoneAvailable = ["AR", "AT", "AU", "BE", "BG", "BR", "CA", "CH", "CL", "CO", "CZ", "DE", "DK", "ES", "FI",
                              "FR", "GR", "HK", "HR", "HU", "ID", "IE", "IL", "IN", "IS", "IT", "JP", "KR", "MX", "NL",
                              "NO", "NZ", "PL", "RO", "RU", "SE", "SG", "SK", "TR", "UK", "US", "GB"]

    def get_ext_ver(self) -> str:
        about = httpx.get("https://hola.org/access/my/settings#/about").text
        if 'window.pub_config.init({"ver":"' in about:
            version = about.split('window.pub_config.init({"ver":"')[1].split('"')[0]
            return version

        # last know working version
        return "1.199.485"


class Engine:
    def __init__(self, Settings) -> None:
        self.settings = Settings

    def get_proxy(self, tunnels, tls=False) -> str:
        login = f"user-uuid-{self.settings.user_uuid}"
        proxies = dict(tunnels)
        protocol = "https" if tls else "http"
        for k, v in proxies["ip_list"].items():
            return "%s://%s:%s@%s:%d" % (
                protocol,
                login,
                proxies["agent_key"],
                k if tls else v,
                proxies["port"][self.settings.port_type_choice],
            )

    def generate_session_key(self, timeout: float = 10.0) -> json:
        post_data = {"login": "1", "ver": self.settings.ext_ver}
        return httpx.post(
            f"{self.settings.ccgi_url}background_init?uuid={self.settings.user_uuid}",
            json=post_data,
            headers={"User-Agent": self.settings.user_agent},
            timeout=timeout,
        ).json()["key"]

    def zgettunnels(
        self, session_key: str, country: str, timeout: float = 10.0
    ) -> json:

        qs = {
            "country": country.lower(),
            "limit": 1,
            "ping_id": random.random(),
            "ext_ver": self.settings.ext_ver,
            "browser": self.settings.ext_browser,
            "uuid": self.settings.user_uuid,
            "session_key": session_key,
        }

        return httpx.post(
            f"{self.settings.ccgi_url}zgettunnels", params=qs, timeout=timeout
        ).json()


class Hola:
    def __init__(self, Settings) -> None:
        self.myipUri: str = "https://hola.org/myip.json"
        self.settings = Settings

    def get_country(self) -> str:

        if not self.settings.randomProxy and not self.settings.userCountry:
            self.settings.userCountry = httpx.get(self.myipUri).json()["country"]

        if (
            not self.settings.userCountry in self.settings.zoneAvailable
            or self.settings.randomProxy
        ):
            self.settings.userCountry = random.choice(self.settings.zoneAvailable)

        return self.settings.userCountry


def init_proxy(data):
    settings = Settings(
        data["zone"]
    )  # True if you want random proxy each request / "DE" for a proxy with region of your choice (German here) / False if you wish to have a proxy localized to your IP address
    settings.port_type_choice = data[
        "port"
    ]  # direct return datacenter ipinfo, peer "residential" (can fail sometime)

    hola = Hola(settings)
    engine = Engine(settings)

    userCountry = hola.get_country()
    session_key = engine.generate_session_key()
#    time.sleep(10)
    tunnels = engine.zgettunnels(session_key, userCountry)

    return engine.get_proxy(tunnels)


allowed_countries = [
        "AR", "AT", "AU", "BE", "BG", "BR", "CA", "CH", "CL", "CO", "CZ", "DE", "DK", "ES", "FI",
        "FR", "GR", "HK", "HR", "HU", "ID", "IE", "IL", "IN", "IS", "IT", "JP", "KR", "MX", "NL",
        "NO", "NZ", "PL", "RO", "RU", "SE", "SG", "SK", "TR", "UK", "US", "GB"
    ]

print("Welcome to TPD-Keys! \n")
print("[Generic Services]")
print("1. Generic without any headers")
print("2. Generic with generic headers")
print("3. Generic with headers from DRMHeaders.py")
print("4. JSON Widevine challenge, headers from DRMHeaders.py \n")
print("[Specific Services]")
print("5. Canal+ Live TV")
print("6. Youtube \n")
print("7. Star \n")
print("8. Directv \n")
selection = int(input("Please choose a service: "))

if selection == 1:
    print("")
    print("Generic without headers.")
    ipssh = input("PSSH: ")
    pssh = PSSH(ipssh)
    device = Device.load(MyWVD)
    cdm = Cdm.from_device(device)
    session_id = cdm.open()
    challenge = cdm.get_license_challenge(session_id, pssh)
    ilicurl = input("License URL: ")
    country_code = input("Proxy? (2 letter country code or N for no): ")
    if len(country_code) == 2 and country_code.upper() in allowed_countries:
        proxy = init_proxy({"zone": country_code, "port": "peer"})
        proxies = {
            "http": proxy
        }
        print(f"Using proxy {proxies['http']}")
        licence = requests.post(ilicurl, proxies=proxies, data=challenge)
    else:
        print("Proxy-less request.")
        licence = requests.post(ilicurl, data=challenge)
    licence.raise_for_status()
    cdm.parse_license(session_id, licence.content)
    fkeys = ""
    for key in cdm.get_keys(session_id):
        if key.type != 'SIGNING':
            fkeys += key.kid.hex + ":" + key.key.hex() + "\n"
    print("")
    print(fkeys)
    cdm.close(session_id)

elif selection == 2:
    print("")
    print("Generic with generic headers.")
    ipssh = input("PSSH: ")
    pssh = PSSH(ipssh)
    device = Device.load(MyWVD)
    cdm = Cdm.from_device(device)
    session_id = cdm.open()
    challenge = cdm.get_license_challenge(session_id, pssh)
    ilicurl = input("License URL: ")
    country_code = input("Proxy? (2 letter country code or N for no): ")
    generic_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    if len(country_code) == 2 and country_code.upper() in allowed_countries:
        proxy = init_proxy({"zone": country_code, "port": "peer"})
        proxies = {
            "http": proxy
        }
        print(f"Using proxy {proxies['http']}")
        licence = requests.post(ilicurl, data=challenge, headers=generic_headers, proxies=proxies)
    else:
        print("Proxy-less request.")
        licence = requests.post(ilicurl, data=challenge, headers=generic_headers)
    licence.raise_for_status()
    cdm.parse_license(session_id, licence.content)
    fkeys = ""
    for key in cdm.get_keys(session_id):
        if key.type != 'SIGNING':
            fkeys += key.kid.hex + ":" + key.key.hex() + "\n"
    print("")
    print(fkeys)
    cdm.close(session_id)

elif selection == 3:
    print("")
    print("Generic with headers from DRMHeaders.py")
    ipssh = input("PSSH: ")
    pssh = PSSH(ipssh)
    device = Device.load(MyWVD)
    cdm = Cdm.from_device(device)
    session_id = cdm.open()
    challenge = cdm.get_license_challenge(session_id, pssh)
    ilicurl = input("License URL: ")
    country_code = input("Proxy? (2 letter country code or N for no): ")
    if len(country_code) == 2 and country_code.upper() in allowed_countries:
        proxy = init_proxy({"zone": country_code, "port": "peer"})
        proxies = {
            "http": proxy
        }
        print(f"Using proxy {proxies['http']}")
        licence = requests.post(ilicurl, data=challenge, headers=DRMHeaders.headers, proxies=proxies)
    else:
        print("Proxy-less request.")
        licence = requests.post(ilicurl, data=challenge, headers=DRMHeaders.headers)
    licence.raise_for_status()
    cdm.parse_license(session_id, licence.content)
    fkeys = ""
    for key in cdm.get_keys(session_id):
        if key.type != 'SIGNING':
            fkeys += key.kid.hex + ":" + key.key.hex() + "\n"
    print("")
    print(fkeys)
    cdm.close(session_id)

elif selection == 4:
    print("")
    print("JSON Widevine challenge, headers from DRMHeaders.py")
    ipssh = input("PSSH: ")
    pssh = PSSH(ipssh)
    device = Device.load(MyWVD)
    cdm = Cdm.from_device(device)
    session_id = cdm.open()
    challenge = cdm.get_license_challenge(session_id, pssh)
    request = b64encode(challenge)
    ilicurl = input("License URL: ")
    pid = input("releasePid: ")
    country_code = input("Proxy? (2 letter country code or N for no): ")
    if len(country_code) == 2 and country_code.upper() in allowed_countries:
        proxy = init_proxy({"zone": country_code, "port": "peer"})
        proxies = {
            "http": proxy
        }
        print(f"Using proxy {proxies['http']}")
        licence = requests.post(ilicurl, headers=DRMHeaders.headers, proxies=proxies, json={
            "getRawWidevineLicense":
                {
                    'releasePid': pid,
                    'widevineChallenge': str(request, "utf-8")
                }
        })
    else:
        print("Proxy-less request.")
        licence = requests.post(ilicurl, headers=DRMHeaders.headers, json={
            "getRawWidevineLicense":
                {
                    'releasePid': pid,
                    'widevineChallenge': str(request, "utf-8")
                }
        })
    licence.raise_for_status()
    cdm.parse_license(session_id, licence.content)
    fkeys = ""
    for key in cdm.get_keys(session_id):
        if key.type != 'SIGNING':
            fkeys += key.kid.hex + ":" + key.key.hex() + "\n"
    print("")
    print(fkeys)
    cdm.close(session_id)

elif selection == 5:
    print("")
    print("Canal+ Live TV")
    ipssh = input("PSSH: ")
    channel = input("Channel: ")
    live_token = input("Live Token: ")
    pssh = PSSH(ipssh)
    device = Device.load(MyWVD)
    cdm = Cdm.from_device(device)
    session_id = cdm.open()
    challenge = cdm.get_license_challenge(session_id, pssh)
    request = b64encode(challenge)
    ilicurl = "https://secure-browser.canalplus-bo.net/WebPortal/ottlivetv/api/V4/zones/cpfra/devices/31/apps/1/jobs/GetLicence"
    country_code = input("Proxy? (2 letter country code or N for no): ")
    if len(country_code) == 2 and country_code.upper() in allowed_countries:
        proxy = init_proxy({"zone": country_code, "port": "peer"})
        proxies = {
            "http": proxy
        }
        print(f"Using proxy {proxies['http']}")
        licence = requests.post(ilicurl, headers=DRMHeaders.headers, proxies=proxies, json={
            'ServiceRequest': {
                'InData': {
                    'EpgId': channel,
                    'LiveToken': live_token,
                    'UserKeyId': '_sdivii9vz',
                    'DeviceKeyId': '1676391356366-a3a5a7d663de',
                    'ChallengeInfo': f'{base64.b64encode(challenge).decode()}',
                    'Mode': 'MKPL',
                },
            },
        })
    else:
        print("Proxy-less request.")
        licence = requests.post(ilicurl, headers=DRMHeaders.headers, json={
            'ServiceRequest': {
                'InData': {
                    'EpgId': channel,
                    'LiveToken': live_token,
                    'UserKeyId': '_jprs988fy',
                    'DeviceKeyId': '1678334845207-61e4e804264c',
                    'ChallengeInfo': f'{base64.b64encode(challenge).decode()}',
                    'Mode': 'MKPL',
                },
            },
        })
    licence.raise_for_status()
    cdm.parse_license(session_id, licence.json()["ServiceResponse"]["OutData"]["LicenseInfo"])
    fkeys = ""
    for key in cdm.get_keys(session_id):
        if key.type != 'SIGNING':
            fkeys += key.kid.hex + ":" + key.key.hex() + "\n"
    print("")
    print(fkeys)
    cdm.close(session_id)

elif selection == 6:
    print("")
    print("YouTube")
    ipssh = "AAAAQXBzc2gAAAAA7e+LqXnWSs6jyCfc1R0h7QAAACEiGVlUX01FRElBOjZlMzI4ZWQxYjQ5YmYyMWZI49yVmwY="
    ilicurl = input("License URL: ")
    pssh = PSSH(ipssh)
    device = Device.load(MyWVD)
    cdm = Cdm.from_device(device)
    session_id = cdm.open()
    challenge = cdm.get_license_challenge(session_id, pssh)
    country_code = input("Proxy? (2 letter country code or N for no): ")
    json_data = DRMHeaders.json_data
    json_data["licenseRequest"] = base64.b64encode(challenge).decode("utf-8")
    if len(country_code) == 2 and country_code.upper() in allowed_countries:
        proxy = init_proxy({"zone": country_code, "port": "peer"})
        proxies = {
            "http": proxy
        }
        print(f"Using proxy {proxies['http']}")
        licence = requests.post(ilicurl, cookies=DRMHeaders.cookies, headers=DRMHeaders.headers, proxies=proxies, json=json_data)
    else:
        print("Proxy-less request.")
        licence = requests.post(ilicurl, cookies=DRMHeaders.cookies, headers=DRMHeaders.headers, json=json_data)

    licence.raise_for_status()
    cdm.parse_license(session_id, licence.json()["license"].replace("-", "+").replace("_", "/"))
    fkeys = ""
    for key in cdm.get_keys(session_id):
        if key.type != 'SIGNING':
            fkeys += key.kid.hex + ":" + key.key.hex() + "\n"
    cache_key(ipssh, fkeys)
    print("")
    print(fkeys)
    cdm.close(session_id)

elif selection == 7:
    print("")
    print("Star+.")
    ipssh = input("PSSH: ")
    pssh = PSSH(ipssh)
    device = Device.load(MyWVD)
    cdm = Cdm.from_device(device)
    session_id = cdm.open()
    challenge = cdm.get_license_challenge(session_id, pssh)
    ilicurl = "https://star.playback.edge.bamgrid.com/widevine/v1/obtain-license"
    authorization_b = input("authorization :")
    country_code = input("Proxy? (2 letter country code or N for no): ")
    generic_headers = {
     'Authorization':  authorization_b,
    }
    if len(country_code) == 2 and country_code.upper() in allowed_countries:
        proxy = init_proxy({"zone": country_code, "port": "peer"})
        proxies = {
            "http": proxy
        }
        print(f"Using proxy {proxies['http']}")
        licence = requests.post(ilicurl, data=challenge, headers=generic_headers, proxies=proxies)
    else:
        print("Proxy-less request.")
        licence = requests.post(ilicurl, data=challenge, headers=generic_headers)
    licence.raise_for_status()
    cdm.parse_license(session_id, licence.content)
    fkeys = ""
    for key in cdm.get_keys(session_id):
        if key.type != 'SIGNING':
            fkeys += key.kid.hex + ":" + key.key.hex() + "\n"
    print("Your key is")
    print(fkeys)
    cdm.close(session_id)

elif selection == 8:
    print("")
    print("Directv Latinoamerica.")
    ipssh = input("PSSH: ")
    pssh = PSSH(ipssh)
    device = Device.load(MyWVD)
    cdm = Cdm.from_device(device)
    session_id = cdm.open()
    challenge = cdm.get_license_challenge(session_id, pssh)
    ilicurl = input("License:")
    authorization_b = input("authorization :")
    country_code = input("Proxy? (2 letter country code or N for no): ")
    generic_headers = {
     'Authorization':  authorization_b,
    }
    if len(country_code) == 2 and country_code.upper() in allowed_countries:
        proxy = init_proxy({"zone": country_code, "port": "peer"})
        proxies = {
            "http": proxy
        }
        print(f"Using proxy {proxies['http']}")
        licence = requests.post(ilicurl, data=challenge, headers=generic_headers, proxies=proxies)
    else:
        print("Proxy-less request.")
        licence = requests.post(ilicurl, data=challenge, headers=generic_headers)
    licence.raise_for_status()
    cdm.parse_license(session_id, licence.content)
    fkeys = ""
    for key in cdm.get_keys(session_id):
        if key.type != 'SIGNING':
            fkeys += key.kid.hex + ":" + key.key.hex() + "\n"
    print("Your key is")
    print(fkeys)
    cdm.close(session_id)
   

else:
    print("Invalid selection")
