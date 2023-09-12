# -*- mode: python -*-

#
# da notare come ('..\\source\\qtdesigner\\*.py','qtdesigner') sia stata sostituita da ('..\\source\\qtdesigner\\*.py','.') per funzionamento eseguibile dopo passaggio da Inno Setup
#

block_cipher = None


a = Analysis(['..\\source\\MSql_editor.py'],
             pathex=[],
             binaries=[],
             datas=[					
					('..\\source\\help\\*.*','help'),										
					('..\\source\\qtdesigner\\*.py','.')
			       ],
             hiddenimports=[],             
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='MSql',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False, 
		  icon='..\\source\\qtdesigner\\icons\\MSql.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='MSql')
