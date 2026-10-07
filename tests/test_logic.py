def test():
    lien = "https://store.steampowered.com/"
    media_type = "web"
    is_generic_web = True
    duration = 2000
    DEFAULT_DURATION_BOT = 2000
    
    if ((lien and not is_generic_web) or media_type in ('video', 'audio')) and duration == DEFAULT_DURATION_BOT:
        duration = None
        
    print("Duration:", duration)

test()
