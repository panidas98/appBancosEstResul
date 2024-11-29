# Consideraciones iniciales:
Para abordar el ejercicio, creé primero una extracción de los datos desde una carpeta publica que tengo en google drive.
[Link carpeta](https://drive.google.com/drive/folders/1uxxPGufCgLTU54hBlqVvw3QSE1-BWW8J?usp=sharing)
Los puntos 1,2 y 3 fueron realizados en el archivo appROI.ipynb
https://colab.research.google.com/drive/1BlQPwetZKa20wcwM8yuyG7TBaonygfl8?usp=sharing

1. Obtengo todas las rutas disponibles y las guardo en una lista
2. Luego hago una extracción de los datos de cada archivo, contemplando que pueden iniciar desde partes distintas y tener diferente longitud.
3. Luego tomo ese dataset consolidado y creo uno con el beneficio neto.
4. Utilizo un codigo con librerías de analisis de datos y streamlit para generar analítica de la información obtenida de una forma amigable con el usuario. El repositorio en git hub es [este](https://github.com/panidas98/appBancosEstResul/tree/main) Por favor revisar allí la otra parte muy importante del despliegue que es el escript usado para graficar y analizar.
5. Y este es el servicio donde podrán ver el analisis de la información.
[Link del dashboard](https://appbancosestresul.streamlit.app/)
