import zlib
import struct
import re
import os

typeIndex = {'ULONG': 4,
             'U24': 3,
             'USHORT': 2,
             'UBYTE': 1,
             'LINK': 0,
             'DATA': 0}

packLongSize = struct.calcsize('L')


def path_join(dir_name, file_name):
    return os.path.join(dir_name, file_name)


class decompose:
    def parse_format(self):
        select = 0
        fconfig = open(path_join(self.dir, 'config.cft'), 'rb')
        for line in fconfig:
            result = re.match(r'\$(\S+)\s*=\s*(\S+)', line)
            if result:
                if result.group(1) == 'CONTENT,OFFSET':
                    self.formatStr[1] = typeIndex[result.group(2)]
                    select = 2
                else:
                    self.formatStr[select] += typeIndex[result.group(2)]

    def write_offset_index(self):
        i = 0
        fdata = open(path_join(self.dir, 'files.dat'), 'rb')
        while True:
            i += 1
            if len(fdata.read(self.formatStr[0])) == 0:
                break
            _buf = fdata.read(self.formatStr[1])
            self.offsets.append(
                struct.unpack('L', str(_buf + (packLongSize - self.formatStr[1]) * '\x00'))[0])
            fdata.read(self.formatStr[2])

    def inflate_tda(self):
        fin = open(path_join(self.dir, 'CONTENT.tda'), 'rb')
        fdst = open(path_join(self.outdir, 'output'), 'wb')
        findex = open(path_join(self.dir, 'CONTENT.tda.tdz'), 'rb')
        byte = []
        while True:
            bin = findex.read(8)
            if len(bin) == 0:
                break
            byte.append(struct.unpack('ii', str(bin)))
        i = 0
        print 'Now decompressing...'
        for xi, bytei in byte:
            i += 1
            dedata = zlib.decompress(fin.read(bytei))
            fdst.write(dedata)
        print 'Done! Total %d entries.' % i

    def write_files(self):
        fin = open(path_join(self.dir, 'NAME.tda'), 'rb')
        raw = fin.read()
        name = raw.split('\x00')

        fin = open(path_join(self.outdir, 'output'), 'rb')
        for i in range(len(self.offsets)):
            fout = open(path_join(self.outdir, name[i]), 'wb')
            if i == len(self.offsets) - 1:
                fout.write(fin.read()[:-1])
            else:
                fout.write(fin.read(self.offsets[i + 1] - self.offsets[i])[:-1])
            print 'Now writing separate files:' + str(i + 1) + '\r',
        print '\nDone!'

    def __init__(self, dir, outdir):
        self.dir = dir
        self.outdir = outdir
        self.formatStr = [0, 0, 0]
        self.offsets = []
        self.parse_format()
        self.write_offset_index()
