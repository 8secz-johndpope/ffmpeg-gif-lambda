#!/bin/bash
ffmpeg -i $INFILE -vf 'fps=10,scale=200:-1:flags=lanczos,palettegen' /tmp/palette.png
ffmpeg -i $INFILE -i /tmp/palette.png  -filter_complex 'fps=20,scale=200:-1:flags=lanczos,paletteuse' $OUTFILE
