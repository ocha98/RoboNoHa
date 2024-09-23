import re

def cleaing_txt(txt: str) -> str:
    txt = re.sub(r'@([a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.)+[a-zA-Z]{2,}', '', txt) # BlueSkyのメンションを削除
    txt = re.sub(r'@[A-Za-z0-9_]+', '', txt) # Twitterのメンションを削除
    txt = re.sub(r'https?:\/\/[\w\/:%#\$&\?\(\)~\.=\+\-]+', '', txt) #URLを削除
    txt = re.sub(r'([a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.)+[a-zA-Z]{2,}\/[\w\/:%#\$&\?\(\)~\.=\+\-]+(...)?', '', txt) # BlueSkyの省略URLを削除
    txt = txt.replace('\n', ' ').strip()

    return txt
