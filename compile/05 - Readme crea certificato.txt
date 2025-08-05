COMANDI PER GESTIONE DEI CERTIFICATI DA ESEGUIRE TRAMITE PowerShell!!!

---
-- PERMETTE DI VISUALIZZARE ELENCO DEI CERTIFICATI (NEL CASO DI MSQL DOVREBBE ESSERE SOLO 1)
---
Get-ChildItem -Path Cert:\CurrentUser\My

---
-- ELIMINAZIONE DI TUTTI I CERTIFICATI RELATIVI A MSQL
---
$certs = Get-ChildItem -Path Cert:\CurrentUser\My | Where-Object { $_.Subject -like "*MSql*" }

foreach ($cert in $certs) {
    Remove-Item -Path $cert.PSPath
}

---
-- CREAZIONE DEL CERTIFICATO PERSONALE PER MSQL
---
New-SelfSignedCertificate `
  -Subject "CN=MSql" `
  -CertStoreLocation "Cert:\CurrentUser\My" `
  -FriendlyName "MSql" `
  -KeyLength 2048 `
  -NotAfter (Get-Date).AddYears(5) `
  -Type Custom `
  -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3") # EKU: Code Signing

---
-- Per applicare il certificato uso il programma DigiCertUtil.exe presente nella cartella di compilazione, 
-- Aperto il programma, visualizza elenco dei certificati che sono presenti e lo applico sia a MSql.exe presente in c:\MSql_exe che MSql_setup.exe
--