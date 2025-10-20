# back-faberit-punto-cdv-v1

## crear y activar entorno virtual
```
 python3 -m venv venv
 source venv/bin/activate
```

## instalar dependencias
```
 pip install -r requirements.txt
```

## crear y ejecutar migraciones
```
 python manage.py makemigrations
 python manage.py migrate 
```

## crear superusuario
``` 
 python manage.py createsuperuser --email ceo@faberit.pe --username ceo@faberit.pe
```

## ejecutar servidor
```
 python manage.py runserver localhost:8080
```
