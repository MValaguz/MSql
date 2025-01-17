import re

v_stringa = """substr(REPLACE(REPLACE(REPLACE(Replace(Replace(Replace(descri, chr(13),chr(10)),chr(10),''),';',':'),'¿',null),'''',''),'"',NULL),1,35) descr"""

def fine_istruzione(p_stringa):
    # se istruzione è / --> allora termine istruzione
    if p_stringa == '/':
        return True
    # se istruzione finisce con ; e il punto e virgola però non è tra apici 
    v_reg = "^(?!.*(['\"].*;\1)).*;$"
    if re.match(v_reg, p_stringa):
        return True        

    return False

if fine_istruzione(v_stringa):
    print('istruzione con fine')
else:
    print('istruzione SENZA fine')