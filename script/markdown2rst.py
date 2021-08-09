# https://github.com/miyakogi/m2r
from m2r import parse_from_file
output = parse_from_file('../README.md')
with open('../README.rst', 'w', encoding='utf-8') as f:
    f.write(output)