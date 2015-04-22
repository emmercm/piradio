# piradio
A headless jukebox designed to run on the Raspberry Pi.

### Intro
Started as a single semester-long Computer Science Bachelor's senior project, `piradio` is a fully-featured internet radio and local media playback device.

The application currently supports playback from:
- The root filesystem
- Attached USB mass storage devices
- Pandora (via pianobar)
- Spotify (premium accounts only)

### Installation
##### Download
Download the latest release from https://github.com/emmercm/piradio/releases and extract to any directory.
##### Dependencies
To install all necessary dependencies run the following:
```
sudo python setup.py
```
This setup script will:
- Add apt.mopidy.com to the APT source list (for pyspotify)
- Install various APT packages
- Install pip if it is missing
- Install/update various PyPy packages
- Build pianobar from source

### Execution
To execute `piradio` run the following:
```
sudo python piradio.py
```
Root access is required for:
- Running the CherryPy web server on port 80
- For Display-O-Tron 3000 (dot3k) to have access to `/dev/mem`

### Additional
To make `piradio` start on Raspbian startup you can add the following line to `/etc/rc.local`:
```
nohup sudo python piradio.py
```

### License
`piradio` is under the MIT license which is simple and permissive but requires attribution to the original author(s).