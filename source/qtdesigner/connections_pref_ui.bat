pyuic6 -x connections_pref_ui.ui -o connections_pref_ui.py
python trova_e_sostituisci.py "connections_pref_ui.py" ":/icons/icons/" "icons:"
pause