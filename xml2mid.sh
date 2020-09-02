ext='.musicxml'
for i in $1/*${ext}
do
base=`basename $i $ext`
 /Applications/MuseScore\ 3.app/Contents/MacOS/mscore -o $1/${base}.mid $1/${base}.musicxml
done
