# Introducción a los Contenedores y Docker
## ¿Qué es un contenedor?
- Un contenedor es una unidad ligera y portable que empaqueta una aplicación y sus dependencias para ejecutarse de manera consistente en cualquier entorno
- Comparado con máquinas virtuales, los contenedores comparten el kernel del sistema operativo y son más eficientes en el uso de recursos

## ¿Qué es Docker?
- Plataforma que permite crear, ejecutar y gestionar contenedores de manera sencilla
- Utiliza imágenes y contenedores para facilitar la portabilidad de aplicaciones

## Componentes Claves de Docker
- Imágenes: Plantillas inmutables que contienen el sistema base y las dependencias necesarias
- Contenedores: Instancias en ejecución de una imagen
- Dockerfile: Archivo con instrucciones para crear imágenes personalizadas
- Docker Hub: Repositorio en la nube para almacenar imágenes
- Docker Engine: Motor que permite ejecutar los contenedores

## Verificar si Docker está instalado

Ejecutar el siguiente comando en la terminal:
```bash
docker --version
```
Si Docker está instalado, mostrará la versión actual. En caso contrario, deberá instalarse desde la documentación oficial. [Docker Desktop](https://docs.docker.com/desktop/) o [Cómo instalar y usar Docker en Ubuntu 22.04](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-22-04)

## Probar que Docker funciona correctamente

```bash
docker run hello-world
```
Este comando descarga y ejecuta un contenedor de prueba.

## Ejemplo

[Ejemplo de un Dockerfile básico](basico/Dockerfile)
[Archivo de prueba](basico/archivo_prueba.txt)

Para construir la imagen, ejecutar el siguiente comando en la misma carpeta donde se encuentra el Dockerfile:

```bash
docker build -t mi_imagen_prueba .
````
- `-t mi_imagen_prueba`: Asigna un nombre a la imagen
- `.` : Indica que el contexto de construcción es la carpeta actual

Verificar que la imagen se creó correctamente

```bash
docker images
```
### Crear un Contenedor a partir de la Imagen
Una vez creada la imagen, podemos ejecutar un contenedor basado en ella.

```bash
docker run --name mi_contenedor -it mi_imagen_prueba
```
- `--name mi_contenedor`: Asigna un nombre al contenedor
- `-it`: Permite una sesión interactiva
- `mi_imagen_prueba`: Especifica la imagen a usar

Este comando ejecutará `ls -l /app`, mostrando los archivos dentro del directorio `/app`

### Validar los Archivos Copiados dentro del Contenedor
Para verificar que `archivo_prueba.txt` está dentro del contenedor, podemos acceder a la terminal del contenedor y listar su contenido.

Acceder al contenedor en ejecución
```bash
docker run --name mi_contenedor -it mi_imagen_prueba bash
```

Dentro del contenedor, ejecutar:
```bash
ls -l /app
cat /app/archivo_prueba.txt
```

Esto debería mostrar el archivo copiado y su contenido.

Salir del contenedor
Para salir de la sesión interactiva, escribir:
```bash
exit
```

### Detener y Eliminar Contenedores

Si un contenedor está en ejecución y queremos detenerlo:

```bash
docker stop mi_contenedor
```
Para eliminarlo completamente:

```bash

docker rm mi_contenedor
```

Para eliminar la imagen creada:

```bash
docker rmi mi_imagen_prueba
```

Para eliminar todos los contenedores detenidos:

```bash
docker container prune
```

### Descargar y Ejecutar Imágenes desde Docker Hub
Docker Hub permite acceder a imágenes oficiales y personalizadas.

Buscar una imagen en Docker Hub
```bash
docker search ubuntu
```

Descargar una imagen sin ejecutarla

```bash
docker pull ubuntu:latest
```

Ejecutar un contenedor desde una imagen descargada

```bash
docker run -it ubuntu bash
```

Esto inicia una sesión interactiva dentro de un contenedor Ubuntu.


## Ejemplo desplegar FASTAPI

### 1. **Crear imagen y contenedor de docker docker**

- Crear imagen

```bash
docker build -t fastapi_app .
```

- Validar Imagen

```bash
docker images
```

- Crear contenedor

```bash
docker run --rm --name fastapi_cont -it -p 80:80 fastapi_app

```

# Desarrollo de Machine Learning en Contenedores

El desarrollo de modelos de Machine Learning (ML) enfrenta desafíos significativos al pasar del entorno de desarrollo a producción. La reproducibilidad, escalabilidad y portabilidad son aspectos críticos para garantizar el éxito del ciclo de vida del modelo. Los contenedores permiten abordar estos desafíos al proporcionar entornos aislados y consistentes.

## Componentes Claves del Desarrollo de ML en Contenedores

1. **Entorno de Desarrollo Aislado:** Garantiza que las dependencias y configuraciones del entorno sean consistentes entre diferentes máquinas.
2. **Docker y Docker Compose:** Herramientas fundamentales para crear, gestionar y orquestar contenedores.
3. **Gestión de Dependencias:** Uso de archivos `requirements.txt` para definir las bibliotecas necesarias.
4. **Versionamiento de Imágenes:** Mantener versiones de imágenes para garantizar la trazabilidad y reproducibilidad.
5. **Orquestación de Contenedores:** Herramientas como Kubernetes para entornos de producción a gran escala.
6. **Persistencia de Datos:** Montaje de volúmenes para mantener datos entre sesiones.
7. **Exposición de Modelos:** APIs para desplegar modelos y permitir su consumo desde aplicaciones externas.

## Ejemplo Básico de Desarrollo en Contenedores

### 1. **Dockerfile para un Proyecto de ML**

```dockerfile
# Imagen base con Python y bibliotecas de ML
FROM python:3.9-slim

# Copiar archivos del proyecto
WORKDIR /app
COPY . /app

# Instalar dependencias
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Comando por defecto
CMD ["python", "main.py"]
```

### 2. **Archivo de requerimientos del proyecto**

```
numpy
pandas
scikit-learn
fastapi
uvicorn
```

### 3. **Script de ML (main.py)**

```python
from fastapi import FastAPI
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier

app = FastAPI()

# Modelo simple de ejemplo
data = load_iris()
model = RandomForestClassifier()
model.fit(data.data, data.target)

@app.get("/predict")
def predict(sepal_length: float, sepal_width: float, petal_length: float, petal_width: float):
    prediction = model.predict([[sepal_length, sepal_width, petal_length, petal_width]])
    return {"prediction": int(prediction[0])}
```

### 4. **Archivo Docker-compose**``

```yaml
version: '3'  # Especifica la versión de Docker Compose que se está utilizando.

services:     # Define los servicios que se ejecutarán en contenedores Docker.
  ml_service: # Nombre del servicio, en este caso es un servicio para ML (Machine Learning).
    build: .  # Indica que Docker debe construir la imagen usando el Dockerfile ubicado en el directorio actual (".").
    
    ports:
      - "8000:80" 
      # Mapea el puerto 80 del contenedor al puerto 8000 del host.
      # Esto permite acceder a la aplicación en http://localhost:8000 mientras que internamente escucha en el puerto 80.

    volumes:
      - './app:/app' 
      # Monta el directorio local './app' en la ruta '/app' dentro del contenedor.
      # Esto permite que los cambios realizados en el código fuente local se reflejen inmediatamente en el contenedor (ideal para desarrollo).

    command: ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]
    # Define el comando que se ejecutará al iniciar el contenedor.
    # Aquí se usa `uvicorn` para iniciar una aplicación FastAPI (`main:app`).
    # --host 0.0.0.0: Permite que la aplicación sea accesible desde cualquier IP dentro de la red del contenedor.
    # --port 80: La aplicación se ejecutará en el puerto 80 dentro del contenedor.
    # --reload: Activa el modo de recarga automática, útil para entornos de desarrollo ya que reinicia el servidor si hay cambios en el código.

