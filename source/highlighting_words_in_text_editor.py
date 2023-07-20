# -*- coding: utf-8 -*-

"""
 Creato da.....: Artemio Garza Reyna
 Piattaforma...: Python3.11 con libreria pyqt5
 Data..........: 18/05/2023
 Descrizione...: Questa classe è stata scaricata dal web a questa pagina
                 https://wiki.python.org/moin/PyQt/Python%20syntax%20highlighting
                 In pratica permette di evidenziare le parole chiave all'interno di un widget di testo, in base a regole definite dal programmatore.
                 In questo caso è stata modificata in modo che evidenzi le parole chiave del linguaggio PLSQL.
                 E' stata inoltre modificata in modo che correttamente gestisca i commenti multiriga.
                 
"""
from PyQt5 import QtCore, QtGui, QtWidgets

def format(color, style=''):
    """
       Return a QTextCharFormat with the given attributes.
    """
    _color = QtGui.QColor()
    _color.setNamedColor(color)

    _format = QtGui.QTextCharFormat()
    _format.setForeground(_color)
    if 'bold' in style:
        _format.setFontWeight(QtGui.QFont.Bold)
    if 'italic' in style:
        _format.setFontItalic(True)

    return _format

# Syntax styles that can be shared by all languages
PLSQL_STYLES = {
    'sql_key': format('blue'),
    'operator': format('red'),
    'brace': format('orange', 'bold'),
    'plsql_key': format('black', 'bold'),
    'proc_fun': format('blue','bold'),
    'string': format('brown'),
    'string2': format('darkMagenta'),
    'comment': format('darkGreen', 'italic'),    
    'numbers': format('magenta'),
}

