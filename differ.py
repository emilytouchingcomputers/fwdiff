#script for diffing firmware images
#solves the problem of elf headers with different build info
#binwalk -e image1.bin
#binwalk -e image2.bin
#python3 differ.py firmware/_image1.bin.extracted/ firmware/_image2.bin.extracted/ image1_vs_image2.txt
import os
import sys
import argparse
import re
import hashlib

#this exists because of OSX, thanks Tim Apple.
objcopy_path = "/usr/bin/objcopy"

#regexs for parsing the diff output
regex_directory_first = re.compile("Files( *.+.extracted+.*)")
regex_directory_second = re.compile("(.*)differ")

#arg parsing
parser = argparse.ArgumentParser()
parser.add_argument("first", help="first directory")
parser.add_argument("second", help="second directory")
parser.add_argument("outfile", help="outfile")
args = parser.parse_args()
print("First Directory: \n%s\n\nSecond Directory: \n%s\n\nOutfile: \n%s\n" % (args.first, args.second, args.outfile))
directory_first = ("\"" + args.first + "\"")
directory_second =("\"" + args.second + "\"")
outfile = (args.outfile)

#diff, if file is elf then objdump and diff again, otherwise just write to file
#diff -r --brief --no-dereference "firmware/_image1.bin.extracted/" "firmware/_image2.bin.extracted/" >> diffed.txt
diff_string = ("diff -r --brief --no-dereference " + directory_first + " " + directory_second + ">> " + "tmp_diff_file.txt")
print ("Command:\n" + diff_string)

#diff the folders and everything in them
os.system(diff_string)

#make a directory to keep our bins
#for some reason this fails if it exists, but #wontfix
if not os.path.isfile('adiff_tmpdir'):
	os.mkdir('adiff_tmpdir')
final_file = open(outfile, "w+")

#open our text file of diff output
file = open("tmp_diff_file.txt", 'r')
print("**************DUMPING_OUTFILE************")
for line in file:
	#if a file exists only in one image, just write it out and move on
	if ("Only in " in line):
		final_file.write(line)
	#diff just says "named pipe is a fifo while named pipe is a fifo" and that's useless.
	#could also use this to exclude like .html or whatever else we don't want in the future
	elif ("is a fifo while" in line):
		continue
	else:
		split_string = line.split(' and ')
		directory_first = (re.match(regex_directory_first, split_string[0]))
		directory_second = (re.match(regex_directory_second, split_string[1]))
		directory_first = str(directory_first.group(1)[1:])
		directory_second = str(directory_second.group(1))
		filename_first = directory_first.split('/')[-1]
		filename_second = directory_second.split('/')[-1]
		try:
			#objdump elf files to extract the .text section and put it in the temp dir.  This gets around differences in build ID from triggering the diff
			os.system(objcopy_path + " -O binary --only-section=.text " + directory_first + " adiff_tmpdir/file_1.bin.text >/dev/null 2>&1")
			os.system(objcopy_path + " -O binary --only-section=.text " + directory_second + " adiff_tmpdir/file_2.bin.text >/dev/null 2>&1")
			#check the hashes of the .text sections to see if the code is actually different
			filehash_first = hashlib.md5(open('adiff_tmpdir/file_1.bin.text','rb').read()).hexdigest()
			filehash_second = hashlib.md5(open('adiff_tmpdir/file_2.bin.text','rb').read()).hexdigest()
			#They are the same, so we don't write this to our file
			if filehash_first == filehash_second:
				os.system("rm adiff_tmpdir/file_1.bin.text")
				os.system("rm adiff_tmpdir/file_2.bin.text")
			#They are different!	
			else:
				print("Differ: %s, %s" % (filehash_first, filehash_second))
				print(directory_first)
				print(directory_second)
				print("")
				final_file.write(line)
				os.system("rm adiff_tmpdir/file_1.bin.text")
				os.system("rm adiff_tmpdir/file_2.bin.text")
		#Too lazy to make sure it's an ELF so we just write it out if objcopy errors
		except:
			final_file.write(line)
			continue
file.close()
final_file.close()
print("********REMOVING TEMP DIR**********")
os.system("rm -rf adiff_tmpdir")
print("********REMOVING TEMP FILE**********")
os.system("rm tmp_diff_file.txt")
print("*********CLOSED_OUTFILE************")
print("Thank you for playing Wing Commander!")
