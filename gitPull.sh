#!/bin/bash

until git pull https://github.com/Jason-Botha/LED_Active.git
do
  echo
  echo "Download failed. Retrying.."
  echo "CTRL +C to Exit"
  echo
done
sleep 5
