"""Parser"""

class Parser:
    """Parser"""
    @staticmethod
    def split(string, to_split, not_between=["()"]):
        """Splits a string"""
        strings = []
        previous_index = 0
        i = 0
        while i < len(not_between):
            if len(not_between[i]) != 2:
                del not_between[i]
            else:
                i += 1
        i = 0
        while i < len(string):
            if string[i:(i + len(to_split))] == to_split:
                strings.append(string[previous_index:i])
                previous_index = i + 1
            else:
                for characters in not_between:
                    if string[i] == characters[0]:
                        i += 1
                        count = 1
                        while i < len(string) and count > 0:
                            if string[i] == characters[0]:
                                count += 1
                            if string[i] == characters[1]:
                                count -= 1
                            if count > 0:
                                i += 1
                        break
            i += 1
        strings.append(string[previous_index:i])
        return strings
