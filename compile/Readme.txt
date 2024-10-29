1) il file "compile_MSql.bat" viene lanciato per primo 
   prende i sorgenti di python da "Documenti\GitHub\MSql"
   e li compila in C:\MSql_exe\
   Di fatto il risultato di questo passaggio produce un eseguibile....e il passaggio successivo serve solo per impacchettare il tutto
2) utilizzando il programma "Inno setup" 
   e aprendo lo script che si trova in questa cartella, 
   è possibile creare un programma d'installazione 
   che poi verrà parcheggiato in C:\MSql_setup per essere reso disponibile a tutti gli utenti
   
Al termine sia la dir C:\MSql_exe\ che C:\MSql_setup possono essere eliminate!

