from enum import Enum

class Separators(str, Enum):

    ARABIC : list = ["\n\n", "\n", ".", "،", "؟", "!", " ", ""],   
    ENGLISH: list = ["\n\n", "\n", ".", "!", "?",  " ", ""]


