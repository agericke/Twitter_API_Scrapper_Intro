"""
Summarize data.
"""
import os, sys

def main(args):
	print("SUMMARY FOR collect.py:")
	os.system('python collect.py')
	print("\n\n")
	print("SUMMARY FOR cluster.py:")
	if len(args) > 1:
		#arg = 'python cluster.py %s' 
		os.system('python cluster.py %s' % args[1])
	else:
		os.system('python cluster.py')
	print("\n\n")
	print("SUMMARY FOR classify.py:")
	os.system('python classify.py')
if __name__ == "__main__":
    main(sys.argv)
