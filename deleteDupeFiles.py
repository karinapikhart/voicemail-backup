# @karinapikhart

# version history
# 2018-07-21 V0.1

# Background:
# BEWARE!!! THIS SCRIPT CAN DELETE FILES!!!!!! VERY DANGEROUS!!!!
# The voicemailRecovery tool produces a lot of files, but there isn't sufficient metadata to easily compare files and remove dupes
# This is a quick script that allows files to be compared and dupes to be deleted

# Compatible with:
# ...

# Instructions:
# ...

# Lessons learned:
# ...

# To do:
# ...

##########
# IMPORT #
##########

import os
import subprocess
import sys
import pprint
import shutil

##########
# INPUTS #
##########

layered_source_directory = '/Users/Karina/Dropbox/Projects/software/VoicemailBackup/recovered-voicemails'
flattened_destination_directory = '/Users/Karina/Dropbox/Projects/software/VoicemailBackup/recovered-voicemails-dedupedAndFlattened'

#############
# FUNCTIONS #
#############

def print_basic_directory_metrics(directory):

    print
    print 'Contents of ' + directory.split('/')[-1]

    directory_contents = os.walk(directory)
    for dirpath, dirnames, filenames in directory_contents:
        print dirpath, len(dirnames), len(filenames)

    return

def get_md5(full_filepath):
    md5 = subprocess.check_output('md5 -q ' + full_filepath, shell=True).strip()
    return md5

def get_md5_list(directory):
    md5s = []
    directory_contents = os.walk(directory)
    for dirpath, dirnames, filenames in directory_contents:
        for filename in filenames:
            full_filepath = dirpath + '/' + filename
            md5 = get_md5(full_filepath)
            md5s.append(md5)

    return md5s

def find_dupes(master_md5s, directory):
    dupe_files = []
    directory_contents = os.walk(directory)
    for dirpath, dirnames, filenames in directory_contents:
        for filename in filenames:
            full_filepath = dirpath + '/' + filename
            md5 = get_md5(full_filepath)

            if md5 in master_md5s:
                dupe_files.append(full_filepath)

    return dupe_files

def sort_files_by_md5(directory):
    files = {}
    directory_contents = os.walk(directory)
    for dirpath, dirnames, filenames in directory_contents:
        for filename in filenames:
            full_filepath = dirpath + '/' + filename
            md5 = get_md5(full_filepath)

            if md5 not in files.keys():
                files[md5] = []

            files[md5] = files[md5] + [full_filepath]

    return files

def get_dupe_files(md5_file_dict):
    dupe_files = {}
    for md5 in md5_file_dict:
        if len(md5_file_dict[md5]) > 1:
            dupe_files[md5] = md5_file_dict[md5]

    return dupe_files

def delete_dupes(file_list):
    print
    print 'The following files are all identical:'
    pprint.pprint(file_list)

    file_to_keep = raw_input('Which one would you like to keep? All others will be deleted')
    if file_to_keep not in file_list:
        print 'Invalid file to keep. Exiting script'
        sys.exit()
    else:
        for file in file_list:
            if file != file_to_keep:
                print 'deleting ' + file
                # os.remove(file)
    return

def copy_unique_files_to_destination(md5_dictionary, destination_folder):
    final_file_names = []

    for md5 in md5_dictionary:
        file_to_copy = md5_dictionary[md5][0]
        file_name = file_to_copy.split('/')[-1]

        # found that files with different md5 can have same file name
        # HACK to deal with this: prefix the filename with a hyphen...
        if file_name not in final_file_names:
            final_file_names.append(file_name)
            shutil.copy(file_to_copy, destination_folder)
        else:
            shutil.copy(file_to_copy, destination_folder + '/-' + file_name)

    return

########
# MAIN #
########

if __name__ == "__main__":

    ##############################
    # 1. Compare md5 of all files in source directory
    ##############################

    all_files_by_md5 = sort_files_by_md5(layered_source_directory)
    print 'unique md5s: ' + str(len(all_files_by_md5))

    ##############################
    # 2. Put 1 copy of each unique file into destination directory
    ##############################

    copy_unique_files_to_destination(all_files_by_md5, flattened_destination_directory)
    print 'files in destination: ' + str(len(os.listdir(flattened_destination_directory)))

    ##############################
    # 3. Exit
    ##############################

    sys.exit()

    ###############################################################################################################
    ###############################################################################################################
    ###############################################################################################################

    # OLD STUFF

    # dupe_files = get_dupe_files(all_files_by_md5)

    ##############################
    # 3. Check before proceeding
    ##############################

    #proceed = raw_input('Proceeding past this point will start the process of deleting duplicate files. Please type PROCEED if you understand the risks.')
    #if proceed != 'PROCEED':
    #    sys.exit()

    ##############################
    # 4. Delete files
    ##############################

    #for md5 in dupe_files:
    #    delete_dupes(dupe_files[md5])

    ##############################

    #pprint.pprint(dupe_files)
    #print len(dupe_files)


    # num_file_copies = {}
    # for md5 in dupe_files:
    #     num_files = len(dupe_files[md5])
    #     if num_files not in num_file_copies.keys():
    #         num_file_copies[num_files] = 0
    #     num_file_copies[num_files] += 1
    # pprint.pprint(num_file_copies)