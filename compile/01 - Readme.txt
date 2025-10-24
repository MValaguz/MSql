1) il file "02 - compile_MSql.bat" viene lanciato per primo!
   Prende i sorgenti di python da "Documenti\GitHub\MSql"
   e li compila in C:\MSql_exe\
   Di fatto il risultato di questo passaggio produce un eseguibile....
	 e i passaggi successivi servono solo per impacchettare il tutto
2) Applicare la firma (serve per far capire agli antivirus che non si tratta di un virus..vedi punto 4 di questo readme)	 
   In realtà questo punto non viene più svolto perché è bastato impostare in pyinstaller la direttiva upx=False
	 e in questo modo l'antivirus sembra non aver più dato problemi
3) utilizzando il programma "Inno setup" 
   e aprendo lo script che si trova in questa cartella, 
   è possibile creare un programma d'installazione 
   che poi verrà parcheggiato in C:\MSql_setup per essere reso disponibile a tutti gli utenti
4) firma degli exe; per impedire all'antivirus di vedere MSql come un virus, è necessario firmare gli exe digitalmente.
   per fare questo dare riferimento al documento "05 - Readme crea certificato.txt"   
	 Punto che non viene più eseguito come descritto al punto2

Al termine la dir C:\MSql_exe\ può essere eliminato e distribuito il contenuto di C:\MSql_setup 