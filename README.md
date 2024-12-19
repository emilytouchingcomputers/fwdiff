# fwdiff
tool to quickly find changes in binaries in linux based firmware images

 **Usage:**

    binwalk -e image1.bin
    binwalk -e image2.bin
    python3 differ.py firmware/_image1.bin.extracted/ firmware/_image2.bin.extracted/ image1_vs_image2.txt