```

### 5. **Iniciar el Contenedor**

```bash
docker-compose up --build
```

Ingresar el URL en el buscador:

http://127.0.0.1:80/docs

Valores de referencia para probar el servicio:
  - sepal_length=5.1
  - sepal_width=3.5
  - petal_length=1.4
  - petal_width=0.2


# Desarrollo en contenedores
Desarrollar en contenedores ofrece ventajas significativas al proporcionar aislamiento de entornos, lo que evita conflictos de dependencias entre proyectos y garantiza que las aplicaciones se ejecuten de manera consistente en diferentes sistemas. Además, facilita la portabilidad, permitiendo que el mismo contenedor funcione sin modificaciones en cualquier entorno, ya sea local, en servidores o en la nube. Los contenedores también mejoran la escalabilidad y simplifican los flujos de trabajo de integración y despliegue continuo (CI/CD), optimizando la gestión de recursos y el mantenimiento del software.

Implementar JupyterLab en un contenedor maximiza estos beneficios al crear un entorno de desarrollo aislado, reproducible y fácil de desplegar. Esto permite experimentar con diferentes bibliotecas y versiones sin afectar el sistema principal, facilita la colaboración en equipos de ciencia de datos y simplifica la configuración de entornos complejos. Además, es ideal para entornos en la nube, ya que permite escalar instancias de JupyterLab según la demanda, manteniendo la flexibilidad y la eficiencia operativa.


### Ventajas y Desventajas de UV y Docker en Ciencia de Datos y MLOps

En el ámbito de la ciencia de datos y MLOps, el uso de contenedores mediante Docker se ha consolidado como una práctica fundamental para unificar dependencias y reducir la fricción en los despliegues. Por otro lado, manejadores de dependencias como UV buscan mantener la cohesión en el desarrollo de aplicaciones, especialmente en entornos basados en Python. Ambos enfoques presentan ventajas y desventajas que conviene analizar para determinar su idoneidad en distintos contextos.

Docker ofrece una serie de ventajas notables. Su principal fortaleza radica en la portabilidad, ya que permite ejecutar aplicaciones de manera consistente en cualquier entorno, sea local, en servidores o en la nube. Además, proporciona un alto nivel de aislamiento, dado que cada contenedor incluye su propio sistema de archivos y conjunto de dependencias, lo que elimina conflictos entre proyectos. Otra ventaja significativa es su capacidad de escalar aplicaciones de forma eficiente, gracias a su integración nativa con Kubernetes y otros orquestadores. Esta capacidad de escalado se complementa con la reproducibilidad que ofrece, aspecto crucial en ciencia de datos, donde la replicación de experimentos es fundamental. Finalmente, Docker simplifica el despliegue continuo al integrarse fácilmente con flujos CI/CD, lo que facilita la automatización de la puesta en producción de modelos.

Sin embargo, Docker también tiene desventajas. Aunque es más ligero que una máquina virtual, introduce cierta sobrecarga en el uso de CPU y memoria. Su uso puede resultar complejo, especialmente para quienes deben aprender a manejar Dockerfiles, redes, volúmenes y configuraciones de orquestación. Además, si no se gestionan adecuadamente las imágenes y configuraciones, pueden surgir problemas de seguridad debido a vulnerabilidades en el software empaquetado.

Por su parte, UV se destaca como un manejador de dependencias extremadamente rápido para la resolución e instalación de paquetes en comparación con herramientas tradicionales como pip o pipenv. UV mejora la consistencia en la gestión de dependencias, asegurando que las versiones utilizadas sean uniformes en diferentes entornos de desarrollo. Al ser una herramienta ligera, resulta ideal para la gestión de entornos de desarrollo locales sin necesidad de depender de contenedores. Sin embargo, UV presenta algunas limitaciones. Su ámbito de aplicación se restringe a proyectos en Python, a diferencia de Docker, que puede manejar aplicaciones que combinan múltiples lenguajes. Además, aunque UV gestiona eficientemente las dependencias, no ofrece el mismo nivel de aislamiento del sistema operativo que proporciona Docker. Finalmente, al ser una herramienta relativamente nueva, puede tener limitaciones de compatibilidad en entornos muy específicos o menos comunes.

Combinar UV y Docker puede ser una excelente práctica, especialmente en entornos de ciencia de datos y MLOps. UV puede utilizarse en la fase de desarrollo para gestionar dependencias de manera rápida y eficiente, mientras que Docker asegura que la aplicación funcione de forma consistente en cualquier entorno, desde pruebas hasta producción. Un flujo de trabajo eficiente podría consistir en utilizar UV para instalar dependencias en el entorno local durante el desarrollo. Posteriormente, al construir el contenedor, se puede incluir UV en el Dockerfile para gestionar las dependencias dentro del propio contenedor. Finalmente, en la etapa de despliegue, Docker garantiza que la aplicación, junto con sus dependencias gestionadas por UV, opere de manera confiable tanto en entornos de staging como en producción.

Además, desarrollar utilizando UV directamente sobre un contenedor es una práctica recomendada que permite optimizar aún más el rendimiento y la gestión de dependencias en entornos de producción. Esta combinación ofrece ventajas significativas, como un rendimiento mejorado en la resolución de dependencias, mayor consistencia en entornos de desarrollo y producción, y una menor complejidad en la gestión de entornos virtuales. Usar UV sobre Docker es especialmente útil en proyectos complejos de ciencia de datos, entornos de integración y despliegue continuo (CI/CD), y microservicios en Python, donde la eficiencia y la reproducibilidad son esenciales.

En conclusión, UV destaca por su velocidad y eficiencia en la gestión de dependencias de Python, mientras que Docker ofrece portabilidad, aislamiento y consistencia en todo el ciclo de vida del modelo. El uso combinado de ambas herramientas permite aprovechar lo mejor de cada una: la rapidez en el desarrollo y la robustez en la producción, optimizando así los flujos de trabajo en ciencia de datos y MLOps.
