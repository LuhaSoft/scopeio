#!/bin/bash

for file in *.exp
do
	expect $file | grep -e "Test:" -e "Result:"
done

