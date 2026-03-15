@echo off
echo Starting Django server on all network interfaces...
echo This allows access from other devices on your network.
echo.
echo Server will be accessible at:
echo   - http://localhost:8000/
echo   - http://127.0.0.1:8000/
echo   - http://192.168.1.7:8000/ (or your local IP)
echo.
echo Press Ctrl+C to stop the server.
echo.
python manage.py runserver 0.0.0.0:8000

