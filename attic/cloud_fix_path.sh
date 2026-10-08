#!/bin/bash
cd /root/autodl-tmp/mbn/llm
/root/miniconda3/bin/python -c "import pathlib; p = pathlib.Path(chr(101)+chr(120)+chr(112)+chr(111)+chr(115)+chr(117)+chr(114)+chr(101)+chr(95)+chr(105)+chr(110)+chr(99)+chr(111)+chr(110)+chr(116)+chr(101)+chr(120)+chr(116)+chr(46)+chr(112)+chr(121)); s = p.read_text(); s = s.replace(chr(47)+chr(114)+chr(111)+chr(111)+chr(116)+chr(47)+chr(109)+chr(98)+chr(110), chr(47)+chr(114)+chr(111)+chr(111)+chr(116)+chr(47)+chr(97)+chr(117)+chr(116)+chr(111)+chr(100)+chr(108)+chr(45)+chr(116)+chr(109)+chr(112)+chr(47)+chr(109)+chr(98)+chr(110)); p.write_text(s); print(chr(80)+chr(65)+chr(84)+chr(72)+chr(95)+chr(70)+chr(73)+chr(88))"
setsid nohup /root/miniconda3/bin/python exposure_incontext.py gpt2 > exposure_incontext_gpt2v2.log 2>&1 < /dev/null &
sleep 150
tail -4 exposure_incontext_gpt2v2.log
