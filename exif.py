#!/usr/bin/env python
"""
Support for Exchangeable image file format for Digital Still Cameras: Exif

Mark Hammond <mhammond@skippinet.com.au>

"""
import struct

# TIFF tag IDs in the Exif data
# tag names used for humans only!
tags_by_id = {
    254 : "NewSubfileType",
    255: "SubfileType",
    256: "ImageWidth",
    257: "ImageLength",
    258: "BitsPerSample",
    259: "Compression",
    262: "PhotometricInterpretation",
    263: "Threshholding",
    264: "CellWidth",
    265: "CellLength",
    266: "FillOrder",
    269: "DocumentName",
    270: "ImageDescription",
    271: "Make",
    272: "Model",
    273: "StripOffsets",
    274: "Orientation",
    277: "SamplesPerPixel",
    278: "RowsPerStrip",
    279: "StripByteCounts",
    280: "MinSampleValue",
    281: "MaxSampleValue",
    282: "XResolution",
    283: "YResolution",
    284: "PlanarConfiguration",
    285: "PageName",
    286: "XPosition",
    287: "YPosition",
    288: "FreeOffsets",
    289: "FreeByteCounts",
    290: "GrayResponseUnit",
    291: "GrayResponseCurve",
    292: "T4Options",
    293: "T6Options",
    296: "ResolutionUnit",
    297: "PageNumber",
    301: "TransferFunction",
    305: "Software",
    306: "DateTime",
    315: "Artist",
    316: "HostComputer",
    317: "Predictor",
    318: "WhitePoint",
    319: "PrimaryChromaticities",
    320: "ColorMap",
    321: "HalftoneHints",
    322: "TileWidth",
    323: "TileLength",
    324: "TileOffsets",
    325: "TileByteCounts",
    332: "InkSet",
    333: "InkNames",
    334: "NumberOfInks",
    336: "DotRange",
    337: "TargetPrinter",
    338: "ExtraSamples",
    339: "SampleFormat",
    340: "SMinSampleValue",
    341: "SMaxSampleValue",
    342: "TransferRange",
    512: "JPEGProc",
    513: "JPEGInterchangeFormat",
    514: "JPEGInterchangeFormatLngth",
    515: "JPEGRestartInterval",
    517: "JPEGLosslessPredictors",
    518: "JPEGPointTransforms",
    519: "JPEGQTables",
    520: "JPEGDCTables",
    521: "JPEGACTables",
    529: "YCbCrCoefficients",
    530: "YCbCrSubSampling",
    531: "YCbCrPositioning",
    532: "ReferenceBlackWhite",
    33432: "Copyright",
}

# Reverse map - keyed by name
tags_by_name = {}
for id, name in tags_by_id.items():
    tags_by_name[name] = id


def _normalize_key(key):
    if isinstance(key, str):
        return tags_by_name.get(key, key)
    return key


# Decode the 12 byte tag value
def _decode_tiff_value(data, offset):
    chunk = data[offset:offset+12]
    if len(chunk)!=12:
        raise ValueError, "Expected exactly 12 bytes for a tag header"
    tag, typ, num_vals, val_off = struct.unpack("hhii", chunk)
    if typ==1: # byte
        # fits in val_off
        val = val_off
    elif typ==2: #ascii
        val = data[val_off:val_off+num_vals-1]
    elif typ==3: # short
        # fits in val_off
        val = val_off
    elif typ==4: # int
        # fits in val_off
        val = val_off
    elif typ==5:
        num, dem = struct.unpack("II", data[val_off:val_off+8])
        val = num/dem
    else:
        raise ValueError, "Unknown tag type %d" % (typ,)
    return IFDEntry(tag, val, typ)


# An Image File Directory entry.
class IFDEntry:
    def __init__(self, tag_id, value, typ = None):
        self.typ = typ
        self.id = tag_id
        self.value = value
        self.name = tags_by_id.get(tag_id)
    def format_name(self):
        if self.name is not None:
            return self.name
        return str(self.id)


# A dictionary-like object holding all tags for
# the image.  You can use either an integer ID,
# or the tag name if known.
class Exif:
    def __init__(self, data=None):
        """
        Construct an Exif object, based on a block of data
        obtained from an image, such as a JPEG or TIFF file
        
        """
        self.entries = {}
        self.dirty = 0
                        
        if not data:
            # no exif data in jpeg file
            return
            
        if data[0] != 'I' or data[1] != 'I':
            raise ValueError, 'No I'
        magic, = struct.unpack("xxh", data[:4])
        if magic != 42:
            raise ValueError, "Wrong magic"
        offset = 4
        while 1:
            offset, = struct.unpack("i", data[offset:offset+4])
            if offset == 0:
                break
            num_entries, = struct.unpack("h", data[offset:offset+2])
            offset += 2
            # Get the 12 byte tag, and decode it.
            for i in range(num_entries):
                tag = _decode_tiff_value(data, offset)
                self[tag.id] = tag
                offset += 12
        
    def keys(self):
        return self.entries.keys()
        
    def items(self):
        return self.entries.items()
        
    def values(self):
        return self.entries.values()
        
    def __getitem__(self, key):
        key = _normalize_key(key)
        return self.entries[key]
        
    def __setitem__(self, key, item):
        assert isinstance(item, IFDEntry)
        key = _normalize_key(key)
        self.entries[key] = item
        self.dirty = 1
        
    def __delitem__(self, key):
        key = _normalize_key(key)
        del self.entries[key]
        self.dirty = 1


# 
# Test code that reads info from a JPEG file
#
if __name__ == '__main__':
    import sys, jfif
    
    img = jfif.JFIF(sys.argv[1])
    exif_info = img.getExif()
    for tag in exif_info.values():
        print "    %s: %s" % (tag.format_name(), tag.value)           

#
# --- EOF ----    
#
