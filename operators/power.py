import re

def replace_power(match):
    operand1 = match.group(2)
    operand2 = match.group(3)
    return f"Math.Pow({operand1}, {operand2})"

def replace_power_operator(expression):
    regex = r'([^"\']|^)(\([^()]+\)|[^\s()+]+)\s*\^\s*(\([^()]+\)|[^\s()+]+)(?!["\'])'
    return re.sub(regex, replace_power, expression)


if __name__ == '__main__':
    # Tests:
    print(replace_power_operator('a ^ b + 3'))  # Math.Pow(a, b) + 3
    print(replace_power_operator('a ^ (b + 3)'))  # Math.Pow(a, (b+3))
    print(replace_power_operator('(a+3) ^ b + 3'))  # Math.Pow((a+3), b) + 3
    print(replace_power_operator('(a+3) ^ (b+3)'))  # Math.Pow((a+3), (b+3))

    print(replace_power_operator('"(a+3) ^ (b+3)"'))  # Math.Pow((a+3), (b+3))

