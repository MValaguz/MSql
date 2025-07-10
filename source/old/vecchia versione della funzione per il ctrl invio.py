def slot_ctrl_invio(self):
        """
           L'utente ha premuto CTRL+Invio: viene ricercata l'istruzione dove il cursore di testo è attualmente posizionato
           e viene inviata all'esecutore. Se l'utente ha selezionato del testo, viene eseguito il testo selezionato; questo
           per mantenere un comportamento coerente con l'esecuzione tramite F5.
        """
        # funzione interna creata con CoPilot che dato testo sql e posizione del cursore, restituisce istruzione corrente con posizione di 
        # riga iniziale e finale (caso in cui l'istruzione sia terminata da ; o da /)
        def extract_statement_with_positions_comma_slash(sql, cursor_position):            
            pattern = re.compile(r'(?:SELECT.*?[;/]|INSERT.*?[;/]|UPDATE.*?[;/]|DELETE.*?[;/])', re.DOTALL | re.IGNORECASE)                                     

            matches = list(pattern.finditer(sql))
            for match in matches:
                start, end = match.span()
                if start <= cursor_position <= end:
                    start_line = sql[:start].count('\n') + 1
                    end_line = sql[:end].count('\n')
                    return match.group(), start_line, end_line
            return '', 0, 0

        # funzione interna creata con CoPilot che dato testo sql e posizione del cursore, restituisce posizione di inizio e fine dell'istruzione, riga inizio e di fine
        # funzione che viene usata nel caso NON si stata trovata istruzione che termina con ; o /
        def extract_statement_with_positions_space(sql_string, cursor_position):
            # Pattern per ricercare le istruzioni SQL
            v_pattern = re.compile(r'(SELECT|INSERT|UPDATE|DELETE).*?(?=SELECT|INSERT|UPDATE|DELETE|$)', re.DOTALL | re.IGNORECASE)
            
            v_matches = list(v_pattern.finditer(sql_string))
            # Scorro la lista dei risultati
            for v_match in v_matches:        
                # Se trovo il risultato all'interno della posizione del cursore...
                if v_match.start() <= cursor_position <= v_match.end():
                    # Imposto posizione di inizio e fine            
                    v_start_pos = v_match.start()
                    v_end_pos = v_match.end()            
                    # Ricerco su quale riga è la posizione di inizio
                    v_riga_inizio = 0
                    v_posizione = -1
                    for c in sql_string:              
                        v_posizione += 1
                        if c == chr(10):
                            v_riga_inizio += 1
                        if v_posizione == v_start_pos:
                            break
                    # Ricerco su quale riga è la posizine di fine
                    v_riga_fine = 0
                    v_posizione = -1
                    for c in sql_string:              
                        v_posizione += 1
                        if c == chr(10):
                            v_riga_fine += 1
                        if v_posizione == v_end_pos:
                            break            
                    # Esco con i risultati
                    return v_start_pos, v_end_pos, v_riga_inizio, v_riga_fine
            
            return None, None, None, None

        ###
        # inizio della funzione principale
        ###

        # se indicato dalla preferenza, prima di partire ad eseguire, pulisco l'output
        if o_global_preferences.auto_clear_output:
            self.slot_clear('OUT')
        
        # controllo se utente ha selezionato del testo specifico che vuole eseguire
        v_istruzione = self.e_sql.selectedText()                
        if v_istruzione is not None and v_istruzione != '':            
            # eseguo l'istruzione selezionata                          
            self.esegui_istruzione(v_istruzione, False)        
        # ... altrimenti....
        else:
            # prendo posizione cursore in riga e colonna
            v_pos_line, v_pos_column = self.e_sql.getCursorPosition()
            # imposto var generali
            self.v_offset_numero_di_riga = 0
            # prendo posizione attuale del cursore (relativa!)
            v_pos_relativa_cursore = self.e_sql.SendScintilla(self.e_sql.SCI_GETCURRENTPOS)
            # richiamo funzione interna per estrazione dell'istruzione sql (istruzione che termina con ; o /) e delle relative posizioni di riga
            v_istruzione, v_start_line, v_end_line = extract_statement_with_positions_comma_slash(self.e_sql.text(), v_pos_relativa_cursore)                
            # correggo posizioni riga
            if v_end_line < v_start_line:
                v_end_line = v_start_line
            else:
                v_start_line -= 1
                v_end_line += 1        
            
            # se trovata istruzione che terminava con ;            
            if v_istruzione != '':                
                # eventuale punto e virgola e spazi finali vengono tolti
                v_istruzione = v_istruzione.rstrip('; ')                                                
                # eventuale slash e spazi finali vengono tolti
                v_istruzione = v_istruzione.rstrip('/ ')                                      
                # eseguo l'istruzione                            
                self.esegui_istruzione(v_istruzione, False)        
                # seleziono il testo per evidenziare l'istruzione che è stata eseguita                                                            
                if v_start_line < v_end_line:                
                    self.e_sql.setSelection(v_start_line, 0, v_end_line, -1)                           
            # .. altrimenti
            else:
                # se non trovato nulla --> provo a fare la ricerca di un'istruzione usando come delimitatori le parole chiave INSERT,UPDATE,DELETE,SELECT
                # da notare come la stringa venga passata aggiungendo un ritorno a capo in fondo...questo perché se cursore è su ultima istruzione non dava le posizioni corrette
                v_pos_start, v_pos_end, v_start_line, v_end_line = extract_statement_with_positions_space(self.e_sql.text()+chr(10), v_pos_relativa_cursore)                        
                if v_pos_start != None and v_pos_end != None:
                    v_istruzione = self.e_sql.text()[v_pos_start:v_pos_end]                    
                    if v_istruzione != '' and v_istruzione is not None:
                        # eventuale punto e virgola e spazi finali vengono tolti
                        v_istruzione = v_istruzione.rstrip('; ')                                                
                        # eseguo l'istruzione                           
                        self.esegui_istruzione(v_istruzione, False)        
                        # evidenzio il testo dell'istruzione                                                                                                    
                        self.e_sql.setSelection(v_start_line, 0, v_end_line, -1)                           
                    else:
                        # altrimenti errore
                        message_error(QCoreApplication.translate('MSql_win2','No statement found as SELECT, INSERT, UPDATE, DELETE!'))
                        return 'ko'                                    
                else:
                    # altrimenti errore
                    message_error(QCoreApplication.translate('MSql_win2','No statement found as SELECT, INSERT, UPDATE, DELETE!'))
                    return 'ko'                             