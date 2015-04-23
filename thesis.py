from subprocess import Popen, PIPE
### Functions

def getClientList(text):
	output = []
	try:
		text.splitlines(True)
	except AttributeError:
		pass
	for line in text:
		print line
		if "*CLIENT" in line:
			temp = line.split("*Client", 1)
			output.add(temp)
	return output
	
## Main
p = Popen(['/bin/bash','-i', '-c','wlist'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
# output, err = p.communicate(b"input data that is passed to subprocess' stdin")
output, err = p.communicate()
rc = p.returncode
print getClientList(output)
