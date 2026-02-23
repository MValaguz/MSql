pyuic6 -x preferences_ui.ui -o preferences_ui.py
python trova_e_sostituisci.py "preferences_ui.py" ":/icons/icons/" "icons:"
pause