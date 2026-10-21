# run_dashboard.ps1 — executa o dashboard com PYTHONPATH configurado
$env:PYTHONPATH = $PSScriptRoot
& "$PSScriptRoot\.venv\Scripts\python.exe" -m streamlit run "$PSScriptRoot\dashboard\app.py"
