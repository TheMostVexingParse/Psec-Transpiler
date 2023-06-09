import re

def replace_and(expression):
    regex = r'([^"\']|^)([^\s"\'&]+)\s+ve\s+([^\s"\'&]+)(?!["\'])'
    return re.sub(regex, r" \2 && \3", expression)
def replace_or(expression):
    regex = r'([^"\']|^)([^\s"\'&]+)\s+veya\s+([^\s"\'&]+)(?!["\'])'
    return re.sub(regex, r" \2 || \3", expression)

# Examples:
if __name__ == '__main__':
    print(replace_and('a = "a ve b"'))  # a = "a and b" (unchanged)
    print(replace_and('a = a ve b'))  # a = a & b

    print(replace_or('a = "a veya b"'))  # a = "a and b" (unchanged)
    print(replace_or('a = a veya b'))  # a = a & b
