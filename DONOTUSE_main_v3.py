#THIS IS BUGGED, SEEN REPEATED CHUNKS FOR HOURS UPON EXECUTION, BUT THERE IS AN IMPROVEMENT HERE IF YOU CAN BE BOTHERED TAKING IT FORWARD#
from wif_helper import *
from cryptos import *
from pathlib import Path
import multiprocessing as mp, os
import argparse

#Initialise our argument parser
parser = argparse.ArgumentParser()

#Add our long and short hand arguments along with help info
parser.add_argument("--dir", "-d", help="set directory to scan for text files")
parser.add_argument("--out", "-o", help="set the output filename, it saves alongside discovered files")
parser.add_argument("--enc", "-e", help="set file encoding as a string, eg 'UTF-8','ISO-8859-1', default is ISO-8859-1")

#Get ref to args
args = parser.parse_args()

#Global variables
log_info_enabled = False
output_file = None
#Only tested with lst files as it was how I generated my past potential brain wallets
#rootdir should ideally be a folder with sub directories which each have a single text file, eg: if D:/seed_phrases/ then D:/seed_phrases/seeds_01/seeds_01.lst, D:/seed_phrases/seeds_02/seeds_02.lst, etc
rootdir = '.'
output_filename = 'found_addresses.txt'
file_encoding = 'ISO-8859-1'

#Add supported filetypes you want to be parsed
known_exts = ['.txt','.lst']

#Set vals with args
if args.dir is not None:
    rootdir = args.dir
if args.out is not None:
    output_filename = args.out
if args.enc is not None:
    file_encoding = args.end

#Set up our blockchain connection
c = Bitcoin()

global counter

#Main method
def main():
    #Loop through each sub directory to find files, assumes 1 output in each directory and will append results
    for subdir, dirs, files in os.walk(rootdir):
        for file in files:
            if file.endswith(tuple(known_exts)) and not file.endswith(output_filename):
                #Get a reference to this file's absolute path
                filepath = os.path.join(subdir, file)
                
                #Call our output file generation method at the start of this program 
                generate_output(subdir)

                #Create a multi processing pool to utilise all cores and a blank array of jobs 
                pool = mp.Pool()
                jobs = []

                #Create jobs by splitting our file into chunks
                print('Splitting file: {} into chunks and adding jobs into list'.format(filepath))
                for chunkStart,chunkSize in chunkify(filepath):
                    jobs.append( pool.apply_async(process_wrapper,(filepath,chunkStart,chunkSize)) )

                #Wait for all of our jobs to finish
                print('Jobs added for {0}, starting processing of jobs'.format(filepath))
                for job in jobs:
                    job.get()

                #Clean up
                log_info('Finished processing {0} - cleaning up'.format(filepath))
                pool.close()

                #We are done with this file, rename it so we know it's complete
                root, ext = os.path.splitext(filepath)
                os.rename(filepath, '{0}_complete{1}'.format(root,ext))
    return

#Helper methods
def process_wrapper(filepath,chunkStart, chunkSize):
    with open(filepath, 'r', encoding=file_encoding) as input_file:
        input_file.seek(chunkStart)
        lines = input_file.read(chunkSize).splitlines()
        for line in lines:
            process_line(line)

def chunkify(fname,size=1024*1024):
    fileEnd = os.path.getsize(fname)
    with open(fname, 'rb') as f:
        chunkEnd = f.tell()
        
        while True:
            chunkStart = chunkEnd
            f.seek(size,1)
            f.readline()
            chunkEnd = f.tell()
            yield chunkStart, chunkEnd - chunkStart
            if chunkEnd > fileEnd:
                break

def process_line(line):
    check_address_using_passphrase(line)
    print('Finished execution for: ' + line)
    return line

def generate_output(subdir):
    #Check for output file in execution dir, if found don't create
    results_file = os.path.join(subdir, output_filename)
    matched = os.path.isfile(results_file)
    
    if matched == True:
        print('output file {0} exists in directory {0}, skipping creation'.format(output_filename, subdir))
    else:
        #Create and close file for now
        output_file = open(results_file, 'w+')
        output_file.close()
        print('output file created as {0} in directory {1}'.format(output_filename, subdir))
    return

def check_address_using_passphrase(passphrase):
    #Use provided passphrase for our brainwallet, sha256 to get a privatekey
    log_info('passphrase: ' + passphrase)
    privkey = sha256(passphrase)
    log_info('privatekey: ' + privkey)

    #Turn our privatekey into a publickey then an address 
    pubkey = c.privtopub(privkey)
    log_info('publickey: ' + pubkey)
    address = c.pubtoaddr(pubkey)
    log_info('address: ' + address)

    #In order to import our privatekey into most wallets we need it in wif format
    wif_privkey = gen_wif_key(privkey)
    wif_str = ''.join(map(chr, wif_privkey))
    log_info('wif_privkey: ' + wif_str)

    #Use our address to check for any unspent balance on this address
    try:
        inputs = c.unspent(address)
        if any(inputs):
            #Always log found addresses, in case file shits the bed
            print('address has balance: ' + address)
            with open('found_addresses.txt', 'a') as output_file:
                output_file.write(wif_str+';\n')
        else:
            log_info('address has no balance: ' + address)
    except:
        log_info('address has no transactions, skipping for: ' + address)
    return
        
def log_info(text):
    if(log_info_enabled == True):
        print(text)
    return

#Execution code
if __name__ == "__main__":
    main()
