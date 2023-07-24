echo off
rem Pulizia della directory di destinazione
rmdir o:\Install\MSql\MSql10 /S /Q
rem Puliza della copia eseguibile in locale
rmdir c:\MGrep\MSql10 /S /Q
pyinstaller MSql.spec
cd dist
xcopy MSql o:\Install\MSql\MSql10\ /S /H /I
xcopy MSql c:\MSql\MSql10\ /S /H /I
cd ..
rmdir dist /S /Q
rmdir build /S /Q
pause
