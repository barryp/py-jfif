#!/usr/bin/env python
"""
 Toolkit for manipulating the structure of a JPEG-JFIF
 file.  Doesn't actually decompress the image

 Barry Pederson <bp@barryp.org>
"""
import types

#
# JPEG Marker codes
#
# Start of Frame markers, non-differential, Huffman coding

SOF_0   = 0xc0    # Baseline DCT
SOF_1   = 0xc1    # Extended sequential DCT
SOF_2   = 0xc2    # Progressive DCT
SOF_3   = 0xc3    # Lossless (sequential)

SOI     = 0xd8    # Start of Image
EOI     = 0xd9    # End of Image
SOS     = 0xda    # Start of Scan

APP_0   = 0xe0    # Application specific segments
APP_1   = 0xe1    # Application specific segments
APP_2   = 0xe2    # Application specific segments
APP_3   = 0xe3    # Application specific segments
APP_4   = 0xe4    # Application specific segments
APP_5   = 0xe5    # Application specific segments
APP_6   = 0xe6    # Application specific segments
APP_7   = 0xe7    # Application specific segments
APP_8   = 0xe8    # Application specific segments
APP_9   = 0xe9    # Application specific segments
APP_10  = 0xea    # Application specific segments
APP_11  = 0xeb    # Application specific segments
APP_12  = 0xec    # Application specific segments
APP_13  = 0xed    # Application specific segments
APP_14  = 0xee    # Application specific segments
APP_15  = 0xef    # Application specific segments

COM     = 0xfe    # Comment

class JFIF:
    """
    Represent the structure of a JPEG-JFIF file.
    
    The constructor's data parameter may be:
    
     1) a string containing the actual bytes of a JPEG-JFIF image
     2) a string containing a filename
     3) another JFIF instance
     4) a list of JFIF segments, as returned by another JFIF 
        object's getSegments() method
     5) a file-like object with a read() method.
    """
    def __init__(self, data):
        self._segments = []
        
        #
        # Get the actual bytes of the JPEG image
        #
        if type(data) == types.StringType:
            if data.startswith('\xff\xd8\xff'):
                img = data
            else:
                img = open(data, 'rb').read()
        elif type(data) == types.ListType:
            self._segments = data[:]
            return   
        elif isinstance(data, JFIF):
            self._segments = data._segments[:]
            return                         
        else:            
            img = data.read()

        #
        # Scan over the bytes, breaking the stream
        # into a list of segments
        #    
        i = 0
        imglen = len(img)    
        while i < imglen:
            b = img[i]
            if b == '\xff':
                i += 1
                b = img[i]
                if b == '\x01' or ((b >= '\xd0' and b <= '\xd9')):
                    pass
                elif b == '\xda':
                    j = i+1
                    while j < imglen:
                        b2 = img[j]
                        b3 = img[j+1]
                        if (b2 == '\xff') and (b3 != '\x00') and (not((b3 >= '\xd0') and (b3 <= '\xd7'))):
                            self._segments.append((0xda, img[i+1:j]))
                            i = j-1
                            break
                        j += 1    
                else:
                    ln = (ord(img[i+1]) * 256) + ord(img[i+2])
                    self._segments.append((ord(b), img[i+3:i+1+ln]))
                    i += ln
            i += 1
    #            
    # all done, the self._segments property now holds
    # the broken-up JPEG image
    #
    
    
    def getBytes(self):
        """
        Rebuild the JPEG-JFIF data, and return
        as a single string.
        """
        img = '\xff\xd8'
        for s in self._segments:
            if s[0] == SOS:
                img += '\xff\xda' + s[1]
            else:
                img += '\xff'
                img += chr(s[0])
                ln = len(s[1]) + 2
                img += chr(ln >> 8)
                img += chr(ln & 0xff)
                img += s[1]            
        return img + '\xff\xd9'

    
    def getByteSize(self):
        """
        Calculate how big a rebuilt JPEG-JFIF file will
        be when write() or getBytes() is called.
        """
        if not self._segments:
            return 0
            
        count = 4
        for s in self._segments:
            if s[0] == SOS:
                count += 2 + len(s[1])
            else:
                count += 4 + len(s[1])
        return count        
        
        
    def getMD5(self):
        """
        Get a MD5 digest of the segments of the JPEG
        file, skipping any application-specific and comment
        segments.  Good for comparing two files to see
        if they are the same, ignoring differences in 
        non-image data.
        """
        import md5
        h = md5.md5()
        for s in self._segments:
            if s[0] == COM:
                continue
            if (s[0] >= APP_0) and (s[0] <= APP_15):
                continue
            h.update(chr(s[0]))              
            h.update(s[1])
        return h.hexdigest()        
          
                
    def getSegments(self):
        """
        Get the list of segments that make up the image.
        Each entry in the list is a tuple of two items:
        the marker byte that identifies the segment, and
        the bytes that make up the segment.  
        
        The SOI and EOI segments are omitted, and the contents
        of each segment don't include the 2 length bytes that 
        come right after the marker in the original JFIF file.
        """
        return self._segments[:]


    def getSize(self):
        """
        Get the width and height of the image, returned
        as a tuple of integers in that order
        """
        for s in self._segments:
            if (s[0] >= SOF_0) and (s[0] <= SOF_3):
                return ((ord(s[1][3]) * 256) + ord(s[1][4]), (ord(s[1][1]) * 256) + ord(s[1][2]))
                        
        
    def write(self, outfile):
        """
        Write the image to a file-like object, all it
        has to have is a write() method. No flush()
        or close() methods are called by this method.
        
        If the 'outfile' parameter is a string, it's 
        treated as a filename, and a file is opened
        and written to under that name.
        """
        if type(outfile) == types.StringType:
            outfile = open(outfile, 'wb')
            
        outfile.write('\xff\xd8')
        for s in self._segments:
            if s[0] == SOS:
                outfile.write('\xff\xda')
                outfile.write(s[1])
            else:
                outfile.write('\xff')
                outfile.write(chr(s[0]))
                ln = len(s[1]) + 2
                outfile.write(chr(ln >> 8))
                outfile.write(chr(ln & 0xff))
                outfile.write(s[1])
        outfile.write('\xff\xd9')
    

# ------- Test code ------------
#
# Reads a JPEG file, strips out non-image segments, writes
# out to a new file.
#

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print 'Test usage: %s <input-jpeg> <output-file>' % sys.argv[0]
        sys.exit(0)
        
    img = JFIF(sys.argv[1])

    #
    # Build a new list of segments, copying elements from the 
    # old list of segments
    #
    ns = []
    for s in img.getSegments():
        #
        # Copy the header
        #
        if (s[0] == APP_0) and s[1].startswith('JFIF\x00'):
            ns.append(s)
            continue
         
        # 
        # Skip over all other application-specific bits, and comments
        #        
        if ((s[0] >= APP_0) and (s[0] <= APP_15)) or (s[0] == COM):
            continue
         
        #
        # copy everything else
        #        
        ns.append(s)
    
    #
    # Recombine the new list of segments into a new JFIF 
    # object, and write to a file.
    #
    JFIF(ns).write(sys.argv[2])

#
# --- EOF ----    
#