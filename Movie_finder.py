# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import os
import re
from urllib.parse import quote

TMDB_API_KEY = "9b7c615cabe385068a90a09b02dea502"
XML_FILE = "movie_database.xml"

# --- SERVER URL GENERATOR ---
# এই অংশটি আপনার দেওয়া বড় লিস্টকে লজিক দিয়ে শর্ট করেছে।
SERVER_URLS = []

# 1. Bangla (Kolkata) Category
SERVER_URLS += [f"http://10.16.100.202/ftps10/iccftps10sasd{i}/Movies/Bangla%20(Kolkata)/" for i in range(1, 10)]
SERVER_URLS += [f"http://10.16.100.206/ftps3/ftps3d{i}/Movies/Bangla%20(Kolkata)/" for i in range(1, 8)]
SERVER_URLS += [f"http://10.16.100.212/iccftps12/iccftps12sasd{i}/Movies/Bangla%20(Kolkata)/" for i in range(1, 10)]

# 2. Dual Audio Category
SERVER_URLS += [f"http://10.16.100.202/ftps10/iccftps10sasd{i}/Movies/Dual%20Audio/" for i in range(1, 10)]
SERVER_URLS += [f"http://10.16.100.206/ftps3/ftps3d{i}/Movies/Dual%20Audio/" for i in range(1, 8)]
SERVER_URLS += [f"http://10.16.100.212/iccftps12/iccftps12sasd{i}/Movies/Dual%20Audio/" for i in range(1, 10)]
SERVER_URLS += [f"http://10.16.100.213/iccftps13/iccftps13sasd{i}/Movies/Dual%20Audio/" for i in range(1, 10)]
SERVER_URLS += [f"http://10.16.100.214/iccftps14/iccftps14sasd{i}/Movies/Dual%20Audio/" for i in range(1, 8)]

# 3. Hindi Category
SERVER_URLS += [f"http://10.16.100.202/ftps10/iccftps10sasd{i}/Movies/Hindi/" for i in range(1, 10)]
SERVER_URLS += [f"http://10.16.100.206/ftps3/ftps3d{i}/Movies/Hindi/" for i in range(1, 8)]
SERVER_URLS += [f"http://10.16.100.212/iccftps12/iccftps12sasd{i}/Movies/Hindi/" for i in range(1, 10)]
SERVER_URLS += [f"http://10.16.100.213/iccftps13/iccftps13sasd{i}/Movies/Hindi/" for i in range(1, 10)]
SERVER_URLS += [f"http://10.16.100.214/iccftps14/iccftps14sasd{i}/Movies/Hindi/" for i in range(1, 8)]

# 4. South Indian (Hindi Dubbed) Category
SERVER_URLS += [f"http://10.16.100.202/ftps10/iccftps10sasd{i}/Movies/South%20Indian%20(Hindi%20Dubbed)/" for i in range(1, 10)]
SERVER_URLS += [f"http://10.16.100.206/ftps3/ftps3d{i}/Movies/South%20Indian%20(Hindi%20Dubbed)/" for i in range(1, 8)]
SERVER_URLS += [f"http://10.16.100.212/iccftps12/iccftps12sasd{i}/Movies/South%20Indian%20(Hindi%20Dubbed)/" for i in range(1, 10)]
SERVER_URLS += [f"http://10.16.100.213/iccftps13/iccftps13sasd{i}/Movies/South%20Indian%20(Hindi%20Dubbed)/" for i in range(1, 10)]
SERVER_URLS += [f"http://10.16.100.214/iccftps14/iccftps14sasd{i}/Movies/South%20Indian%20(Hindi%20Dubbed)/" for i in range(1, 8)]

# --- FUNCTIONS ---

def clean_movie_name(filename):
    clean = re.sub(r'\(.*?\)|\[.*?\]', '', filename)
    clean = re.split(r'\d{4}', clean)[0] 
    clean = re.sub(r'\.(mp4|mkv|avi|ts|1080p|720p|webdl|bluray|h264|hindi|dual|audio|english)', '', clean, flags=re.IGNORECASE)
    return clean.replace('.', ' ').replace('-', ' ').strip()

def get_poster(filename):
    try:
        name = clean_movie_name(filename)
        year_match = re.search(r'(\d{4})', filename)
        year = year_match.group(1) if year_match else ""
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={quote(name)}&year={year}"
        data = requests.get(search_url, timeout=5).json()
        if data.get('results'):
            path = data['results'][0].get('poster_path')
            if path: return f"https://image.tmdb.org/t/p/w500{path}"
    except: pass
    return "https://raw.githubusercontent.com/xbmc/xbmc/master/addons/skin.estuary/extras/default_video.png"

def load_data():
    movies = []
    if os.path.exists(XML_FILE):
        try:
            tree = ET.parse(XML_FILE)
            for m in tree.getroot().findall("movie"):
                movies.append({"title": m.find("title").text, "link": m.find("link").text, "poster": m.find("poster").text})
        except: pass
    return movies

def scan_and_save(mode="update"):
    existing_movies = [] if mode == "fresh" else load_data()
    existing_links = {m['link'] for m in existing_movies}
    new_count = 0
    print(f"\n[!] Scanning {len(SERVER_URLS)} directories. Please wait...")

    for index, url in enumerate(SERVER_URLS, 1):
        try:
            r = requests.get(url, timeout=8)
            soup = BeautifulSoup(r.text, 'html.parser')
            for a in soup.find_all('a'):
                href = a.get('href')
                if href and any(ext in href.lower() for ext in ['.mp4', '.mkv', '.avi']):
                    full_url = url + href
                    if full_url not in existing_links:
                        name = a.get_text().strip()
                        print(f"Adding: {name}")
                        existing_movies.append({"title": name, "link": full_url, "poster": get_poster(name)})
                        existing_links.add(full_url)
                        new_count += 1
        except: continue
        
    root = ET.Element("movies")
    for m in existing_movies:
        movie_node = ET.SubElement(root, "movie")
        ET.SubElement(movie_node, "title").text = m["title"]
        ET.SubElement(movie_node, "link").text = m["link"]
        ET.SubElement(movie_node, "poster").text = m["poster"]

    ET.ElementTree(root).write(XML_FILE, encoding="utf-8", xml_declaration=True)
    print(f"\n[+] Scan Complete! Total: {len(existing_movies)} (New: {new_count})")

def search_movie():
    movies = load_data()
    query = input("\nEnter movie name: ").lower()
    results = [m for m in movies if query in m['title'].lower()]
    for i, m in enumerate(results[:20], 1): print(f"{i}. {m['title']}")
    if results:
        try:
            sel = int(input("\nSelect number (0 to back): "))
            if sel > 0: os.system(f"termux-open --view '{results[sel-1]['link']}'")
        except: print("Error!")
    else: print("Not found.")

if __name__ == "__main__":
    while True:
        print("\n--- CODEX MULTI-SERVER FINDER ---")
        print("1. Fresh Scan | 2. Update Scan | 3. Search | 0. Exit")
        choice = input("Choice: ")
        if choice == "1": scan_and_save("fresh")
        elif choice == "2": scan_and_save("update")
        elif choice == "3": search_movie()
        elif choice == "0": break