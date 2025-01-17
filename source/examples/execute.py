import re

sql = """
SELECT * FROM table1;
BEGIN
   INSERT INTO table2 (col1, col2)
   VALUES (val1, val2);
   UPDATE table3
   SET col1 = val1
   WHERE col2 = val2;
END;
CREATE OR REPLACE PACKAGE BODY package1 AS
   PROCEDURE proc1 IS
   BEGIN
      NULL;
   END proc1;
END package1;
CREATE TABLE table5 (
    id INT,
    name VARCHAR(100),
    created_at TIMESTAMP
);
DELETE FROM table4
WHERE col1 = val1;
"""

line_number = 2

def extract_statement_with_line_number(sql, line_number):
    pattern = re.compile(
        r'(?:SELECT.*?;|INSERT.*?;|UPDATE.*?;|DELETE.*?;|CREATE TABLE.*?\);|CREATE OR REPLACE PACKAGE BODY.*?END package1;|BEGIN.*?END;)', 
        re.DOTALL
    )

    matches = list(pattern.finditer(sql))
    lines = sql.splitlines()

    # Calcolare le posizioni iniziale e finale per ogni riga
    line_start_positions = [0]
    for line in lines:
        line_start_positions.append(line_start_positions[-1] + len(line) + 1)

    for match in matches:
        start, end = match.span()
        start_line = next(i for i, pos in enumerate(line_start_positions) if pos > start) - 1
        end_line = next(i for i, pos in enumerate(line_start_positions) if pos > end) - 1
        if start_line <= line_number <= end_line:
            return match.group(), start_line + 1, end_line + 1

    return None, None, None

statement, start_line, end_line = extract_statement_with_line_number(sql, line_number)
print("Statement containing cursor position:", statement)
print("Start line:", start_line)
print("End line:", end_line)
