# TPD-Keys

How to use:

1. Create TPD-Keys folder.

2. Download and extract tpd-keys.py, requirements.txt and DRMHeaders.py into the newly created TPD-Keys directory

3. Install the requirements with pip install -r requirements.txt

4. Create a WVD with pywidevine; pywidevine create-device -k "/PATH/TO/device_private_key" -c "/PATH/TO/device_client_id_blob" -t "ANDROID" -l 3

5. Replace MyWVD= "/PATH/TO/WVD.wvd" with the path to your .wvd on line 15 of tpd-keys.py

For instance MyWVD = "C:\Users\TPD94\Desktop\AndroidDeivce.wvd" or if it is located in the same folder MyWVD = "AndroidDeivce.wvd"

6. Paste any needed headers into DRMHeaders.py

7. Run with python tpd-keys.py

Make a selection

Credits:
CDRM-Project for creating this aplication
