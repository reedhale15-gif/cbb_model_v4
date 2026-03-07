import re

def team_key(name):

    name = name.lower()

    # normalize saint abbreviations safely
    name = re.sub(r"\bst\.\s", "saint ", name)
    name = re.sub(r"\bst\s", "saint ", name)

    # remove punctuation
    name = re.sub(r"[^\w\s]", "", name)

    # remove spaces
    name = name.replace(" ", "")

    return name
