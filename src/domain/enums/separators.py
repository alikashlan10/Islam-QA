from enum import Enum
from typing import List

class Separators(Enum):

    ARABIC : List = ["\n\n", "\n", ".", "،", "؟", "!", " ", ""],   
    ENGLISH: List = ["\n\n", "\n", ".", "!", "?",  " ", ""]


