import re, os, sys
import random
import subprocess
import shutil

import pprint
import argparse

import operators.power
import operators.logic


def randomvar():
    clist = [chr(i) for i in range(65, 123)]
    for i in clist:
        if not i.isalpha():
            clist.remove(i)
            continue
        if i.upper() == i.lower():
            clist.remove(i)
    for i in ["^", "\\", "`"]:
        try:
            clist.remove(i)
        except:
            pass
    length = random.randint(16, 24)
    out = ""
    for i in range(length):
        out += random.choice(clist + list("1234567890"))
    return "temp_" + out


static_template = """

using System;
using System.Collections;
using System.Collections.Generic;


namespace PsecTranspiled {{
	class Psec {{
		static void Main(string[] args) {{
		
{}
		}}
	}}
}}

"""


natives = """"""


default_indent = "          "
tab_indent = "  "


def process_line(line):
    partially_tokenized = line.split()

    if line.startswith("{"):
        try:
            line = "{" + process_line(line[1:])
        except:
            pass
    if line.endswith("}"):
        try:
            line = process_line(line[:-1]) + "}"
        except:
            pass
    line = line.split("//")[0].strip()
    while "  " in line:
        line = line.replace("  ", " ")
    line = re.sub("'([^\"]*)'", r'"\1"', line)

    isdef = re.findall(r"[^=]=[^=]", line)

    isstatements = re.findall(r"\b(\w+)\s+içinde\s+(\w+)\b", line)
    for couples in isstatements:
        line = line.replace(
            f"{couples[0]} içinde {couples[1]}", f"{couples[1]}.Contains({couples[0]})"
        )
    if not isstatements:
        isstatements = re.findall(r"\b(\w+)\s+sahip\s+(\w+)\b", line)
        for couples in isstatements:
            line = line.replace(
                f"{couples[0]} sahip {couples[1]}",
                f"{couples[0]}.Contains({couples[1]})",
            )
    ##print(isstatements)

    if line == "":
        return
    if "her" in partially_tokenized and "->" in partially_tokenized:
        if partially_tokenized.count("->") == 1:
            line = replace_foreach_pattern(line)
    elif line.startswith("başla") or line.startswith("bitir"):
        return
    elif line.startswith(":"):
        return default_indent + line[1:] + ":"
    elif line.startswith("yaz"):
        matched = re.findall(r"yaz\s+(.*)", line)[0]
        bracketsmatch = re.findall(r"\(([^()]+)\)", matched)
        # print(bracketsmatch)
        for i in bracketsmatch:
            matched = matched.replace(
                "(" + i + ")", "(" + process_line(i).strip() + ")"
            )
        line = "Console.WriteLine({});".format(matched)
    elif line.startswith("git"):
        line = re.sub(r"git\s+(.*)", r"goto \1;", line)
    elif line.startswith("eğer"):
        expression = re.findall(r"eğer\s+(.*)", line)[0]
        logical_expression, statement = re.findall(r"(.*)\s+ise\s+(.*)", expression)[0]
        logical_expression = native_transform(logical_expression)
        statement = process_line(statement).strip()

        if statement.startswith("{"):
            if len(statement) > 1:
                line = f"if ({logical_expression}){statement}"
            else:
                line = f"if ({logical_expression}){{"
        else:
            line = f"if ({logical_expression}) {{\n{tab_indent+statement}\n{default_indent}}}"
    elif line.startswith("değilse"):
        expression = re.findall(r"değilse\s+(.*)", line)[0]
        statement = expression.replace("değilse", "").strip()
        statement = process_line(statement).strip()
        if statement.startswith("{"):
            if len(statement) > 1:
                line = f"else {statement}"
            else:
                line = "else {"
        else:
            line = f"else {{\n{tab_indent+statement}\n{default_indent}}}"
            # line = f'else {{\n{tab_indent+statement}\n{default_indent}}}'
    elif line.startswith("ekle"):
        # syntax: ekle <variable> -> <target>
        variable, target = re.findall(r"ekle\s+(.*)\s+->\s+(.*)", line)[0]
        variable = native_transform(variable)
        line = "{}.Add({});".format(target, variable)
    elif isdef:
        right_statement = native_transform(line.split("=")[-1].strip())
        line = "= ".join(line.split("=")[:-1] + [right_statement])
        pattern = re.compile("sırala\([^()]*\)")
        sort_matches = sorted(pattern.findall(line), key=lambda x: -len(x))
        ##print(line, sort_matches)
        if sort_matches:
            if sort_matches[0].count("(") != sort_matches[0].count(")"):
                line += ";"
                return default_indent + line
            var_name = randomvar()
            list_name = sort_matches[0].split("sırala")[-1][1:-1]
            list_name = process_line(list_name).strip()
            line = line.replace(sort_matches[0], var_name)
            ##print(line, sort_matches[0])
            if "sırala" in line:
                line = process_line(line).strip()
            nline = (
                f"dynamic {var_name};\n{default_indent}{var_name} = {list_name};\n{default_indent}{var_name}.Sort();\n{default_indent}"
                + line
            )

            line = nline
        if not line.endswith(";"):
            line += ";"
    else:
        # needs further processing
        line = native_transform(line)
    return default_indent + line


