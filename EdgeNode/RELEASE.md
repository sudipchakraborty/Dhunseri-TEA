# TeaVision Edge Windows release

## Build

From PowerShell in the project folder:

```powershell
.\.venv\Scripts\python.exe -m pip install pyinstaller
.\build_release.ps1
```

The build creates:

- `dist\TeaVisionEdge\TeaVisionEdge.exe`
- `dist\TeaVisionEdge-Windows.zip`

## Distribute

Send `TeaVisionEdge-Windows.zip`. The recipient should extract the complete
folder and run `TeaVisionEdge.exe`. Python is not required on their computer.
Do not send only the EXE because its `_internal` dependency folder is required.

Windows SmartScreen may show an unknown-publisher warning until the executable
is digitally code-signed. The target computer must be able to reach the RTSP
camera network address.

Runtime data is stored beside the EXE:

- `config\analysis_metrics.json`
- `config\camera.json`
- `data\inspection_history.db`
- `data\sample_images\`
