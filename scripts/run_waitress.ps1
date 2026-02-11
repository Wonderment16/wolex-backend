param(
    [string]$ListenHost = "0.0.0.0",
    [int]$Port = 8000
)

python -m waitress --listen "$ListenHost`:$Port" wolex_backend.wsgi:application
