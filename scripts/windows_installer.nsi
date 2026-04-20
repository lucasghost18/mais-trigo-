; NSIS script to package Mais Trigo
; Place the built files in dist\ before running makensis
!define APPNAME "MaisTrigo"
!define VERSION "1.0.0"
OutFile "${APPNAME}-Installer-${VERSION}.exe"
InstallDir "$PROGRAMFILES64\${APPNAME}"
Page directory
Page instfiles

Section "Install"
  SetOutPath "$INSTDIR"
  ; copy all files from dist\ into the install dir (dist must exist when compiling)
  File /r "dist\\*"

  ; create Start Menu folder and shortcut
  CreateDirectory "$SMPROGRAMS\\${APPNAME}"
  CreateShortCut "$SMPROGRAMS\\${APPNAME}\\${APPNAME}.lnk" "$INSTDIR\\run.exe"

  ; write uninstaller
  WriteUninstaller "$INSTDIR\\Uninstall.exe"
SectionEnd

Section "Uninstall"
  Delete "$SMPROGRAMS\\${APPNAME}\\${APPNAME}.lnk"
  RMDir "$SMPROGRAMS\\${APPNAME}"
  Delete "$INSTDIR\\run.exe"
  Delete "$INSTDIR\\Uninstall.exe"
  RMDir "$INSTDIR"
SectionEnd
