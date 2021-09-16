import argparse
import errno
import glob
import logging
import os
import sys
import time
from collections import namedtuple
from contextlib import contextmanager
from typing import Iterable, List, Union, Callable

import serial
from tqdm import trange

BUFFER_SIZE = 2048
DEFAULT_ITERATIONS = 100
DEFAULT_DIR = "data_wr"
DEFAULT_BAUDRATE = 9600
DATE_TIME_FORMAT = '%d-%m-%Y %H:%M:%S'

Config = namedtuple(
    'Config', 'port count_iter file_name debug log write baudrate')
class ComPort:
    __is_port = True

    def __init__(self, serial_port):
        self.buf = bytearray()
        self.serial_port: serial.Serial = serial_port

    def readline(self):
        i = self.buf.find(b"\n")
        if i >= 0:
            r = self.buf[:i + 1]
            self.buf = self.buf[i + 1:]
            return r

        while True:
            i = max(1, min(BUFFER_SIZE, self.serial_port.in_waiting))
            data = self.serial_port.read(i)
            i = data.find(b"\n")
            if i >= 0:
                r = self.buf + data[:i + 1]
                self.buf[0:] = data[i + 1:]
                return r
            else:
                self.buf.extend(data)


@contextmanager
def file_open(path: str) -> Iterable[int]:
    try:
        file = open(path, 'w', encoding='utf-8')
        yield file
    except OSError:
        print("We had an error!")
    finally:
        print('Closing file')
        file.close()


def create_dir(directories):
    try:
        os.mkdir(directories)
    except:
        raise OSError(
            f"Can't create destination directory :{directories}") 


def cleaning_artifacts(data: List[str]) -> List[str]:
    """Clears the beginning of the message from ASCII characters 0x00.
    """
    data_new = ''
    for elem in data[0]:
        if ord(elem) == 0:
            continue
        data_new += elem
    data[0] = data_new
    return data


def get_path_file(file_name:str, name_dir: str=DEFAULT_DIR) -> str:
    if not os.path.exists(name_dir):
       create_dir(name_dir)
    return os.path.join(name_dir, file_name + '.txt')


def print_port_info(serial_potr: serial.Serial) -> None:
    print('Parametrs:')
    print(' baudrate:', serial_potr.baudrate)
    print(' timeout:', serial_potr.timeout)
    print(' rtscts:', serial_potr.rtscts)
    print(' xonxoff:', serial_potr.xonxoff)
    print(' dsrdtr:', serial_potr.dsrdtr)
    print('...')
    time.sleep(0.5)
    print(f"\033[31mConnecting ...  True\033[0m")

def is_valied_baudrate(baudrate:int) -> bool:
    return baudrate in (110, 300, 600, 1200, 2400, 4800, 9600, 14400,
                         19200, 38400, 57600, 115200, 128000, 256000)


def get_active_comport(conf:Config) -> serial.Serial:
    port: str = conf.port
    baudrate: int = conf.baudrate

    if not is_valied_baudrate(baudrate):
        logging.error(f"Incorrect value baudrate: {baudrate}")
        raise ValueError(f"Incorrect value baudrate: {baudrate}")

    print(f'\033[31m Connecting.... PORT: {port} \033[0m')
    time.sleep(0.8)
    serial_potr: Union[serial.Serial] = None
    try:
        serial_potr = serial.Serial(port, baudrate=baudrate,
                                    dsrdtr=False, timeout=1.0,
                                    rtscts=True, xonxoff=False)
    except Exception as exc:
        logging.exception(exc)
        raise ValueError("Ошибка открытия порта") from exc

    print_port_info(serial_potr)

    comport: ComPort = ComPort(serial_potr)
    if not comport._ComPort__is_port:                                   #TODO
        raise TypeError('Error type!')

    return comport


