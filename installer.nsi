; ZeroLog Viewer NSIS Installer Script
; This script creates a Windows installer for ZeroLog Viewer

!include "MUI2.nsh"

; Version info (will be replaced during build)
!define VERSION "0.2.0"
!define PRODUCT_NAME "ZeroLog Viewer"
!define PRODUCT_PUBLISHER "ZeroLog Viewer Team"
!define PRODUCT_WEB_SITE "https://github.com/ashajkofci/zerolog_viewer"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

; Application settings
Name "${PRODUCT_NAME} ${VERSION}"
OutFile "zerolog-viewer-${VERSION}-installer.exe"
InstallDir "$PROGRAMFILES64\ZeroLog Viewer"
InstallDirRegKey HKLM "Software\${PRODUCT_NAME}" "InstallDir"
RequestExecutionLevel admin

; Modern UI Configuration
!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; Welcome page
!insertmacro MUI_PAGE_WELCOME

; License page (optional, can be removed if no license file)
; !insertmacro MUI_PAGE_LICENSE "LICENSE"

; Components page
!insertmacro MUI_PAGE_COMPONENTS

; Directory page
!insertmacro MUI_PAGE_DIRECTORY

; Instfiles page
!insertmacro MUI_PAGE_INSTFILES

; Finish page
!define MUI_FINISHPAGE_RUN "$INSTDIR\zerolog_viewer.exe"
!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\README.txt"
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Language
!insertmacro MUI_LANGUAGE "English"

; Installer Sections
Section "!ZeroLog Viewer (Required)" SEC01
  SectionIn RO
  
  ; Set output path to the installation directory
  SetOutPath "$INSTDIR"
  
  ; Copy the executable
  File "dist\zerolog_viewer.exe"
  
  ; Create a simple README
  FileOpen $0 "$INSTDIR\README.txt" w
  FileWrite $0 "ZeroLog Viewer - JSONL Log Viewer$\r$\n"
  FileWrite $0 "$\r$\n"
  FileWrite $0 "A cross-platform GUI application for viewing and analyzing JSONL (JSON Lines) log files.$\r$\n"
  FileWrite $0 "$\r$\n"
  FileWrite $0 "To run the application, use the Start Menu shortcut or run zerolog_viewer.exe$\r$\n"
  FileWrite $0 "$\r$\n"
  FileWrite $0 "For more information, visit: ${PRODUCT_WEB_SITE}$\r$\n"
  FileClose $0
  
  ; Write registry keys for uninstaller
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninstall.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\zerolog_viewer.exe"
  
  ; Write install directory to registry
  WriteRegStr HKLM "Software\${PRODUCT_NAME}" "InstallDir" "$INSTDIR"
  
  ; Create uninstaller
  WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

Section "Start Menu Shortcuts" SEC02
  CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
  CreateShortcut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk" "$INSTDIR\zerolog_viewer.exe"
  CreateShortcut "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall.lnk" "$INSTDIR\uninstall.exe"
SectionEnd

Section "Desktop Shortcut" SEC03
  CreateShortcut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\zerolog_viewer.exe"
SectionEnd

Section "Associate .jsonl files" SEC04
  ; Register .jsonl file association
  WriteRegStr HKCR ".jsonl" "" "ZeroLogViewer.jsonl"
  WriteRegStr HKCR "ZeroLogViewer.jsonl" "" "JSONL Log File"
  WriteRegStr HKCR "ZeroLogViewer.jsonl\DefaultIcon" "" "$INSTDIR\zerolog_viewer.exe,0"
  WriteRegStr HKCR "ZeroLogViewer.jsonl\shell\open\command" "" '"$INSTDIR\zerolog_viewer.exe" "%1"'
  
  ; Notify Windows of the file association change
  System::Call 'shell32.dll::SHChangeNotify(i, i, i, i) v (0x08000000, 0, 0, 0)'
SectionEnd

; Section descriptions
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC01} "Install the ZeroLog Viewer application (required)."
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC02} "Create shortcuts in the Start Menu."
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC03} "Create a shortcut on the Desktop."
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC04} "Associate .jsonl files with ZeroLog Viewer."
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; Uninstaller Section
Section "Uninstall"
  ; Remove files
  Delete "$INSTDIR\zerolog_viewer.exe"
  Delete "$INSTDIR\README.txt"
  Delete "$INSTDIR\uninstall.exe"
  
  ; Remove shortcuts
  Delete "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk"
  Delete "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall.lnk"
  RMDir "$SMPROGRAMS\${PRODUCT_NAME}"
  Delete "$DESKTOP\${PRODUCT_NAME}.lnk"
  
  ; Remove file associations
  DeleteRegKey HKCR ".jsonl"
  DeleteRegKey HKCR "ZeroLogViewer.jsonl"
  
  ; Notify Windows of the file association change
  System::Call 'shell32.dll::SHChangeNotify(i, i, i, i) v (0x08000000, 0, 0, 0)'
  
  ; Remove registry keys
  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "Software\${PRODUCT_NAME}"
  
  ; Remove installation directory
  RMDir "$INSTDIR"
SectionEnd
