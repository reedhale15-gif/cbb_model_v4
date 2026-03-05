import re

def team_key(name):

    name = name.lower()

    # normalize abbreviations BEFORE punctuation removal
    name = name.replace("st.", "saint")
    name = name.replace("st ", "saint ")
    name = name.replace(" st", " saint")

    name = name.replace("colorado st", "colorado state")

    # remove punctuation
    name = re.sub(r"[^\w\s]", "", name)

    # collapse spaces
    name = "".join(name.split())

    return name.strip()
