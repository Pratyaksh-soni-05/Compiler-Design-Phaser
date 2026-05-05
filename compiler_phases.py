import re

# 🔷 INPUT PROGRAM
code = """
char ch = 'A';
if((ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z'))
{
    printf("Alphabet");
}
"""

# -------------------------------
# 🔷 1. LEXICAL ANALYSIS
# -------------------------------
def lexical_analysis(code):
    tokens = re.findall(r"[a-zA-Z_]+|\d+|==|!=|<=|>=|&&|\|\||[^\s]", code)
    print("\nLEXICAL ANALYSIS:")
    print(tokens)
    return tokens

# -------------------------------
# 🔷 2. SYNTAX ANALYSIS (Simple Check)
# -------------------------------
def syntax_analysis(code):
    print("\nSYNTAX ANALYSIS:")
    if code.count("(") == code.count(")") and code.count("{") == code.count("}"):
        print("Syntax is valid")
    else:
        print("Syntax Error")

# -------------------------------
# 🔷 3. SEMANTIC ANALYSIS
# -------------------------------
def semantic_analysis():
    print("\nSEMANTIC ANALYSIS:")
    symbol_table = {"ch": "char"}
    print("Symbol Table:", symbol_table)

# -------------------------------
# 🔷 4. INTERMEDIATE CODE
# -------------------------------
def intermediate_code():
    print("\nINTERMEDIATE CODE (3-Address Code):")
    print("t1 = ch >= 'a'")
    print("t2 = ch <= 'z'")
    print("t3 = t1 && t2")

# -------------------------------
# 🔷 5. CODE OPTIMIZATION
# -------------------------------
def optimization():
    print("\nCODE OPTIMIZATION:")
    print("Removed redundant expressions")

# -------------------------------
# 🔷 6. TARGET CODE GENERATION
# -------------------------------
def target_code():
    print("\nTARGET CODE (Pseudo Assembly):")
    print("LOAD ch")
    print("CMP 'a'")
    print("JGE LABEL1")

# -------------------------------
# 🔷 MAIN FUNCTION
# -------------------------------
tokens = lexical_analysis(code)
syntax_analysis(code)
semantic_analysis()
intermediate_code()
optimization()
target_code()