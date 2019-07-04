#!/bin/bash
echo "fver.sh <up to 7 char file hash>"
git log --raw |grep -B 10 $1

