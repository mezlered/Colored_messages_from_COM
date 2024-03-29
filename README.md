## Colored messages from COM port Puthon 3.7

The program allows you to write data from a com port file, output color
string and digital values ​​to the standard output stream. The program provides
message coloring for debugging the following logging levels: [info, debug, error, exception, warning].
Each message must start at the appropriate `logging level` + `:`.

## Installation

```bash
pip install -r requirements.txt
```

## Run

```bash
python -m working_time.py
```

## To help

```bash
python -m com_p.py --help
```

```
usage: python -m com_p.py [-h] [-p [PORT]] [-i [ITER]] [-b [BAUDRATE]]
                          [-n [NAME]] [-d] [-l LOG] [-w]

optional arguments:
  -h, --help            show this help message and exit
  -p [PORT], --port [PORT]
                        port string representation: COM
  -i [ITER], --iter [ITER]
                        Number of record iterations
  -b [BAUDRATE], --baudrate [BAUDRATE]
                        Standard baud rates (bits per second)
  -n [NAME], --name [NAME]
                        File name + time
  -d, --debug
  -l LOG, --log LOG
  -w, --write           Flag for selecting the write mode or standard output in `stdout`
```