# x68pcm

## install

```bash
pip install git+https://github.com/yumimint/x68pic
```

## usage

usage: x68pcm [-h] [-o OUTPUT] [-s N] [-d] {d,e} input

x68k ADPCM converter

positional arguments:
  {d,e}         specify mode. d=decode/play or e=encode
  input         specify input file

options:
  -h, --help    show this help message and exit
  -o OUTPUT     specify output file
  -s N          sample rate (0=3.9, 1=5.2, 3=7.8, 3=10.4, 4=15.6) KHz
                default=4
  -d, --dither  enable dithering
