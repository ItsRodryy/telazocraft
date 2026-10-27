param([string]$Minecraft = (Join-Path $env:APPDATA '.minecraft'))
$ErrorActionPreference = 'Stop'
$OutputEncoding = [Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
try {
    $datos = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'paquete.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $destinoJuego = [IO.Path]::GetFullPath($Minecraft)
    if ($destinoJuego -eq [IO.Path]::GetPathRoot($destinoJuego)) { throw 'Elige la carpeta del juego, no la raiz de una unidad.' }
    $origenMods = Join-Path $PSScriptRoot 'mods'
    foreach ($mod in $datos.mods.PSObject.Properties) {
        if ([IO.Path]::GetFileName($mod.Name) -ne $mod.Name) { throw 'Nombre de mod no valido.' }
        if ((Get-FileHash -LiteralPath (Join-Path $origenMods $mod.Name) -Algorithm SHA256).Hash -ne $mod.Value) { throw ('Mod danado: ' + $mod.Name) }
    }
    $jarCliente = ''
    if ($datos.instalador) {
        if ([IO.Path]::GetFileName($datos.instalador) -ne $datos.instalador) { throw 'Instalador no valido.' }
        $jarCliente = Join-Path $PSScriptRoot $datos.instalador
        if ((Get-FileHash -LiteralPath $jarCliente -Algorithm SHA256).Hash -ne $datos.sha256_instalador) { throw 'El instalador no coincide con su SHA-256.' }
    }
    New-Item -ItemType Directory -Path $destinoJuego -Force | Out-Null
    $destinoMods = [IO.Path]::GetFullPath((Join-Path $destinoJuego 'mods'))
    if (-not $destinoMods.StartsWith($destinoJuego.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Carpeta de mods fuera del juego.' }
    if ((Test-Path -LiteralPath $destinoMods) -and ((Get-Item -LiteralPath $destinoMods).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'La carpeta mods es un enlace. Elige una carpeta normal.' }
    if (Test-Path -LiteralPath $destinoMods) {
        $respaldoMods = Join-Path $destinoJuego ('mods_anterior_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fffffff'))
        if (-not ([IO.Path]::GetFullPath($respaldoMods)).StartsWith($destinoJuego.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Respaldo fuera del juego.' }
        Move-Item -LiteralPath $destinoMods -Destination $respaldoMods
        Write-Host ('Mods anteriores guardados en ' + $respaldoMods)
    }
    New-Item -ItemType Directory -Path $destinoMods -Force | Out-Null
    foreach ($mod in $datos.mods.PSObject.Properties) { Copy-Item -LiteralPath (Join-Path $origenMods $mod.Name) -Destination $destinoMods }
    if ($jarCliente) {
        $candidatosJava = @()
        foreach ($comandoJava in @(Get-Command java.exe -All -ErrorAction SilentlyContinue)) { $candidatosJava += $comandoJava.Source }
        $raicesJava = @((Join-Path $env:APPDATA '.minecraft/runtime'), (Join-Path $env:LOCALAPPDATA '.minecraft/runtime'), (Join-Path $env:APPDATA '.tlauncher/runtime'), (Join-Path $env:APPDATA '.tlauncher/jvms'), (Join-Path $destinoJuego 'runtime'))
        foreach ($carpetaJava in $raicesJava) {
            if (Test-Path -LiteralPath $carpetaJava) { $candidatosJava += @(Get-ChildItem -LiteralPath $carpetaJava -Filter java.exe -File -Recurse -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName) }
        }
        foreach ($carpetaJava in @((Join-Path $env:ProgramFiles 'Microsoft'), (Join-Path $env:ProgramFiles 'Eclipse Adoptium'), (Join-Path $env:ProgramFiles 'Java'))) {
            if (Test-Path -LiteralPath $carpetaJava) { $candidatosJava += @(Get-ChildItem -LiteralPath $carpetaJava -Filter java.exe -File -Recurse -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName) }
        }
        $javaCliente = ''
        foreach ($candidatoJava in @($candidatosJava | Select-Object -Unique)) {
            $pruebaJava = [Diagnostics.Process]::new()
            $pruebaJava.StartInfo.FileName = $candidatoJava
            $pruebaJava.StartInfo.Arguments = '-version'
            $pruebaJava.StartInfo.UseShellExecute = $false
            $pruebaJava.StartInfo.CreateNoWindow = $true
            $pruebaJava.StartInfo.RedirectStandardError = $true
            $pruebaJava.StartInfo.RedirectStandardOutput = $true
            $null = $pruebaJava.Start()
            $salidaJava = $pruebaJava.StandardError.ReadToEnd() + $pruebaJava.StandardOutput.ReadToEnd()
            $pruebaJava.WaitForExit(); $pruebaJava.Dispose()
            if ($salidaJava -match ('version "' + $datos.java + '(?:\.|"|-)')) { $javaCliente = $candidatoJava; break }
        }
        if (-not $javaCliente) { throw ('No se encontro Java ' + $datos.java + '. Instalalo y vuelve a ejecutar Instalar.bat.') }
        $javaSinVentana = Join-Path (Split-Path -Parent $javaCliente) 'javaw.exe'
        if (-not (Test-Path -LiteralPath $javaSinVentana)) { $javaSinVentana = $javaCliente }
        Write-Host 'Instalando NeoForge; espera a que termine...'
        $procesoCliente = Start-Process -FilePath $javaSinVentana -ArgumentList @('-jar', ('"' + $jarCliente + '"'), '--install-client', ('"' + $destinoJuego + '"')) -WorkingDirectory $destinoJuego -WindowStyle Hidden -PassThru -Wait
        if ($procesoCliente.ExitCode -ne 0) {
            Write-Host 'La instalacion silenciosa fallo. Completa Install client en la ventana que se abrira.'
            Start-Process -FilePath $javaSinVentana -ArgumentList @('-jar', ('"' + $jarCliente + '"')) -WorkingDirectory $destinoJuego
            exit 1
        }
    }
    Write-Host 'Paquete instalado. Abre el launcher y elige la version indicada en LEEME.txt.'
    exit 0
} catch { Write-Host ('Error: ' + $_.Exception.Message); exit 1 }
