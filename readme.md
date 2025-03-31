# RaspberryPi SecurityCam

## perpouse of the project
 A project for my final poject for the JohnBryce Academy quick course for Python fullstack programing.
 In this project I built a securityCam on Raspberry-Pi to function as the computer processing everything and as server for the user to access through HTML. 

 I am using Raspberry-Pi-5 16GB integrated (shared between CPU and GPU) and microSD over 100GB in memory.
 <br>Using Python version 3.9 and virtual enviroment because I found it the version needed for Face recognition package.
<br><br>

## I needed to do major changes here to make this work
Because this is focused to Linux-Bookworm for Raspberry Pi this needed libcamera and picamera to handle the camera because my RaspberryPi5 didnt have the Binder needed to use cv2 because libcamera and picamera are the deafult, so installations of the package in the sudo apt were needed and pip install.<br> And to avoid problems with dealing installing pykms, which picamera demands, adjustments were needed to be made in the <b>drm_preview.py</b> in picamera package <b>((</b> env/lib/python3.9/site-packages/picamera2/previews/drm_preview.py<b> ))</b> in my Virtualenviroment where I defined the <b>"kms"</b> package as <b>None</b> and had to add <b>"if condition"</b> to the <b>Class DrmPreview(NullPreview)</b> and then put it into an <b>"else raise error"</b> so it wont need that class and would work:

<b>// this is in the import in the up part of the page //</b><br>
try:<br>
    # If available, use pure python kms package<br>
    import kms as pykms<br>
except ImportError:<br>
    pykms = None

<b>// the drmpreview class //</b> 

if pykms is not None:<br>
    class DrmPreview(NullPreview):<br>
        FMT_MAP = {<br>
            "RGB888": pykms.PixelFormat.RGB888,<br>
            "BGR888": pykms.PixelFormat.BGR888,

<b>......... Rest of the class code .......</b>

<b>// after the end of the class //</b> 

else: <br>
    class DrmPreview:<br>
        def __init__(self, *args, **kwargs):<br>
            raise ImportError("pykms is not available, cannot use DrmPreview")

## The installation commands were: 

<b>Updating the package manager:</b><br>
sudo apt update

<b>Installing required libcamera + picamera2 packages to the system (((requiered))):</b><br>
sudo apt install -y python3-libcamera python3-picamera2 libcamera-dev

<b>And then installing the python packages if working with virtual enviroment (like i did):</b><br>
pip install picamera2
pip install rpi-libcamera

 ### For Database managment I am using sqlite3 and for code packages I am using: 

annotated-types==0.7.0 <br>
anyio==4.8.0<br>
attrs==25.3.0<br>
av==14.2.0<br>
click==8.1.8<br>
cmake==3.31.6<br>
colorama==0.4.6<br>
distlib==0.3.9<br>
dlib==19.24.6<br>
exceptiongroup==1.2.2<br>
face-recognition==1.3.0<br>
face-recognition-models==0.3.0<br>
fastapi==0.115.8<br>
filelock==3.17.0<br>
h11==0.14.0<br>
idna==3.10<br>
jsonschema==4.23.0<br>
jsonschema-specifications==2024.10.1<br>
libarchive-c==5.2<br>
numpy==2.0.2<br>
opencv-python==4.11.0.86<br>
picamera2==0.3.25<br>
pidng==4.0.9<br>
piexif==1.1.3<br>
pillow==11.1.0<br>
platformdirs==4.3.6<br>
pydantic==2.10.6<br>
pydantic_core==2.27.2<br>
PyJWT==2.10.1<br>
python-dotenv==1.0.1<br>
python-prctl==1.8.1<br>
referencing==0.36.2<br>
rpds-py==0.23.1<br>
rpi-libcamera==0.1a9<br>
simplejpeg==1.8.2<br>
sniffio==1.3.1<br>
starlette==0.45.3<br>
tqdm==4.67.1<br>
typing_extensions==4.12.2<br>
uvicorn==0.34.0<br>
v4l2-python3==0.3.5<br>
virtualenv==20.29.2<br>
wheel ==  0.45.1 