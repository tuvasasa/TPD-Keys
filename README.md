# TPD-Keys v2 by tuvasasa
Add new updates for Star+ and Directv Go Latam
Añadido nuevas actualizaciones para Star+ y Directv Go Latam


English:
--------------
It is necessary to have our own CDM, for more information, read here.
https://forum.videohelp.com/threads/408031-Dumping-Your-own-L3-CDM-with-Android-Studio

How to use:

1. Create TPD-Keys folder.

2. Download and extract tpd-keys.py, requirements.txt and DRMHeaders.py into the newly created TPD-Keys directory

3. Install the requirements with pip install -r requirements.txt

4. Create a WVD with pywidevine; pywidevine create-device -k "/PATH/TO/device_private_key" -c "/PATH/TO/device_client_id_blob" -t "ANDROID" -l 3

5. Replace MyWVD= "/PATH/TO/WVD.wvd" with the path to your .wvd on line 15 of tpd-keys.py

For instance MyWVD = "C:\Users\TPD94\Desktop\AndroidDevice.wvd" or if it is located in the same folder MyWVD = "AndroidDevice.wvd"

6. Paste any needed headers into DRMHeaders.py

7. Run with python tpd-keys.py

Make a selection

Credits:
CDRM-Project for creating this aplication

Español
----------------
Es necesario contar con nuestro propio CDM, para más información, leer aquí
https://forum.videohelp.com/threads/408031-Dumping-Your-own-L3-CDM-with-Android-Studio

Modo de empleo:

1. Crear la carpeta TPD-Keys.

2. Descargar y extraer tpd-keys.py, requirements.txt y DRMHeaders.py en el directorio TPD-Keys recién creado.

3. Instalar los requisitos con pip install -r requirements.txt

4. Crear un WVD con pywidevine; pywidevine create-device -k "/PATH/TO/device_private_key" -c "/PATH/TO/device_client_id_blob" -t "ANDROID" -l 3

5. Sustituir MyWVD= "/PATH/TO/WVD.wvd" por la ruta a su .wvd en la línea 15 de tpd-keys.py

Por ejemplo MyWVD = "C:\users\TPD94\Desktop\AndroidDeivce.wvd" o si se encuentra en la misma carpeta MyWVD = "AndroidDevice.wvd"

6. Pegar las cabeceras necesarias en DRMHeaders.py

7. Iniciar con python tpd-keys.py

8. Hacer selección

Créditos:
CDRM-Project por crear esta aplicación
