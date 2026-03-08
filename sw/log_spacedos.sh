echo "SPACEDOS data logger"
echo "To exit, pres ctrl-a, ctrl-x"
echo "usage example: ./log_spacedos.sh /dev/ttyUSB0 [description]"

mkdir ./log/ >/dev/null 2>&1

DESC=""
if [ -n "$2" ]; then
  DESC="_$2"
fi

picocom -b 2400 -q $1 | awk '{ print strftime("%s,")$0; fflush(); }' | tee ./log/SPACEDOS01_$(date +"%Y%m%d_%H%M%S")${DESC}.log
