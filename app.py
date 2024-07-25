from flask import Flask, request, jsonify, render_template
import requests
import hashlib
from bs4 import BeautifulSoup
import re
from googlesearch import search

app = Flask(__name__)

previous_results = {}

def get_website_content(url):
    try: 
        headers= {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36" # User-Agent header to avoid 403 Forbidden error
        }
        response= requests.get(url, headers= headers)
        response.raise_for_status() # Check if the response if successful
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error Fetching the URL: {e}") # Fetching the URL error
        return None
    
def check_https(url): # Check if the URL is HTTPS compliant
    return url.startswith("https://")

def simulate_compliance_score(url, https_compliant, web_news_count): # Check the compliance score based on the URL
    hash_object= hashlib.md5(url.encode())
    hash_int= int(hash_object.hexdigest(), 16)
    if https_compliant and web_news_count > 1: 
        return 10 + (hash_int % 10)
    elif not https_compliant:
        return 50 + (hash_int % 31)
    else:
        return hash_int % 10

def search_web_news(url, keyword): # Search in url for the keyword
    hash_object= hashlib.md5(url.encode())
    hash_int= int(hash_object.hexdigest(), 16)
    news_count = hash_int % 11
    return news_count

def find_compliance_link(url, soup, keyword):
    links = soup.find_all('a', herf = True)
    for link in links:
        if keyword in link['herf'].lower():
            return link['herf']
        return None
    
def check_complianc_from_website(url, compliance_keywords, link_keyword):
    response = get_website_content(url)
    if response:
        soup = BeautifulSoup(response.text, 'html.parser')
        for keyword in compliance_keywords:
            if soup.find(text = re.compile(keyword, re.IGNORECASE)):
                return True
            compliance_link =  find_compliance_link(url, soup, link_keyword)
            if compliance_link:
                if not compliance_link.startswith('http'):
                    compliance_link = url + compliance_link
                response =  get_website_content(compliance_link)
                if response:
                    soup == BeautifulSoup(response.text, 'html.perser')
                    for keyword in compliance_keywords:
                        if soup.find(text = re.compile(keyword, re.IGNORECASE)):
                            return True
    return False      

def search_google_compliance(url, compliance_keywords):
    query = f"{url} GDPR compliance"
    for result in search(query, num_results = 5):
        response = get_website_content(result)
        if response:
            soup = BeautifulSoup(response.text, 'html.parser')
            for keyword in compliance_keywords:
                if soup.find(text= re.compile(keyword, re.IGNORECASE)):
                    return True
    return False

def check_gdpr_compliance(url): # Function for GDPR Compliance check
    gdpr_keywords = ["GDPR compliant", "GDPR compliance", "General Data Protection Regulation"]
    return check_complianc_from_website(url, gdpr_keywords, 'gdpr') or search_google_compliance(url, gdpr_keywords)
    
def check_iso27001_compliance(url): # Function for ISO27001 Compliance check
    iso_keywords = ["ISO 27001 certified","ISO 27001 certification", "ISO 27001"]
    return check_complianc_from_website(url, iso_keywords, 'iso') or search_google_compliance(url, iso_keywords)

def check_pci_dss_firewall(url):
    return True

def check_pci_dss_default_passwords(url):
    return True

def check_pci_dss_compliance(https_compliant, url):
    return https_compliant and check_pci_dss_firewall(url) and check_pci_dss_default_passwords(url)

def scan_website(url): # Scanning the website for all the compilance checks and returning the result for GDPR, ISO27001, Dark Web Exposure Score
    global previous_results

    if url in previous_results:
        return previous_results[url] 
    result={
        "url": url,
        "https_compliant": False,
        "firewall_compliant": False,
        "default_passwords": False,
        "pci_dss_compliant": False,
        "dark_web_exposure_score": 0,
        "gdpr_compliant": False,
        "iso27001_compliant": False,
        "errors": []
    }

    if check_https(url):
        result["https_compliant"]= True
    else:
        result["errors"].append("Website does not use HTTPS") 
    
    response = get_website_content(url) 
    if response: 
        dark_web_keywords= ["breach", "hacked", "leaks", "compromise", "data theft", "data breach", "cyber attack", "cybersecurity incident", "security breach", "information leak"]
        dark_web_news_count= search_web_news(url, dark_web_keywords)
        result["dark_web_exposure_score"]= simulate_compliance_score(url, result["https_compliant"], dark_web_news_count)
        
        result["gdpr_compliant"] = check_gdpr_compliance(url)
        
        result["iso27001_compliant"] = check_iso27001_compliance(url)

        result["firewall_compliant"] = check_pci_dss_firewall(url)
        result["default_passwords"] = check_pci_dss_default_passwords(url)
        result["pci_dss_compliant"]= check_pci_dss_compliance(result["https_compliant"], url)
   
    previous_results[url] = result
    return result

@app.route('/') # Home Page
def index():
    return render_template('index.html')

@app.route('/scan', methods= ['POST']) # Scan the website
def scan():
    url = request.form['website']
    if not url.startswith("http"):
        url = "https://" + url
    
    result = scan_website(url)

    return render_template('results.html', result= result)

if __name__ == "__main__": # Run the Flask app
    app.run(debug= True)
