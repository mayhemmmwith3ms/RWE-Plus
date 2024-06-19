**RWE+ requires python 3.11 or higher**

## Setting things up

To use RWE+ on linux you first need to set up a python3.11 virtual environment

If you do not already have python3.11 installed on your system, it can be installed using the following command:

`$ sudo apt install python3.11`

Next thing you need to do is download the source code from the newest RWE+ [release](https://github.com/mayhemmmwith3ms/RWE-Plus/releases/download/latest/), unzip and open it in the terminal

The virtual environment can then be installed and created with:


`$ sudo apt install python3.11-venv`

`$ python3.11 -m venv ./`

All modules listed in requirements.txt and can be easily installed with:

`$ bin/pip3.11 install -r requirements.txt`

Some of the modules need to be installed using apt:

`$ sudo apt install python3.11-tk`

After that, main.py can be ran using a bash script:

`$ ./run.sh`

If everything has been set up correctly, this will start RWE+.

## Additional info
By default, this fork uses the default OS file browser to select files. This works fine on Windows, however appears to be unstable on Linux. The in-built file browser can be enabled by navigating to `files/settings.json`, and changing `"native_file_browser"` to `false`.

RWE+ ships with a version of [Drizzle](https://github.com/SlimeCubed/Drizzle) compiled for Windows only. In order to render levels on Linux, you need to download the latest Linux build of Drizzle from the repository, and replace the contents of the `drizzle` folder with the contents of the release archive. **Note that as far as I have tested, the Linux build of Drizzle does not appear to function. This means for the time being, levels cannot be rendered on Linux.**