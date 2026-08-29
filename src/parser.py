import os
import re
import html
from datetime import datetime

def parse_date(date_str):
    if not date_str:
        return None
    clean_str = date_str.replace('\u202f', ' ').replace('\xa0', ' ').strip()
    clean_str_no_tz = re.sub(r'\s+[A-Z]{3,4}$', '', clean_str)
    
    for fmt in [
        '%b %d, %Y, %I:%M:%S %p',
        '%b %d, %Y, %H:%M:%S',
        '%b %d, %Y %I:%M:%S %p',
        '%B %d, %Y, %I:%M:%S %p'
    ]:
        try:
            dt = datetime.strptime(clean_str_no_tz, fmt)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            pass
    return clean_str

def strip_tags(html_content):
    if not html_content:
        return ""
    text = re.sub(r'<[^>]+>', ' ', html_content)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parse_takeout_html(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Takeout HTML file not found at {filepath}")
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    cards = content.split('<div class="outer-cell')
    print(f"Parsing {len(cards)-1} cards from {filepath}...")
    
    chats = []
    
    for card_idx, card_html in enumerate(cards[1:], 1):
        if not card_html.strip() or 'mdl-grid' not in card_html:
            continue
            
        was_audio_input = '.wav' in card_html
        
        # Details URL & Thread ID
        details_match = re.search(r'href="(https://gemini\.google\.com/app/([a-f0-9]+))"', card_html, re.IGNORECASE)
        if details_match:
            details_url = details_match.group(1)
            thread_id = details_match.group(2)
        else:
            # Fallback URL pattern
            alt_match = re.search(r'href="(https://gemini\.google\.com/app/[^"]+)"', card_html, re.IGNORECASE)
            details_url = alt_match.group(1) if alt_match else ""
            thread_match = re.search(r'/app/([a-f0-9]+)', details_url)
            thread_id = thread_match.group(1) if thread_match else ""
            
        # Extract main content cell
        content_match = re.search(r'<div class="content-cell mdl-cell mdl-cell--6-col mdl-typography--body-1">(.*?)</div>', card_html, re.DOTALL)
        if not content_match:
            continue
            
        main_cell = content_match.group(1)
        
        # Strip audio links
        clean_cell = re.sub(r'<a[^>]+href="[^"]+\.wav"[^>]*>Audio included\.</a>\s*<br\s*/?>', '', main_cell, flags=re.IGNORECASE)
        clean_cell = re.sub(r'<a[^>]+href="[^"]+\.wav"[^>]*>Audio included\.</a>', '', clean_cell, flags=re.IGNORECASE)
        
        # Date pattern
        date_match = re.search(r'([A-Z][a-z]{2}\s+\d{1,2},\s+\d{4},\s+\d{1,2}:\d{2}:\d{2}[\s\u202f\xa0]*(?:AM|PM|a\.m\.|p\.m\.)(?:\s+[A-Z]{3,4})?)', main_cell)
        
        timestamp_raw = date_match.group(1) if date_match else None
        timestamp_iso = parse_date(timestamp_raw) if timestamp_raw else None
        
        prompt_text = ""
        response_html = ""
        
        if "Prompted" in clean_cell:
            parts = clean_cell.split("Prompted", 1)
            after_prompted = parts[1]
            
            if date_match:
                date_str = date_match.group(1)
                prompt_and_resp = after_prompted.split(date_str, 1)
                prompt_raw = prompt_and_resp[0]
                response_raw = prompt_and_resp[1] if len(prompt_and_resp) > 1 else ""
            else:
                prompt_raw = after_prompted
                response_raw = ""
                
            prompt_text = strip_tags(prompt_raw)
            response_html = response_raw.strip()
        else:
            prompt_text = ""
            response_html = clean_cell.strip()
            
        response_plain = strip_tags(response_html)
        
        media_files = re.findall(r'href="([^"]+\.(?:jpg|png|webp|pdf|csv|zip|xlsx|mp3|mp4|js|json))"', card_html, re.IGNORECASE)
        img_srcs = re.findall(r'src="([^"]+\.(?:jpg|png|webp))"', card_html, re.IGNORECASE)
        all_media = list(set(media_files + img_srcs))
        
        chats.append({
            'id': card_idx,
            'thread_id': thread_id or "",
            'timestamp_iso': timestamp_iso or "1970-01-01 00:00:00",
            'timestamp_raw': timestamp_raw or "",
            'prompt_text': prompt_text,
            'response_html': response_html,
            'response_plain': response_plain,
            'media_files': all_media,
            'details_url': details_url or "",
            'was_audio_input': 1 if was_audio_input else 0
        })
        
    print(f"Finished parsing. Total clean chats: {len(chats)}")
    return chats

if __name__ == '__main__':
    res = parse_takeout_html('/Users/austinrognes/Seagate-NAS/Gemini/MyActivity.html')
    print(f"Sample item: Thread ID: '{res[0]['thread_id']}' | {res[0]['timestamp_iso']} | Prompt: {res[0]['prompt_text'][:60]}")
