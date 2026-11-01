# Manual de Instalación — Pronty Outlet

## 1. Requisitos

- Python 3.10+
- Node.js 20+
- npm
- Git

## 2. Clonar repositorio

```powershell
git clone https://github.com/carloscifuentesingsoft1560-cyber/pronty-outlet.git
cd pronty-outlet
```

## 3. Crear entorno virtual

```powershell
python -m venv venv
```

## 4. Activar entorno virtual

```powershell
.\venv\Scripts\Activate.ps1
```

## 5. Instalar dependencias Python

```powershell
pip install -r requirements.txt
```

## 6. Instalar dependencias frontend

```powershell
npm install
```

## 7. Crear `.env`

Ejemplo:

```env
DJANGO_SECRET_KEY=tu-clave-secreta
ALLOWED_HOSTS=127.0.0.1,localhost
QR_BASE_URL=http://127.0.0.1:8000
```

No subas `.env` a GitHub.

## 8. Migraciones

```powershell
python manage.py migrate
```

## 9. Verificación

```powershell
python manage.py check
```

## 10. Compilar SASS

Una vez:

```powershell
npm run sass
```

Modo desarrollo:

```powershell
npm run sass:watch
```

## 11. Ejecutar servidor

Local:

```powershell
python manage.py runserver
```

En red local:

```powershell
python manage.py runserver 0.0.0.0:8000
```

## 12. Accesos

Inicio:

```text
http://127.0.0.1:8000/
```

Administración:

```text
http://127.0.0.1:8000/admin/
```

## 13. Problemas comunes

### Django no inicia
Ejecuta:

```powershell
python manage.py check
```

### Estilos no actualizan
Ejecuta:

```powershell
npm run sass
```

y luego recarga con `Ctrl + F5`.

### QR no abre desde celular
Verifica:
- IP local;
- `QR_BASE_URL`;
- `ALLOWED_HOSTS`;
- firewall;
- servidor iniciado con `0.0.0.0:8000`.