def write_data_to_file(comport: ComPort, conf: Config) -> None:
    count_iter: int = conf.count_iter
    file_name: str =  conf.file_name
    debug: bool = conf.debug

    with file_open(get_path_file(file_name)) as file:
        print(f'Create new file: "data_wr/{file_name}.txt"')
        print('\033[33mRecord...\033[0m')
        for i in trange(count_iter):
            data: List[str] = comport.readline().decode("utf-8").split()
            if debug:
                logging.debug(f"reading `raw` lines: {data}")
            data = cleaning_artifacts(data)
            file.write(f'{i} ----- {time.ctime()} {data} \n')
        else:
            comport.serial_port.close()


def print_to_stdout(comport:ComPort, conf: Config) -> None:    
    debug: bool = conf.debug
    try:
        while True:
            data: List[str] = comport.readline().decode("utf-8").split()
            if debug:
                logging.debug(f"reading `raw` lines: {data}")
            data = add_color_text(cleaning_artifacts(data))
            print(time.ctime(), *data)
    finally:
        comport.serial_port.close()


def add_color_text(data: List[str]) -> List[str]:
    """Used to customize display colors in the terminal utility.
       FOR USER!!!
    """

    colors_text ={
        "yellow":    '\033[33m{}\033[0m',
        "green":     '\033[32m{}\033[0m',
        "red":       '\033[31m{}\033[0m',
        "blue":      '\033[34m{}\033[0m',
        "purple":    '\033[35m{}\033[0m',
        "turquoise": '\033[36m{}\033[0m',
    }
    selelect_color = {
        "info:": colors_text["yellow"],
        "debug:": colors_text["green"],
        "warning:": colors_text["blue"],
        "error:": colors_text["red"],
        "exception:": colors_text["purple"],
    }
    color_digits = colors_text["turquoise"]

    status = data[0].strip()
    if not status in set(("info:", "debug:", "error:", "exception:", "warning:")):
        return data

    for i in range(len(data)):
        if data[i].isdigit():
            data[i] = color_digits.format(data[i])
        else:
           data[i] = selelect_color[status].format(data[i])
    return data


def main(conf: Config) -> None:
    wrile_to_file: bool = conf.write
    comport = get_active_comport(conf)

    prosses: Callable = write_data_to_file if wrile_to_file else print_to_stdout
    prosses(comport, conf)


def arg_parser() -> Config:
    time_str = str(time.time())

    parser = argparse.ArgumentParser(
        description=(
            "The program allows you to write data from a com port file, output color string and "
            "digital values ​​to the standard output stream. The program provides message coloring "
            "for debugging the following logging levels: [info, debug, error, exception, warning]. "
            "Each message must start at the appropriate logging level + `:`."),
        prog='python -m com_p.py')

    parser.add_argument('-p', '--port', default='COM9', type=str, nargs='?',
                        help="port string representation: COM")
    parser.add_argument('-i', '--iter', default=DEFAULT_ITERATIONS, type=int, nargs='?',
                        help='Number of record iterations')
    parser.add_argument('-b', '--baudrate', default=DEFAULT_BAUDRATE, type=int, nargs='?',
                        help='Standard baud rates (bits per second)')
    parser.add_argument('-n', '--name', type=str, default=time_str,
                        nargs='?', help='File name + time')
    parser.add_argument('-d', '--debug', action='store_true', default=False)
    parser.add_argument('-l', '--log', action='store', default=None)
    parser.add_argument('-w', '--write', action='store_true', default=False,
                        help='Flag for selecting the write mode or standard output in `stdout`')

    namespace = parser.parse_args(sys.argv[1:])

    if len(namespace.port) > 3:
        namespace.port = "\.\\" + namespace.port
    
    file_name = namespace.name
    if file_name != time_str:
        file_name = file_name + time_str
    

    conf = Config(port= namespace.port, count_iter=namespace.iter, 
                 file_name=file_name.strip(), debug=namespace.debug,
                 log=namespace.log, write=namespace.write, baudrate=namespace.baudrate)
    return conf


if __name__ == "__main__":
    conf = arg_parser()
    logging.basicConfig(filename=conf.log,
                        level=logging.DEBUG if conf.debug else logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s',
                        datefmt='%Y.%m.%d %H:%M:%S')
    try:
        main(conf)
    except KeyboardInterrupt:
        logging.info('Com post closed')
    except Exception as exc: 
        logging.exception(f'Unexpected error: {exc}')