def native_transform(line):
    line = line.strip()
    line = line.replace("  ", " ")
    if line == "[]":
        line = "new List<dynamic>()"
    # python-native type conversions

    if line.count("int ") + line.count("float ") + line.count("string ") > 3:
        raise Exception(
            "TypeConversion", f'Too many type conversions in one line: "{line}"'
        )
    final = False
    typeofop = ""

    match_strings = {
        r'(?<!")\bint\s+([^);]+(.))': "int",
        r'(?<!")\bfloat\s+([^);]+(.))': "float",
        r'(?<!")\bstring\s+([^);]+(.))': "string",
        r'(?<!")\bbool\s+([^);]+(.))': "bool",
    }

    for i in match_strings:
        final = re.findall(i, line)
        if final:
            final = final[0][0]
            if any(j in final for j in match_strings.values()):
                final = final.strip()
                final = native_transform(final)
            typeofop = match_strings[i]
            break
    if final:
        final = final.strip()
        if final.count(")") > final.count("(") and final.endswith(")"):
            final = final[:-1]
        if typeofop == "float":
            line = f'{typeofop}.Parse(string.Format("{{0}}", {final}))'
        elif typeofop == "int":  # or typeofop == "string":
            line = f'({typeofop})(float.Parse(string.Format("{{0}}", {final})))'
        elif typeofop == "string":
            # line = f"{final}.ToString()"
            line = f'string.Format("{{0}}", {final})'
        elif typeofop == "bool":
            line = f"(bool)({final})"
    ops = {
        "^": operators.power.replace_power_operator,
        " ve ": operators.logic.replace_and,
        " veya ": operators.logic.replace_or,
    }
    for i, j in ops.items():
        if i in line:
            line = j(line)
    if "oku" in line:  # change to regex
        var_name = line.replace("oku", "").strip()
        line = "{} = Console.ReadLine();".format(var_name)
    return line


def extract_variable_names(code):
    already_yielded = []
    to_yield = None
    for line in code.split("\n"):
        if len(line.strip()) > 0:
            if re.findall(r'([^"\']|^)[^=]=[^=](?!["\'])', line):
                to_yield = line.split("=")[0].strip()
            elif line.startswith("oku"):
                to_yield = line.replace("oku", "").strip()
            if to_yield in already_yielded:
                continue
            else:
                already_yielded.append(to_yield)
                to_yield = str(to_yield)
                if len(to_yield.split()) > 1:
                    continue
                yield to_yield


def process_code(code):
    collected = []
    for line in code.split("\n"):
        line = line.strip()
        rebuilt_line = process_line(line)
        if rebuilt_line:
            collected.append(rebuilt_line)
    if collected[-1].endswith(":"):
        collected.append(default_indent + ";")
    collected.insert(0, "\n")
    for line in natives.split("\n")[::-1]:
        collected.insert(1, default_indent + line)
    defnone = False

    colvars = sorted(list(extract_variable_names(code)), key=lambda x: -len(x))

    for variables in colvars:
        if str(variables) == "None":
            defnone = True
            continue
        collected.insert(0, default_indent + f"dynamic {variables};")
    if defnone:
        collected.insert(0, default_indent + f"dynamic None;")
        collected.insert(len(colvars), "\n" + default_indent + f"None = null;")
    scope_level = 0

    for index, item in enumerate(collected):
        for i in item:
            if i == "{":
                scope_level += 1
            elif i == "}":
                scope_level -= 1
        collected[index] = scope_level * default_indent + item
    return static_template.format("\n".join(collected))


def replace_foreach(match):
    code = process_line(match.group(4))
    variable = match.group(2)
    iterable = match.group(3)
    return f"foreach (dynamic {variable} in {iterable}) {code}"


def replace_foreach_pattern(expression):
    regex = r'([^"\']|^)her\s+(.*?)\s+->\s+(.*)\s+yap\s+(.*)(?!["\'])'
    return re.sub(regex, replace_foreach, expression)


class Transpiler:
    def __init__(self, code, output_file=None):
        self.source = code
        self.output_code = None
        self.output_file = output_file

    def transpile(self):
        self.output_code = process_code(self.source)

    def compile(self):
        if self.output_file == None:
            prompt = "compiler\\csc.exe transpiled.cs"
        else:
            prompt = f"compiler\\csc.exe -out:{self.output_file} transpiled.cs "
        if self.output_code is None:
            self.transpile()
        with open("transpiled.cs", "w+") as file:
            file.write(self.output_code)
        response = subprocess.run(
            prompt.split(),
            capture_output=True,
            shell=True,
        )  # text=True)
        if response.stderr == b'':
            print("Compilation successful!")
        else: print(response.stderr)
        os.remove("transpiled.cs")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Psec to C# transpiler/compiler")
    parser.add_argument("input", help="input file")
    parser.add_argument("output", help="output file")

    args = parser.parse_args()
    with open(args.input, "r", encoding="utf-8") as file:
        code = file.read()
    transpiler = Transpiler(code, args.output)
    transpiler.compile()