"""
 ____  _       ____   ___  _     
|  _ \| |     / ___| / _ \| |    
| |_) | |     \___ \| | | | |    
|  __/| |___   ___) | |_| | |___ 
|_|   |_____| |____/ \__\_\_____|
                                 
"""
class PLSQL_Highlighter (QtGui.QSyntaxHighlighter):        
    sql_key = [
        'ACCESS',  'ADD',  'AFTER',  'ALL',  'ALTER',  'AND',  'ANY',  'AS',  'ASC',  'AT',  'AUDIT', 
        'AUTHID',  'BEFORE',  'BETWEEN',  'BFILE',  'BLOB',  'BY',  'CASCADE',  'CASE',  'CAST',  'CHAR', 'CHECK', 
        'CLOB',  'CLUSTER',  'COLUMN', 'COMMENT', 'COMMIT', 'COMPILE', 'COMPRESS', 'CONNECT', 'CONSTRAINT', 'CREATE', 
        'CURRENT', 'CURRVAL', 'DATABASE', 'DATE', 'DEBUG', 'DECIMAL', 'DEFAULT', 'DELETE', 'DISABLE', 'DISTINCT', 
        'DROP', 'EACH', 'ENABLE', 'EXCEPTIONS', 'EXCLUSIVE', 'EXECUTE', 'EXISTS', 'FILE', 'FLOAT', 'FOREIGN', 
        'FROM', 'GRANT', 'GROUP', 'HAVING', 'HEAP', 'IDENTIFIED', 'IMMEDIATE', 'IN', 'INCREMENT', 'INDEX', 'INITIAL', 
        'INITRANS', 'INNER', 'INSERT', 'INTEGER', 'INTERSECT', 'INTO', 'IS', 'ISOLATION', 'JOIN', 'KEY', 'LEVEL', 
        'LIKE', 'LINK', 'LOCK', 'LONG', 'MAXEXTENTS', 'MAXTRANS', 'MINEXTENTS', 'MINUS', 'MLSLABEL', 'MODE', 
        'MODIFY', 'NCLOB', 'NEXT', 'NEXTVAL', 'NOAUDIT', 'NOCOMPRESS', 'NOCOPY', 'NOT', 'NOWAIT', 'NULL', 'NUMBER', 
        'OF', 'OFFLINE', 'OLD', 'ON', 'ONLINE', 'OPTION', 'OR', 'ORDER', 'ORGANIZATION', 'OUTER', 'OVER', 'PARTITION', 
        'PCTFREE', 'PCTINCREASE', 'PCTUSED', 'PRIMARY', 'PRIOR', 'PRIVATE', 'PRIVILEGES', 'PUBLIC', 'QUOTA', 'RAW', 
        'REFERENCES', 'REFERENCING', 'RENAME', 'REPLACE', 'RESOURCE', 'REVOKE', 'ROLLBACK', 'ROW', 'ROWID', 'ROWLABEL', 
        'ROWNUM', 'ROWS', 'SELECT', 'SEQUENCE', 'SESSION', 'SET', 'SHARE', 'SIZE', 'SMALLINT', 'SOME', 'START',
        'STORAGE', 'SUCCESSFUL', 'SYNONYM', 'SYSDATE', 'TABLE', 'TABLESPACE', 'TEMPORARY', 'TO', 'TRIGGER', 'UNION', 
        'UNIQUE','UPDATE', 'UROWID', 'USER', 'VALIDATE', 'VALUES', 'VARCHAR','VARCHAR2', 'VIEW', 'WHENEVER', 'WHERE', 
        'WITH', 'XOR','BOOLEAN','TRUE','FALSE'
    ]

    plsql_key = [
        'ABORT','ACCEPT','Access_Into_Null','ARRAY','ASSERT','ASSIGN','AUTHORIZATION','BEGIN','BINARY_INTEGER','BODY', 
        'BULK','CHAR_BASE','CLOSE','COLAUTH','COLLECT','Collection_Is_Null','COLUMNS','CONSTANT','CRASH','CURSOR','Cursor_Already_Open', 
        'DATA_BASE','DAY','DBA','DEBUGOFF','DEBUGON','DECLARE','DEFINITION','DELAY','DELTA','DESC','DIGITS','DISPOSE','DO','Dup_Val_On_Index', 
        'ELSE','ELSIF','END','ENTRY','EXCEPTION','EXCEPTION_INIT','EXIT','EXTENDS','FETCH','FOR','FORALL','FORM','FOUND','FUNCTION', 
        'GENERIC','GOTO','HOUR','IF','INDICATOR','INTERFACE','INTERVAL','Invalid_Cursor','Invalid_Number','ISOPEN','JAVA','LIMITED','Login_Denied', 
        'LOOP','MINUTE','MONTH','NATURAL','NATURALN','NEW','NOTFOUND','Not_Logged_On','No_Data_Found','NUMBER_BASE','OCIROWID','OPAQUE','OPEN', 
        'OPERATOR','OTHERS','OUT','PACKAGE','PLS_INTEGER','POSITIVE','POSITIVEN','PRAGMA','PROCEDURE','Program_Error','RAISE','RANGE','REAL', 
        'RECORD','REF','RELEASE','REM','RESTRICT_REFERENCES','RETURN','REVERSE','ROWCOUNT','ROWTYPE','Rowtype_Mismatch','RUN','SAVEPOINT',
        'SCHEMA','SECOND','Self_Is_Null','SEPARATE','SPACE','SQL','SQLCODE','SQLERRM','STATEMENT','Storage_Error','Subscript_Beyond_Count', 
        'Subscript_Outside_Limit','SUBTYPE','Sys_Invalid_Rowid','TABAUTH','TASK','TERMINATE','THEN','TIME','Timeout_On_Resource','TIMESTAMP', 
        'Too_Many_Rows','TYPE','USE','Value_Error','WHEN','WHILE','WORK','WRITE','YEAR','Zero_Divide','ZONE'
    ]
    
    operators = [
        ':=',
        # Comparison
        '=', '!=', '<', '<=', '>', '>=',
        # Arithmetic
        '-', '/'        
    ]
    
    # sembra che non funzioni?!!!!!!!
    braces = ['\{', '\}', '\(', '\)', '\[', '\]']

    def __init__(self, parent: QtGui.QTextDocument) -> None:
        super().__init__(parent)
    
        rules = []

        # Keyword, operator, and brace rules
        rules += [(r'\b%s\b' % w, 0, PLSQL_STYLES['sql_key'])
            for w in PLSQL_Highlighter.sql_key]
        rules += [(r'\b%s\b' % w, 0, PLSQL_STYLES['plsql_key'])
            for w in PLSQL_Highlighter.plsql_key]
        rules += [(r'%s' % o, 0, PLSQL_STYLES['operator'])
            for o in PLSQL_Highlighter.operators]
        rules += [(r'%s' % b, 0, PLSQL_STYLES['brace'])
            for b in PLSQL_Highlighter.braces]

        # All other rules
        rules += [
            # 'procedure' followed by an identifier
            (r'\bPROCEDURE\b\s*(\w+)', 1, PLSQL_STYLES['proc_fun']),
            # 'function' followed by an identifier
            (r'\bFUNCTION\b\s*(\w+)', 1, PLSQL_STYLES['proc_fun']),

            # Numeric literals
            (r'\b[+-]?[0-9]+[lL]?\b', 0, PLSQL_STYLES['numbers']),
            (r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', 0, PLSQL_STYLES['numbers']),
            (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0, PLSQL_STYLES['numbers']),

            # Double-quoted string, possibly containing escape sequences
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, PLSQL_STYLES['string']),
            # Single-quoted string, possibly containing escape sequences
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, PLSQL_STYLES['string']),

            # Commenti di riga (da '--' fino a new line)
            (r'--[^\n]*', 0, PLSQL_STYLES['comment']),            
        ]

        # Build a QRegExp for each pattern
        self.rules = [(QtCore.QRegExp(pat), index, fmt)
            for (pat, index, fmt) in rules]

    def highlightBlock(self, text):
        """
           Apply syntax highlighting to the given block of text.
        """        
        # il testo in input viene convertito in maiuscolo
        v_testo = text.upper()

        # applica tutti i ruoli definiti sopra
        for expression, nth, format in self.rules:                
            index = expression.indexIn(v_testo, 0)                            
            while index >= 0:
                # We actually want the index of the nth match
                index = expression.pos(nth)
                length = len(expression.cap(nth))
                self.setFormat(index, length, format)
                index = expression.indexIn(v_testo, index + length)

        self.setCurrentBlockState(0)
        
        # applica il formato ai commenti multiriga
        startExpression = "/*"
        endExpression = "*/"
                
        startIndex = 0        
        if self.previousBlockState() != 1:
            startIndex = v_testo.find(startExpression)

        while startIndex >= 0:
            endIndex = v_testo.find(endExpression, startIndex)
            if endIndex == -1:
                self.setCurrentBlockState(1)
                commentLength = len(v_testo) - startIndex
            else:
                commentLength = endIndex - startIndex + len(endExpression)

            self.setFormat(startIndex, commentLength, PLSQL_STYLES['comment'])
            startIndex = v_testo.find(startExpression,startIndex + commentLength)        

# ------------------------------------------------------------------------------------------------------------------------------------
# TEST APPLICAZIONE (DA NOTARE COME VENGA CARICATO UN FILE DI TESTO CHE CONTIENE CODICE PLSQL...IN QUESTO CASO OP_ORDINI_PROD_WMS.PLB)
# ------------------------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":           
    # TEST CON LINGUAGGIO PL/SQL        
    app = QtWidgets.QApplication([])
    editor = QtWidgets.QPlainTextEdit()
    font = QtGui.QFont()
    font.setFamily("Courier")
    font.setPointSize(12)
    editor.setFont(font)
    highlight = PLSQL_Highlighter(editor.document())
    editor.show()

    # Load syntax.py into the editor for demo purposes
    infile = open('example\\OP_ORDINI_PROD_WMS.plb', 'r')
    editor.setPlainText(infile.read())

    app.exec_()            