echo off
rem Pulizia della directory di destinazione
rem rmdir o:\Install\MSql\ /S /Q
rem Pulizia della copia eseguibile in locale
rmdir c:\MSql\ /S /Q
pyinstaller MSql.spec
cd dist
rem xcopy MSql o:\Install\MSql\ /S /H /I
xcopy MSql c:\MSql\ /S /H /I
cd ..
rmdir dist /S /Q
rmdir build /S /Q
pause
