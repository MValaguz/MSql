#
# esempio di decoratore! il decoratore in questo caso è la funzione mio_decoratore che letteralmente ingloba la funzione saluta ma io mi referenzio comunque a saluta
#
def mio_decoratore(prova):
    def wrapper():
        print("Azioni prima della funzione...")        
        prova()  # chiama la funzione originale
        print("Azioni dopo la funzione.")
    return wrapper

# mio_decoratore amplifica la funzione saluta, ma io mi referenzio comunque a saluta
@mio_decoratore
def saluta():
    print("Ciao!")

# main
saluta()