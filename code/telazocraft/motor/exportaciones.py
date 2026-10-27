"""Paquete completo de cliente; solo escribe en exportaciones y caché de la app."""
import datetime
import hashlib
import json
import os
import re
import zipfile
from pathlib import Path
from . import modrinth,neoforge
from .util import descargar,archivar,huella,leer_json

BAT = r'''@echo off
setlocal
chcp 65001 >nul
set "PSModulePath=%SystemRoot%\System32\WindowsPowerShell\v1.0\Modules;%ProgramFiles%\WindowsPowerShell\Modules"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Instalar.ps1" %*
set "resultado=%errorlevel%"
if not defined TELAZOCRAFT_SIN_PAUSA pause
exit /b %resultado%
'''

def crear(servidor, progreso=lambda n,texto:None, cache_path=None):
    from ..common import ajustes
    d=servidor.datos
    carpeta=servidor.biblioteca.ruta('exportaciones',servidor.id);carpeta.mkdir(parents=True,exist_ok=True)
    key=hashlib.sha256(str(servidor.ruta).encode()).hexdigest()[:20]
    cache_path=cache_path or ajustes.ruta().parent/'mods'/key/'inventario.json'
    progreso(2,'Consultando mods compatibles')
    mods=modrinth.inventario(servidor,red=True,cache_path=cache_path) if d['tipo']!='vanilla' else []
    archivos={m['archivo']:servidor.ruta/'mods'/m['archivo'] for m in mods if m['lado']!='unsupported'}
    proyectos={m['proyecto'] for m in mods if m['lado']!='unsupported' and m.get('proyecto')}
    extras=[];vistos=set()
    def incluir(version):
        if version['id'] in vistos or version['project_id'] in proyectos:return
        vistos.add(version['id'])
        for dep in version.get('dependencies',[]):
            if dep['dependency_type']!='required' or dep.get('project_id') in proyectos:continue
            if dep.get('version_id'):v=modrinth.http_json(modrinth.API+'/version/'+dep['version_id'])
            else:
                opciones=modrinth.versiones(dep['project_id'],servidor)
                if not opciones:raise ValueError('Dependencia de cliente sin versión compatible')
                v=opciones[0]
            incluir(v)
        f=next((f for f in version['files'] if f.get('primary')),version['files'][0]);nombre=f['filename']
        if Path(nombre).name!=nombre or '/' in nombre or '\\' in nombre or not nombre.endswith('.jar'):raise ValueError('Nombre de mod inválido')
        ruta=carpeta/'cache'/nombre
        if not ruta.exists() or huella(ruta,'sha512')!=f['hashes']['sha512']:descargar(f['url'],ruta,f['hashes']['sha512'],'sha512')
        if nombre in archivos and huella(archivos[nombre],'sha512')!=f['hashes']['sha512']:raise ValueError('Mods duplicados en el paquete')
        archivos[nombre]=ruta;extras.append(ruta);proyectos.add(version['project_id'])
    for i,slug in enumerate(d.get('extras_cliente',[]) if d['tipo']!='vanilla' else []):
        progreso(5+i*15//max(1,len(d['extras_cliente'])),'Preparando extra: '+slug)
        opciones=modrinth.versiones(slug,servidor)
        if not opciones:raise ValueError('No hay una versión compatible de '+slug)
        incluir(opciones[0])
    jar=None
    if d['tipo']=='neoforge':
        progreso(22,'Verificando instalador de NeoForge')
        jar=neoforge.instalador(servidor,carpeta/'cache',lambda n,total:progreso(22+int(13*n/total) if total else 22,'Descargando NeoForge'))
    sello=datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S_%f')
    nombre=re.sub(r'[^\w -]','',servidor.nombre).strip().replace(' ','_') or servidor.id
    destino=carpeta/f'Paquete_{nombre}_{sello}.zip';temporal=destino.with_suffix('.zip.tmp')
    direccion=leer_json(servidor.biblioteca.raiz/'telazocraft.json',{}).get('direccion','')
    leeme=(f"{servidor.nombre} — Paquete para amigos\nMinecraft {d['version_mc']} · {d['tipo']} {d.get('version_loader','')} · Java {d['java_mayor']}\n\n"
        "1. Cierra Minecraft y el launcher. Descomprime TODO el paquete en una carpeta.\n"
        "2. Abre al menos una vez el launcher oficial o TLauncher y prepara la versión indicada.\n"
        "3. Ejecuta Instalar.bat. Usa %APPDATA%/.minecraft; si tu launcher usa otra carpeta,\n"
        '   arrastra esa carpeta sobre Instalar.bat o ejecuta Instalar.bat "RUTA".\n'
        "4. Elige el perfil de NeoForge en el launcher oficial. En TLauncher elige la misma\n"
        "   versión de NeoForge y la carpeta configurada (Ajustes → Directorio del juego).\n"
        "   Para vanilla elige la versión indicada de Minecraft; no se instala NeoForge.\n"
        "5. Abre Multijugador → Añadir servidor.\n"+('Dirección: '+direccion+'\n' if direccion else 'Pide la dirección al dueño del servidor.\n')+
        "\nEl instalador busca Java en PATH y en los runtimes del launcher oficial/TLauncher.\n"
        "Si falla la instalación silenciosa se abre el instalador normal: selecciona Install client\n"
        "y la misma carpeta del juego. Si falta Java, instala la versión indicada y repite.\n"
        "\nVolver atrás: cierra el juego, aparta la carpeta mods nueva y renombra la carpeta\n"
        "mods_anterior_<fecha> a mods. Los mundos, opciones y perfiles existentes se conservan.\n"
        "No copies estos archivos al servidor. No incluye cuentas ni mundos.\n")
    metadata={'minecraft':d['version_mc'],'neoforge':d.get('version_loader','') if jar else '',
              'java':d['java_mayor'],'instalador':jar.name if jar else '',
              'sha256_instalador':huella(jar) if jar else '', 'mods':{n:huella(p) for n,p in archivos.items()}}
    total=sum(p.stat().st_size for p in archivos.values())+(jar.stat().st_size if jar else 0);escrito=0
    with zipfile.ZipFile(temporal,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        for n,p in archivos.items():
            z.write(p,'mods/'+n);escrito+=p.stat().st_size;progreso(35+int(55*escrito/max(1,total)),'Empaquetando mods')
        if jar:z.write(jar,jar.name)
        z.writestr('Instalar.bat',BAT.replace('\n','\r\n').encode('utf-8'))
        z.write(Path(__file__).with_name('instalar_amigos.ps1'),'Instalar.ps1')
        z.writestr('paquete.json',json.dumps(metadata,ensure_ascii=False,indent=2).encode('utf-8'))
        z.writestr('LEEME.txt',leeme.encode('utf-8'))
    progreso(94,'Verificando paquete')
    with zipfile.ZipFile(temporal) as z:
        if z.testzip() is not None:raise ValueError('ZIP dañado')
    os.replace(temporal,destino)
    antiguos=sorted([*carpeta.glob('Paquete_*.zip'),*carpeta.glob('mods_cliente_*.zip')],key=lambda p:p.stat().st_mtime)
    for viejo in antiguos[:-3]:archivar(viejo,servidor.biblioteca.ruta('archivo','exportaciones',servidor.id))
    progreso(100,'Paquete verificado')
    return destino,{'servidor':len(archivos)-len(extras),'extras':len(extras),'excluidos':sum(m['lado']=='unsupported' for m in mods)}
