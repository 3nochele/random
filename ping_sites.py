import requests
import random
import time
import csv
import os
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

SITES_FILE = 'sites.txt'
SUMMARY_REPORT = 'report.csv'
PROBLEM_REPORT = 'detailed_status.csv'
MAX_WORKERS = 5 

SUB_PAGES = ['', '/about-us', '/contact-us']

def is_valid_url(url):
    # ইউআরএল-এ অবশ্যই ডট থাকতে হবে এবং কোনো স্পেস বা অদ্ভুত চিহ্ন (↑) থাকা যাবে না
    if '.' not in url or ' ' in url or '↑' in url:
        return False
    # স্লাশ বা ডট দিয়ে শুরু হওয়া লাইন বাদ দেওয়া
    if url.startswith(('/', '.', '#')):
        return False
    return True

def ping_url(original_url):
    url = original_url.strip()
    
    # ইনভ্যালিড লাইনগুলো শুরুতেই বাদ দেওয়া
    if not url or not is_valid_url(url):
        return None

    if not url.startswith('http'):
        formatted_url = 'http://' + url
    else:
        formatted_url = url
        
    if formatted_url.endswith('/'):
        formatted_url = formatted_url[:-1]
    
    target_url = f"{formatted_url}{random.choice(SUB_PAGES)}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}
    
    time.sleep(random.uniform(2, 5)) 
    
    try:
        response = requests.get(target_url, headers=headers, timeout=20, allow_redirects=True)
        final_url = response.url.lower()

        if len(response.history) > 0 and ("suspended" in final_url or "limit" in final_url or "notify" in final_url):
            # এখানে original_url রিটার্ন করছি যাতে আপনি ফাইল থেকে ঠিক ঐ লাইনটি খুঁজে পান
            return original_url, response.status_code, "Suspended"
        elif response.status_code == 200:
            return original_url, response.status_code, "Success"
        else:
            return original_url, response.status_code, f"Error_{response.status_code}"
    except Exception:
        return original_url, 0, "Invalid/Down"

def start_process():
    if not os.path.exists(SITES_FILE):
        print("sites.txt not found!")
        return

    with open(SITES_FILE, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    random.shuffle(urls)
    print(f"Checking sites from your list...")
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(executor.map(ping_url, urls))

    # ফলাফল ফিল্টার করা (None গুলো বাদ দেওয়া)
    results = [r for r in results if r is not None]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(PROBLEM_REPORT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Exact_URL_from_List", "Status_Code", "Issue_Type", "Checked_At"])
        for url, code, status in results:
            if status != "Success":
                writer.writerow([url, code, status, now])

    success_count = sum(1 for _, _, s in results if s == "Success")
    suspended_count = sum(1 for _, _, s in results if s == "Suspended")
    failed_count = len(results) - (success_count + suspended_count)

    file_exists = os.path.exists(SUMMARY_REPORT)
    with open(SUMMARY_REPORT, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Date", "Total", "Success", "Suspended", "Failed"])
        writer.writerow([now, len(results), success_count, suspended_count, failed_count])
            
    print("Process Finished. Problem list updated.")

if __name__ == "__main__":
    start_process()
