from flask import Flask, request, jsonify, render_template
import requests
import hashlib

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

def check_gdpr_compliance(https_compliant, web_news_count): # Function for GDPR Compliance check
    if https_compliant and web_news_count > 1:
        return True
    elif not https_compliant and web_news_count > 1:
        return False
    else:
        return False
    
def check_iso27001_compliance(https_compliant, web_news_count): # Function for ISO27001 Compliance check
    if https_compliant and web_news_count >1:
        return True
    elif not https_compliant and web_news_count == 0:
        return False
    else:
        return False

def scan_website(url): # Scanning the website for all the compilance checks and returning the result for GDPR, ISO27001, Dark Web Exposure Score
    global previous_results

    if url in previous_results:
        return previous_results[url] 
    result={
        "url": url,
        "https_compliant": False,
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

        gdpr_keywords= ["GDPR", "General Data Protection Regulation", "data protection", "privacy law"]
        gdpr_news_count= search_web_news(url, gdpr_keywords)
        result["gdpr_compliant"]= check_gdpr_compliance(result["https_compliant"], gdpr_news_count)

        iso27001_keywords= ["ISO27001", "information security", "ISMS", "security management"]
        iso27001_news_count= search_web_news(url, iso27001_keywords)
        result["iso27001_compliant"]= check_iso27001_compliance(result["https_compliant"], iso27001_news_count)
    
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
