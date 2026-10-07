import json

def run_test():
    data = {'url': None, 'type': 'image', 'format': 'illustration', 'duration': 2000, 'text': 'dfrge', 'lien': 'https://store.steampowered.com/app/2445980/GRebels/'}
    
    url = data.get('url')
    lien = data.get('lien')
    text = data.get('text')
    media_type = data.get('type')
    duration_raw = data.get('duration')
    try:
        duration = int(duration_raw) if duration_raw is not None else None
    except ValueError:
        duration = None

    provider_result = {}
    if lien:
        # simulate process_link
        provider_result = {'type': 'web', 'embed_url': 'https://store.steampowered.com/app/2445980/GRebels/', 'web_size': (1632, 918), 'is_generic_web': True}
        
        if "url" in provider_result: url = provider_result["url"]
        if "type" in provider_result: media_type = provider_result["type"]
        if "lien" in provider_result: lien = provider_result["lien"]
        if "top_text" in provider_result: top_text = provider_result["top_text"]

    is_generic_web = provider_result.get("is_generic_web", False)
    if is_generic_web and not duration:
        duration = 2000
        
    if ((lien and not is_generic_web) or media_type in ('video', 'audio')) and duration == 2000:
        duration = None
        
    print(f"DEBUG: Processed duration is: {duration}")

run_test()
