
import unicodedata, re
from subprocess import Popen, PIPE
### Functions






def remove_control_chars(s):
        #all_chars = (unichr(i) for i in xrange(0x110000))
        #control_chars = ''.join(c for c in all_chars if unicodedata.category(c) == 'Cc')
        # or equivalently and much more efficiently
        control_chars = ''.join(map(unichr, range(0,32) + range(127,160)))
        control_char_re = re.compile('[%s]' % re.escape(control_chars))
        return control_char_re.sub('', s)

def getClientList(intext):
	output = []
	#print "Original Text:\n", repr(intext)
	try:
		intext.splitlines(True)
	except AttributeError:
		pass
	for line in intext:
		# print line
		#regex = re.compile('[\x7f\x80]');
		text = remove_control_chars(line)
		#print repr(text)
		output.append(text)
	return ''.join(output)

if __name__ == "__main__":
    p = Popen(['/bin/bash','-i', '-c','wlist'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    # output, err = p.communicate(b"input data that is passed to subprocess' stdin")
    output, err = p.communicate()
    rc = p.returncode
    print "Formatted Text:", getClientList(output)
