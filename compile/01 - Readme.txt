1) The file "02 - compile_MSql.bat" is launched first!
   It takes the Python sources from "Documents\GitHub\MSql"
   and compiles them in C:\MSql_exe\
   In fact, the result of this step produces an executable...
   and the subsequent steps are only used to package everything.
2) Apply the signature (this is used to let antivirus software know it's not a virus...see point 4 of this readme)
   In reality, this step is no longer performed because it was enough to set the upx=False directive in pyinstaller
   and this way the antivirus software seems to have no more problems.
3) Using the "Inno setup" program
   and opening the script found in this folder,
   it is possible to create an installation program
   which will then be parked in C:\MSql_setup to be made available to all users.
4) Signing the .exe files; To prevent antivirus software from identifying MSql as a virus, you must digitally sign the .exe files.
   To do this, refer to the document "05 - Readme create certificate.txt"
   This point is no longer executed as described in point 2.

After completing the C:\MSql_exe\ directory, you can delete it and distribute the contents of C:\MSql_setup.