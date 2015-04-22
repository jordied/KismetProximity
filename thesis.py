from subprocess import Popen, PIPE

p = Popen(['ls', '-l'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
# output, err = p.communicate(b"input data that is passed to subprocess' stdin")
output, err = p.communicate()
rc = p.returncode
print output