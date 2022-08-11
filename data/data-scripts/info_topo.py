import os
import sys
import json
import re
import itertools
import argparse
from   urllib.parse import urlparse
#from argparse import RawTextHelpFormatter
import pathlib
import yaml
import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET


class SmartFormatter(argparse.HelpFormatter):

    def _split_lines(self, text, width):
        if text.startswith('R|'):
            return text[2:].splitlines()  
        # this is the RawTextHelpFormatter._split_lines
        return argparse.HelpFormatter._split_lines(self, text, width)

from argparse import ArgumentParser

parser = ArgumentParser(description='test', formatter_class=SmartFormatter)


import time
import datetime

x = datetime.datetime.now()

test_start = x.strftime("%b %d %Y %H:%M:%S")

epoch_sec = "{0:.0f}".format(time.time())

key_counts            = dict()
key_crashes           = dict()

# We need to categorize links as to how they are handled for converting their
# paths to node ids. This isn't used until later in the script 
# (search on the variable named "link_categories_regex" to find it). But, here,
# near the top of the script where I have a full 80 characters width, I create
# one big regex, with alternation between three sub-regexen. To stay within 80 
# characters, and keep it readable, I write out the sub-rexeen into an array,
# which I will `join` on that method of the alternation ("|") character. 
# Remember that the alternation group will require keeping enclosing parens,
# one at the start of the first group, and one at the end of the last group.
# The regex that results from the join separates a link into the three 
# alternatives: 
# - An xref with a filepath, starting with "../../"
# - An xref with a url, starting with "http" 
# - A conref with a filepath, starting with "../../"
# At last try, all links were successfully intercepted by the regex, but this
# could change when run over different corpora, or if links are changed in doc.
# If any link ever does not match one of these alternatives, the script will
# enter debug mode, just before a statement that prints the offending link.
# That debug session can be used as a lab to determine how to change the 
# corresponding regex, if necessary. 

link_categories_regex_substrings = [ 
r'^((<xref\s+href='\
  + '"((\.\./\.\./(\.\./)*?([^#.]+\.(?:xml|html?)))(\#([^"]+))?)")',
r'(<xref\s+href=(\'|")(https?://[^\10]+)\10)',
r'(conref=(\'|")((\.\./\.\./(\.\./)*?([^#]+\.xml))/?(\#([^\13]+))?\13)))']

# The `join` method of the pipe or alternation character ("|"):
link_categories_regex = "|".join(link_categories_regex_substrings)

# Give the node-name components an obviously fake name. 
# These should get replaced, but when they don't, and show up in the 
# node-names, we know that there is a hole in the assignments somewhere. 
portal = 'fee'
book   = 'fie'
area   = 'foe'
file   = 'fum'

# This "files_of_interest" is the main internal table that holds our findings.
files_of_interest = dict()

# This is for diagnostics, to hold any instances of targets missed by the
# link_categories_regex_substrings that get joined into the link_categories_
# regex.
unresolved_targets = dict()

# This "ext_dom_agglom" (for "external domain agglomeration") had been for 
# marshalling external domains for later determining the weight, especially 
# when I had thought that I needed to measure the weight of the domain. I now
# believe this is not what we want, but I need to consult Tyrin to find out
# exactly what we do want to do. So, I don't want to get rid of this now.
ext_dom_agglom = dict()

# These are the broad classifications we originally said we were looking 
# with regard to links out from documents. In practical terms, it is a finer
# division, but we keep this because we want to know this detail. 
constructs_of_interest = {
  'xref': re.compile(
    r'<xref\s+href="(?:\.\.\/\.\.\/|https?:\/\/)[^"]+"', re.MULTILINE),                 
  'conref': re.compile(
    r'(conref=(\'|")(?:\.\.\/\.\.\/|https?:\/\/)[^\2]+?\2)', re.MULTILINE),
}

# The values assigned in the last block of code are not printable. This
# operation makes them printable for diagnostics.
printable_constructs = \
  { name: v.pattern for (name, v) in constructs_of_interest.items()}

# The doc_title_rgx may now be obsolete. I need to follow through on whether it
# is still needed before I get rid of it. 
doc_title_rgx = re.compile(
  r'<title( [^<]+)?>(<[^<]+>)*?(.+?)(<.*?>)*?</title>', re.MULTILINE)

def remove_start_dir_for_display (root_dir, rel_path):
    '''
    Only for node labels, which appear in the graph, remove the start dir 
    from the start of the path. This is because the start dir will be redund-
    ant, appearing on every path. 

    Don't use this function for anything that will need to know where the 
    actual file is, and run code on it. 
    '''
    # Using the root_dir, I take the last element of it out of it (the 
    # start_dir) so that I can remove it from the reported path or reported 
    # path derivative (such as the node label). I use os.sep in place of 
    # "/" or "\".
    os_root_dir_pattern = re.compile(
      f'^(?:{os.sep}[^{os.sep}]+)*{os.sep}([^{os.sep}]+)$')
    strt_dir = re.sub(os_root_dir_pattern, r'\1', root_dir)

    # Having isolated the start_dir, I form the regex to remove it
    # from the start of the path.
    os_start_dir_pattern = re.compile(
      f'^{strt_dir}{os.sep}(.*)$')
    path_sans_start_dir = re.sub(os_start_dir_pattern, r'\1', rel_path)

    return path_sans_start_dir
    

def list_relpaths_by_filename (root_dir, group_lookup, group_default_color,
  sf_internal_domains, files_of_interest, nn_elem_delim, nn_area_delim,
  filetype, key_width):
    '''
    This function uses Python's file recursion library to get a listing of the 
    file names and their paths into memory. There, I can refer to them much
    more economically than with further recursions. 

    When using this file as a script, the "root_dir" is set in the 
    parameters.yaml file, overridden on the command line if necessary, and 
    passed into this function in the '__name__ == "__main__"' part of the 
    script call during the
    and That listing is called "files_of_interest".

    The name is a filename of the filetype given, with a default of
    "xml" but it could be also "md" (athough that is not tested yet).
    The values are a list of dicts, each containing the path, an 
    SHA256 hash of the path and filename, a key: a subset of least
    significant digits of the hash to the width specified in key_width. 

    This function returns the files_of_interest dict.
    '''
    if files_of_interest is None:
        files_of_interest = dict()

    for root, subFolders, files in os.walk(root_dir, topdown=True):
        for file in files:
            filetype_regex = f'^.*\.{filetype}$'
            a_file = re.search(filetype_regex, file)
            if (a_file):
                if path_root == 'relative':
                  rel_path = os.path.relpath(
                    os.path.join(root,file), start=os.curdir)
                elif path_root == 'absolute':
                  rel_path = os.path.abspath(
                    os.path.join(root,file))

                ensure_files_of_interest_entry(root_dir, rel_path,
                  group_lookup, group_default_color, sf_internal_domains, 
                  nn_elem_delim, nn_area_delim, files_of_interest, key_width)
                files_of_interest[file]['paths'][rel_path]\
                  ['history count'] += 1
                files_of_interest[file]['paths'][rel_path]['history']\
                  .append(f"File found in initial recursion of {root_dir}.")
    
    # This block, and the next, are to determine whether the key has any 
    # duplicates (key crashes). The key is the right-anchored substring of the
    # hash of the node id, and is <key_width> wide. The key width is set in
    # the *defaults.yaml file. Widening the key_width (making it a higher 
    # integer) reduces the chances of a key crash and is the action that should
    # be taken if there are key crashes. To give a of leeway, I've followed the
    # policy of setting the width 2 more than the level at which the key crash
    # disappears.
    for key in key_counts:
        if key_counts[key] > 1:
            key_crashes[key] = key_counts[key]

    for key in key_crashes:
        print(f"key crash: {key_crashes[key]} instances of key: {key}."\
          + " Widen the key_width.")
        print(f"{len(key_crashes.keys())} key_crashes total.")

    return(files_of_interest)

def ensure_files_of_interest_entry(root_dir, rel_path, group_lookup, 
  group_default_color, sf_internal_domains, nn_elem_delim, nn_area_delim, 
  files_of_interest, key_width, key_counts=key_counts):
    '''
    This function establishes the basic record that will go into our main in-
    memory table to hold our findings about each file. Each of those records in
    this table is potentially re-entered, (potentially several times) later, 
    by the function named "analyze_files_for_links()".
    function named The "root_dir" value should be an
    absolute path to the starting directory. When running this file as a 
    script, it is set in the defaults.yaml file, and passed in from that file
    or the overriding CL value, through the calling function. The "rel_path" is
    found and set by the calling function. The "nn_elem_delim" and
    "nn_area_delim" are set in the defaults.yaml file. The 
    "files_of_interest" parameter is the main data structure, which starts life
    as a dictionary, and is repeatedly passed in by the calling function. The
    "key_width" parameter is also from the parameters.yaml file. It controls 
    count of (least significant) digits taken from the right hand end of the 
    SHA digest. This is important because we want a compact key, easy to use
    as a table joining key, but not so short as to be repeated among all the
    files and paths. The policy I have been following 


    '''
    file_name = re.sub(
       r'^.*?/([^/]+)$', r'\1', rel_path)
    rel_parent_dir = re.sub(
      r'^(.*?)/[^/]+$', r'\1', rel_path)
    rel_parent_dir_path = Path(rel_path).name

    if file_name not in files_of_interest:
        files_of_interest[file_name] = {
          'paths': {}, 'filename count': 0}

    if rel_path not in files_of_interest[file_name]['paths']:
        the_hex_hash = hashlib.sha256(
          rel_path.encode()).hexdigest()
        the_key  = the_hex_hash[-key_width:]
        node_id, portal, content_domain, label_part_1of2, title, label, color, \
          cloud = \
          path_or_url_to_node(rel_path, group_lookup, group_default_color, 
            sf_internal_domains, nn_elem_delim, nn_area_delim)

        path_sans_start_dir = remove_start_dir_for_display (root_dir, rel_path)
        
        path_record = {
          'path sans start dir': path_sans_start_dir,
          'vim searchable': ".".join(rel_path.split(os.sep)), 
          'content domain': content_domain,
          'node id': node_id,
          'portal': portal,
          'internal title': None,   # Doc title actual value must wait until
                             #'analyze_file_for_links', when the doc is opened. 
          'label': label_part_1of2, # This, too, must wait for the file to be
                             # opened in 'analyze_file_for_links', or possibly
                             # at some other time (for urls). Also this had 
                             # been 'target label', but it occurs to me that it
                             # should be the same value for targe or source, 
                             # so I changed it to just 'label'.
          'cloud': cloud,
          'color': color,
          'hash': the_hex_hash,
          'key': the_key,
          'target nodes': {},
          'specially handled constructs': { 
          
            'xref': {'xref count': 0, 'xref actual instances': {}},
            'conref': {'conref count': 0, 'conref actual instances': {}}
          },
          'history count': 0,
          'history': [],
          'breadth': 0,
          'depth': 0,


        }
        files_of_interest[file_name]['paths'][rel_path] = path_record
        if the_key not in key_counts:
            key_counts[the_key] = 0
        key_counts[the_key] += 1

             
def store_actual_constructs(xref_or_conref, 
  file_name,
  rel_path,
  doc_node_name, 
  weight_counting_store, 
  construct_matches, 
  data_structure=files_of_interest):
      xcref = xref_or_conref
      xcref_count = f'{xcref} count'
      xcref_actual_instances = f'{xcref} actual instances'
      if xcref is None:
          import pdb; pdb.set_trace()
      files_of_interest[file_name]['paths'][rel_path]\
        ['specially handled constructs'][xcref][xcref_count] = len(
          construct_matches)
      files_of_interest[file_name]['paths'][rel_path]\
        ['specially handled constructs'][xcref][xcref_actual_instances] = \
          [re.sub(r'\n?\s+', r' ', construct) for construct in \
          construct_matches]

      for actual_ref in weight_counting_store:
          if not actual_ref in files_of_interest[file_name]['paths'][rel_path]\
            ['specially handled constructs']\
            [xcref][xcref_actual_instances]:
              files_of_interest[file_name]['paths'][rel_path]\
                ['target node'] = []
              # This will be made redundant by the new 'target files'
              # but I will keep it for now.
              files_of_interest[file_name]['paths'][rel_path]\
                ['specially handled constructs'][xcref]\
                [xcref_actual_instances][actual_ref] = {'weight': 0}
          files_of_interest[file]['paths'][rel_path]\
            ['specially handled constructs'][xcref]\
            [xcref_actual_instances][actual_ref]['weight'] += 1

def slugified(string):

    string = re.sub(r'[\n\s\t]+',' ', string)
    string = re.sub(r'^[\s]+','', string)
    string = re.sub(r'[\s]+$','', string)
    # Tyrin's replacments from her data cleanup script:
    # to_replace = {'(': '',
    #               ')': '',
    #               'fee::':'',
    #               'fie::':'',
    #               '::':':',
    #               '\'':'',
    #               '}': '',
    #               '{':'',
    #               ' ':''
    #               #'.':'_',
    #               #'://':':'
    #               #'\//':'_',
    #              }
    string = re.sub(r'[(){}\\]+',r'', string)
    string = re.sub(r'(?:fee:|fie:):',r'', string)
    string = re.sub(r'::+',r':', string)
    string = re.sub(r'\.',r'_', string)
    string = re.sub(r'://',r':', string)
    string = re.sub(r'//',r'_', string)
    # I am not sure what the conversion immediately above means, and am adding
    # the one below as I think this what is intended, AND it matches what is in
    # Tyrin's filterdata spreasheet.  
    string = re.sub(r'/',r'_', string)
    return string


def url_to_label(url):
    '''
    Convert an "external URL" to a slugified label component, similar to the
    way a file-path is converted in local_path_to_taxonomy(). 
    x

    I removed the formal params nn_elem_delim, and nn_area_delim as I am just
    using Tyrin's replacements from her data cleanup script. In fact, we may be
    able to eliminate this function now, since it's just a wrapper for 
    `slugified()`. I won't do that right away, in case it turns out that Tyrin
    or I want anything else in here. 
    '''
    label = slugified(url)
    return label

def local_path_to_taxonomy(root_dir, rel_path_below_start_dir,
  node_name_element_primary_delimiter, area_element_secondary_delimiter):
    '''
    Convert any path into a four element taxonomy designation represent-
    ing: Portal, Domain, Area and File. Those four are delimited by a character
    that is set in the defaults.yaml file. Area may have sub-elements delimited
    by a different delimiter, also set in the defaults.yaml file. 

    This function is called by `path_or_url_to_node()`. 
    '''

    # First, ensure that the value coming is a filesystem file path, not a URL.
    filesystem_file_path_match = re.search(
      r'^/?([^/]+/)*[^/]+\.(md|xml|html?)$', rel_path_below_start_dir)

    if filesystem_file_path_match:
         
        # Isolate the directory name from before the relative path. This is an
        # artifact of the root dir named in the defaults as the starting place
        # of the script.

        # Keep only the part of the path below the root directory name. In
        # other words, get rid of the directory name and its slash delimiter
        # at the start of the path. Also, remove the dot and extension at
        # the end of the filename, by taking only the part before it in the
        # capturing group.
        path_below_root_dir = re.sub(r'^'+ r'(.*?)\.(md|xml|html?)$', r'\1', 
          rel_path_below_start_dir)

        # Break the remaining path up into an array of path elements
        path_stack = path_below_root_dir.split('/')

        # Establish the name "normal_path_stack" as the receiver of the
        # normalized set of elements to form the 4 element label under 
        # "portal", "domain", "area", "file".
        normal_path_stack = []

        # If there are more than 4 elements in the path, take the first 2, make
        # the third through penultimate into its own array to be dealt with in
        # a moment, then, the last of the elements. 
        if len(path_stack) > 4:
            normal_path_stack = path_stack[0:2] + [path_stack[2:-1]] + \
              [path_stack[-1]]

        # If there are exactly 4 elements in the path, just use them directly
        # as the "portal", "domain", "area" and "file".
        elif len(path_stack) == 4:
            normal_path_stack = path_stack

        # If there are three elements, the third will be "no area".
        elif len(path_stack) == 3:
            normal_path_stack = [path_stack[0], path_stack[1]] +\
              ['no_area', path_stack[2]]

        # If there are only 2 elements, the first will be "no domain", and the
        # third is "no area".
        elif len(path_stack) == 2:
            normal_path_stack = ['no_portal', path_stack[0]] + \
              ['no_area', path_stack[1]]

        # If there were more than 4 elements total, then the third through 
        # penultimate will be in an array by itself as the Area. To keep it 
        # clear that the Area is a series of folders but separate from the
        # folders comprising "portal", "domain" and "file", a different delimi-
        # ter is allowed within the "area". 
        if type(normal_path_stack[2]) == type([]):
            normal_path_stack[2] = \
              area_element_secondary_delimiter.join(normal_path_stack[2])

        return node_name_element_primary_delimiter.join(normal_path_stack) 
    else:
        # None is a blunt signal to the receiving function that
        # we do not have a valid path to deal with. We will use it as a 
        # signal there to switch to processing a URL. 
        return None


def path_or_url_to_node(actionable_path_or_url, group_lookup_table, 
  group_default_color, sf_internal_domains, nn_elem_delim, nn_area_delim):
    '''
    Take a path, and apply rules or table lookups to it to convert it into a 
    node id in our format. This is to unify differences between:

    - Python file recursion's version of a file name and the reference p
      in the file itself. 
    - Repository filesystem and app server (HTML) paths to a file.
    - Version differences between files, mainly XML vs. an HTML extension). 
      Also (eventually) Markdown. 

    The delimiting of the output can vary a bit, based on user-controlled
    settings in defaults.yaml file. Whatever is chosen there should:

    - Be distinct from the slashed delimiting that is present in a filesystem 
      or HTML path.
    - Not use characters, or a character sequence, likely to be present in the
      path already, such as a single dash.
    - The character or character sequence is permitted in the context of the 
      graphing package. 

    This is to make files that we have successfully given a node id stand out
    as visually distinct, thereby disambiguating them from those we have not.  
      
    The goal is to allow any file to appear as either the source or the target
    (or both) of the relationships we map. We fully expect there to be 
    outliers, i.e. filenames 
    are not mapped to our node id format. These will represent both the gap 
    in mapping our files, as well as external links that have no originating 
    XML or Markdown on our site. We will drive this gap to a minimum by writing
    of table-based rules to properly map to the format of this function where 
    possible. Ideally this will leave only true outliers: the external links 
    that have no originating XML or Markdown in our site. 
    
    This function is first called on the path of each file that is opened, then 
    again on each of its pointed-to files. As long as the recursive script that
    calls this function is started at, or above the last common root of all 
    files, the location of the opened file should establish the "portal", 
    "book", & "area", as well as the "file" as elements of the node id. The 
    pointed-to files will either be a file path relative to the location of the 
    opened file, or a full HTML url. 

    File paths from the opened file, will use
    double dot nodes ("../../") to represent parents. This function needs to 
    infer the value that replaces the double dotted node. That can usually be 
    the corresponding element of the file that was opened. 

    For HTML files, this function will need to use an internal table (a dict)
    to supply the file path to the originating file. I am going 

    First, and this should work for most of the xml files opened, the path
    is subject to a regex intended to pull out "portal", "book", "area", and
    "file". If "help" is the book, that occurs at the same level as the other
    portals, so the rule below will set the portal also to "help" for any. 
    Tyrin Avery has commented that we may need to do similarly for others: 
    ("for release notes and some others, it should probably be 'help' by 
    default, rather than through the folder name.")

    After normalizing the path of the file that was opened, reading the file 
    contents, and extracting the links, we should be able to run this same
    function on each of the links. 
 
    Links that are relative file paths should, for the most part, work. Where
    they don't, the failure should usually be detectable, if not obvious, 
    and should share characteristics that make addressing groups of them 
    easier. If nothing else, a series of table lookups will work to place each
    of the relative files to some normalized form of file. 

    Links that are URLs will not work at first but should fail in a benign way: 
    essentially, each url will be a leaf node of its own, not representing any
    of the files that were opened. But, eventually we will map the URLs into
    the files and close the loop. For now, we will just leave the URLs
    denormalized, as actual URLs as a signal that they need help

    There seems to be a good chance that this will take some time and iteration
    before we get it complete. 


    Summary: In this function, I handle all files/urls, both top level and 
    xcref references, to fill out the data that Tyrin has asked for in the 
    spec, and I have also summarized in my summary of the data requests in the 
    spec. This function should have a return statement for each case of:
    + a top-level doc
    + a local file in the filesystem
    + a Salesfoce URL that resolves to a local file in the filesystem
    + a Salesforce URL that does not resolve to a local file in the filesystem
    + an external URL 
    '''

    path_sans_start_dir = remove_start_dir_for_display (root_dir, 
      actionable_path_or_url)

    # I also isolate the root file name (including removal of the file 
    # extension).
    local_file_name_only_pattern =  re.compile(
      f'^(?:{os.sep}?[^{os.sep}]+{os.sep})+([^{os.sep}]+)$')

    local_file_name_only = re.sub(local_file_name_only_pattern, r'\1', 
      actionable_path_or_url)


    # Here is where we get the node id of a local path-based document
    # from the function that handles such documents. If it does not 
    # properly handle it, in other words, if it is a url, and not a 
    # file path, it will return a None value.
    node_id = local_path_to_taxonomy(root_dir, path_sans_start_dir, 
      nn_elem_delim, nn_area_delim)

    if node_id:
        '''
        This should handle both a top-level doc, and any ref that cites a local
        doc.
        '''
        
        actionable_local_path = actionable_path_or_url
        content_domain = node_id.split(nn_elem_delim)[1]
        portal = node_id.split(nn_elem_delim)[0]
        if content_domain in group_lookup_table:
            label_part_1of2 = group_lookup_table[content_domain]['label']
            cloud = group_lookup_table[content_domain]['cloud']
            color = group_lookup_table[content_domain]['color']

        else:
            try:
                label_part_1of2 = titleize(content_domain)                
            except: 
                import pdb; pdb.set_trace()
                print('Something wrong with titleization.')
            #-# group = {'label': label, 'cloud': "Salesforce"}
            # label_part_2of2 needs to wait for opening the xml doc in 
            # analysis
            cloud = 'Salesforce'
            color = group_default_color
            #group = 'PLACEHOLDER'
        title = "Placeholder Title"
        label = f'{label_part_1of2} - {title}'

        return node_id, portal, content_domain, label_part_1of2, title, label, \
          color, cloud
    else:
        '''
        This branch handles all URLs, first trying them to see if they are 
        Salesforce URLs, then attempting to convert them to a local file.

        If they can be converted to a local file, then check if they are 
        filled in already as a Source, and take that data for the target or 
        fill them in as a Source and also use that data for the target.

        If they cannot be converted a local file, still give them "Salesforce"
        as their cloud.

        If they are not Salesforce URLs, handle their cloud and other data
        as dictated by the URL domain and other format.

        Each case identified above should build its own values and have its own
        return statement.  Each return should include: Node Id,  Group/Content 
        Domain, Label (1st part), Label (2nd Part)/Title, Label, Color, and 
        Cloud. These correspond to: node_id, content_domain, label_part_1of2,
        title, label, color, and cloud.

        The Weight and the Ref should be determined by the calling function, 
        which is `analyze_files_for_links()`. This function is also called by
        `ensure_files_of_interest_entry()` but that should execute only the
        branch above, the "if" to this "else:".
        '''

        # If the local_path_to_taxonomy() received a URL, it returns the un- 
        # changed name. This will (so far, with XML files) be an XRef URL. The
        # XRef URL's can either point back into the repository filesystem, or 
        # to an external link. An external link may still be within Salesforce,
        # so not truly external. But for our purposes of resolving it to a 
        # document we can access, it is external. 
        # Next in this function, we either resolve them to a book, or 
        # put them into a normal form similar to the 4 level taxonomy format 
        # that we used for filesystem paths. It will be necessarily different 
        # in that a URL will not reliably fit the 4 "word" format. It may have
        # only a domain, for example. Tyrin has posited a format that I think 
        # will work.
        target_url = actionable_path_or_url  
        converted_to_local_file_path = False
         
        # I had been using a regex to analyze the URL into components such as
        # the domain, path, path components, filename, extension, terminal
        # slash, fragments and args if any. I replaced that with the urlparse 
        # function is much surer, and more reliable.
        http_analysis = urlparse(target_url)

        # The urlparse function doesn't pull out a file name, so we need 
        # to do that here. 
        doc_base_name = None
        file_name_match = re.search(r'(?<=/)([^/.]+)\.html?', 
          http_analysis.netloc)
        if file_name_match:
            doc_base_name = file_name_match.group(1)

        sf_domain_match = False # Here for scope.
        if http_analysis:
            # The block immediately below cycles through every `sf internal
            # domain` from the defaults.yaml file, to find any match. If there
            # is a match, it sets the `sf_domain_match` to True,  breaks out of
            # the loop, and then continues with the "if" statement below. If 
            # there is no match, the code bypasses the if statement below.            
            for sf_internal_domain in sf_internal_domains:
                if sf_internal_domain == http_analysis.netloc:
                    sf_domain_match = True
                    break
                    
        if sf_domain_match:
            '''
            A True value for sf_domain_match means that we see the domain as a 
            Salesforce domain, and go on to check for the file as a local file.
            '''
            putative_file_name = f'{doc_base_name}.xml'
            ff_sentinel = False

            # This "if" on the condition that the file name is "in" files_of-
            # _interest main data structure is necessary and sufficient to 
            # confirm whether the file can be resolved to a local file name. 
            if putative_file_name in files_of_interest:
                converted_to_local_file_path = True
                confirmed_file_name = putative_file_name

                # For the time being, we assume that there is only one path
                # associated with the file name. So, we take the zeroeth of
                # one. But, in a translated repository there will be more than
                # one. When that circumstance ambiguates the result, we can
                # probably use the language-locale metadata of the document
                # that holds the reference to disambiguate it to 
                # the particular language-locale in the path. For now, 
                # this is just a design note for the future.
                
                actionable_path = list(
                  files_of_interest[confirmed_file_name]
                  ['paths'].keys())[0]

                http_analysis_matches.append(actionable_path)

                node_id = files_of_interest[confirmed_file_name]\
                  ['paths'][actionable_path]['node id']

                portal = files_of_interest[confirmed_file_name]\
                  ['paths'][actionable_path]['portal']

                internal_title = files_of_interest[confirmed_file_name]\
                  ['paths'][actionable_path]['internal_title']

                title = internal_title

                content_domain = node_name.split(nn_elem_delim)[1]

                if content_domain in group_lookup_table:
                    label_part_1of2 = group_lookup_table[content_domain]\
                      ['label']
                    cloud = group_lookup_table[content_domain]['cloud']
                    color = group_lookup_table[content_domain]['color']
                    label = f'{label_part_1of2} - {internal_title}'
                else:
                    try:
                        titleized_label_1of2 = titleize(content_domain)
                    except: 
                        import pdb; pdb.set_trace()
                        print('Something wrong with titleization.')
                    label_part_1of2 = titleized_label_1of2
                    cloud = "Salesforce"
                    color = group_default_color
                    label = f'{label_part_1of2} - {internal_title}'

                return node_id, portal, content_domain, label_part_1of2, \
                  title, label, color, cloud

            # This branch executes if a URL is among the sf internal domains, 
            # but is not resolvable to a doc in our
            # local file structure. In other words, it's an external link.
            # "nn-elem-delim" is node-name element delimiter.
            if not converted_to_local_file_path:
                '''
                This is where we should handle Salesforce domains that cannot 
                be resolved to a local file path.
                '''
                url = actionable_path_or_url

                portal = None

                node_id = url_to_label(
                  f'{http_analysis.scheme}://{http_analysis.netloc}\
                  + {http_analysis.path}')

                # in the case of a URL that is not convertible to a local doc,
                # from the formula in the corresponding column of Tyrin’s 
                # spreadsheet, this is the first element of the (URL version 
                # of the) Node ID, before the colon.
                content_domain = node_id.split(nn_elem_delim)[0]
                # I don't think there will be any entries right now that fit,
                # but I think we ought to support putting them in, in the 
                # future. I think I will titleize from the else to before this.
                if content_domain in group_lookup_table:
                    label_part_1of2 = group_lookup_table[content_domain]\
                      ['label']
                    cloud = group_lookup_table[content_domain]['cloud']
                    color = group_lookup_table[content_domain]['color']
                    title = http_analysis.netloc
                    label = f'{label_part_1of2} - {title}'
                # This "else" will be the most trod branch.
                else:
                    label_part_1of2 = titleize(content_domain)

                    # In reverse order of preference (last in wins).
                    label = title
                    filename_or_path = False
                    if http_analysis.path and http_analysis.path != '/':
                        title = http_analysis.path
                        filename_or_path = True
                    if doc_base_name:
                        title = doc_base_name
                        filename_or_path = True

                    # This appends a dash and the title if, and only if the
                    # path or the filename were found to exist in the block 
                    # immediately above. Otherwise, it's just the domain 
                    # (in urlparse-speak, the domain is the "netloc").
                    if filename_or_path:    
                       label += f' - {title}'

                    cloud = "Salesforce"
                    color = group_default_color
                return node_id, portal, content_domain, label_part_1of2, title, \
                  label, color, cloud
        else:
            ''' 
            This is where we handle unquestionably external links.
            '''
            
            url = actionable_path_or_url

            portal = None

            node_id = url_to_label(
              f'{http_analysis.scheme}://{http_analysis.netloc}\
              + {http_analysis.path}')
            
            content_domain = node_id.split(nn_elem_delim)[0]

            if content_domain in group_lookup_table:
                label_part_1of2 = group_lookup_table[content_domain]['label']
                cloud = group_lookup_table[content_domain]['cloud']
                color = group_lookup_table[content_domain]['color']
                title = http_analysis.netloc
                label = f'{label_part_1of2} - {title}'
            else:
                try:
                    label_part_1of2 = titleize(content_domain)
                except: 
                    import pdb; pdb.set_trace()
                    print('Something\'s wrong with titleization.')

                # In reverse order of preference (last in wins).
                title = http_analysis.netloc
                label = title
                filename_or_path = False
                if http_analysis.path and http_analysis.path != '/':
                    title = http_analysis.path
                    filename_or_path = True
                if doc_base_name:
                    title = doc_base_name
                    filename_or_path = True

                # This appends a dash and the title if, and only if the path
                # or the filename were found to exist in the block immediately
                # above. Otherwise, it's just the domain (netloc).
                if filename_or_path:    
                   label += f' - {title}'

            color = group_default_color
            cloud = "External"
                #group = {'label': label, 'cloud': 'PLACEHOLDER'}
                #group = 'PLACEHOLDER'


            return node_id, portal, content_domain, label_part_1of2, title, label, \
              color, cloud

# Diagnostic containers. These should probably be moved to the top of the 
# script. 
xml_files_with_titles = []
xml_files_without_titles = []
xml_files_with_conrefs_as_titles = []
xml_files_referenced_but_nonexistent = []
url_analysis = []


def titleize(raw_string):
    '''
    This is a function to apply title case conventions to a string passed in.
    Before applying the string object's own `title()` method, this function
    substitutes a space for underscores (or for runs of underscores, or runs
    of spaces, or dashes, or plus signs). It also splits a camel-case string
    on the transition from lowercase to upper case. Then, it finally applies
    the string's own built-in `title()` method.
    '''
    delimrs_to_space = re.compile(r'[ +_-]+')
    min_maj_to_space = re.compile(r'([a-z0-9A-Z])([A-Z])')
    first_pass_string = re.sub(delimrs_to_space, r' ', raw_string)
    compare_same = False
    new_string = first_pass_string
    
    # Because Python's re.sub won't handle subsequent overlapping instances of 
    # the pattern, we need to re-execute the re.sub until the string is no
    # longer changed.
    while not compare_same:
        old_string = new_string
        new_string = re.sub(min_maj_to_space, r'\1 \2', new_string)
        if old_string == new_string:
            second_pass_string = new_string
            compare_same = True
    final_string = second_pass_string.title()
    return final_string

def get_xml_elements(whole_file, full_path):
    # It turns out that XML titles have a number of aspects that
    # potentially interfere with simple parsing with a regex. There can
    # be, and frequently are, linebreaks mid-title, sometime several. 
    # Also, titles elements may contain conrefs, instead of text, 
    # usually, but not always, wrapped in an intervening phrase <ph> 
    # element. Finally, there can be no title at all, which is the case
    # with glossary items.
    xml_root = ET.fromstring(whole_file)
    
    # First, look for either of two alternatives. First, just the title
    try:
        src_doc_title = ("").join(xml_root.find('.//title').itertext())
    # If the title is returned in an array, take the zeroeth element.
    except IndexError:
        src_doc_title = ("").join(xml_root.find('.//title')[0].itertext())

    # If an Attribute error occurs, it means that the title element was
    # not found by the most usual search, and we look instead for a 
    # glossterm element.
    except AttributeError:
        glossterm_found = None
        glossterm_found = xml_root.find('glossterm')
        if glossterm_found is not None:
            src_doc_title = "glossterm: " 
            src_doc_title = src_doc_title + ("").join(xml_root.find(
               'glossterm').itertext())
        else:
            #import pdb; pdb.set_trace()
            src_doc_title = "No Title Nor Glossterm Found"
    
    # If neither an Index Error, nor an Attribute Error occurs, try
    # looking for a title that contains a conref, either with an 
    # intervening phrase element, or a "bare" conref. I am not sure,
    # but I think a bare conref may result in a page that displays no
    # title. 
    if not src_doc_title:
        
        # Parsing by XML can give zero-length strings as a positive
        # response. Zero-length stings are falsy, and don't pass
        # in an "if" conditional phrase. So, 
        # 1. I explicitly set the conref_as_title to "None".
        # 2. I gate-keep on whether xml_root.find is explicitly None.
        # 3. Inside the gate, I set the conref_as_title to the 
        #    xml_root.find()'s .attrib (I don't remember exactly why 
        #    I do this, but I should note it here when I do).
        # 4. I also set the title and a diagnostic phrase (title brevis
        #    diagnostic longa).
        # 5. I test whether either conditional has set the `conref_as
        #    _title`, and if so, I append it to 
        # explicitly whether it is still None. 
        conref_as_title = None

        if xml_root.find('.//title[@conref]') is not None:
            conref_as_title = xml_root.find('.//title[@conref]').attrib
            title_dignstic = f'BARE CONREFfed title: {conref_as_title}'
            src_doc_title = 'Warning: Bare Conreffed Title'
            

        if xml_root.find(".//title//ph[@conref]") is not None:
            conref_as_title = xml_root.find(
              ".//title//ph[@conref]").attrib
            src_doc_title = 'Warning: Conreffed Title in <ph> Element'
            title_dignstic = f'conreffed title: {conref_as_title}'

        if conref_as_title is not None:
            xml_files_with_conrefs_as_titles.append(
              f'Conref as Title: {full_path}: {title_dignstic}')
            xml_files_with_titles.append(src_doc_title)

        else:
            xml_files_without_titles.append(full_path)
            src_doc_title = "Warning: No Title"

    # If a bona fide title was found, eliminate any linebreaks or runs
    # of spaces, or tabs in it, and trim both begin and end of string
    # of any spaces.
    else:        
        src_doc_title = slugified(src_doc_title)
        xml_files_with_titles.append(src_doc_title)

    return src_doc_title



def analyze_files_for_links(root_dir, files_of_interest, group_lookup,
  group_default_color, sf_internal_domains, nn_elem_delim, nn_area_delim,
  key_width, key_counts):
    '''
    This is the main cycle. It takes in the main data structure, and uses it to
    open each XML file in the repository. It finds out some things about the 
    file if it can, such as the internal title.

    Then it does an entire-file "slurp",
    and searches for each of the constructs (described above in "constructs of 
    interest").

    To separate each link into one of three classes, this function uses a 
    three-part regular expression The strength of this is that it seems to have
    worked well, covering evey instance of the 56k files without any gaps. 
    There is error checking code to print out warnings for any construct that 
    does not cleanly process. When files ending in .htm started showing up in 
    among the filesystem files, it was caught by the error checking code ands 
    it was simple to add a ".html?" alternative to that particular regex. The 
    three part regular expression is not really properly coupled to this 
    function. I will fix that later. 

    The
    '''
    temp_counter = 0
    xml_files_without_titles = []
    

    # we want to take a snapshot of the original keys (filenames) because we
    # will be adding to the dictionary, changing its length. Python doesn't
    # allow that while iterating the dict, so we iterate a snapshot instead.
    original_filenames = list(files_of_interest.keys())
    for file_name in original_filenames:

        for path_record in files_of_interest[file_name]['paths']:

            full_path =  os.path.relpath(  # not so sure that this is what we 
            # want now. May just be path_record is all that is needed. 
              os.path.join(root_dir,path_record), start=root_dir)

            rel_parent_dir = re.sub(
              r'^(.*?)/[^/]+$', r'\1', path_record)

            posix_rel_parent_dir_path = Path(rel_parent_dir)

            node_id, portal, content_domain, label_part_1of2, title, label, \
              title, cloud = \
              path_or_url_to_node(path_record, group_lookup,
                group_default_color, sf_internal_domains, nn_elem_delim, 
                nn_area_delim)

            f = open( path_record, 'r' )
            whole_file = f.read()
            established_path_record = files_of_interest[file_name]['paths']\
              [path_record]

            # I only want to update the record if it was not previously updated
            # (which would have been as a Target, found before this docuem
            if established_path_record['internal title'] is None:
                
                files_of_interest[file_name]['paths'][path_record]\
                  ["history count"] += 1
                files_of_interest[file_name]['paths'][path_record]\
                  ["history"].append(
                  'File was successfully opened and read for analysis as a '\
                  + 'top-level document.')
                
                src_doc_title = get_xml_elements(whole_file, path_record)

                # At this point, every file should have some kind of title or
                # title-like thing in the "src_doc_title" name. We can then 
                # put it reliably into the file/filepath record. 
                files_of_interest[file_name]['paths'][path_record]\
                  ['internal title'] = src_doc_title
                files_of_interest[file_name]['paths'][path_record]\
                  ["history count"] += 1
                files_of_interest[file_name]['paths'][path_record]\
                  ["history"].append(
                    'File\'s internal title was found to be: "' \
                    + f'{src_doc_title}".' )
                files_of_interest[file_name]['paths'][path_record]\
                  ['internal title'] = src_doc_title
                files_of_interest[file_name]['paths'][path_record]\
                  ['label'] += f' - {src_doc_title}'

            # I moved this to outside the "for construct ..." because
            # I need to marshal all externally pointing references so
            # as to normalize them to stand apart from their fragments
            # and extend their weight count across xref, conref and 
            # possibly others
            weight_counting_store = list()
            for construct in constructs_of_interest:
                construct_matches = re.findall(
                  constructs_of_interest[construct], whole_file
                )
                
                if construct_matches:
                    # When there are capturing parentheses, the results 
                    # from re.findall will be an array of tuples.
                    # Tuple elements beyond the 0-indexed will be the cap-
                    # tured fragments. We want to flatten those tuples, 
                    # into an array, so we can then filter for just the
                    # whole matched expression. 
                    if type(construct_matches[0]) == tuple:
                        construct_matches = list(
                          itertools.chain(*construct_matches)
                        )
                    # This does the actual filtering for the matched
                    # expression. In the context of the "filter" lambda below,
                    # the captured sub-segments don't matter. The only thing
                    # that matters is the fact of whether the expression in 
                    # constructs of interest matches the parameter.
                    construct_matches = list(
                      filter(
                        lambda x: re.match(
                          constructs_of_interest[construct], x
                          ),
                          construct_matches
                      )
                    )
                    #import pdb; pdb.set_trace()
                    #debug_match = re.search('custom_ui_comps_1',
                    #  path_record)
                    #if debug_match:
                    #    import pdb; pdb.set_trace()

                    # The next steps update files of interest for
                    # this file's entry. The key will be the file name, then,
                    # inside that, the file path relative from the starting
                    # directory.
                    # For now, I do this for opened files only inside the 
                    # condition of having found a conref or xref. I also update
                    # the breadth count for each match found. Since there is a 
                    # pass through this part once for each of two patterns, 
                    # the breadth has a max level of 2. The depth reflects 
                    # every instance of a link found. 
                    ensure_files_of_interest_entry(root_dir, path_record,
                      group_lookup, group_default_color, sf_internal_domains,
                      nn_elem_delim, nn_area_delim, files_of_interest, 
                      key_width, key_counts)
                    files_of_interest[file_name]['paths'][path_record]\
                      ['breadth'] += 1
                    files_of_interest[file_name]['paths'][path_record]\
                      ['depth'] += len(construct_matches)

                    # At this point, I've handled the basie the main file 
                    # record concerns, and move on the the target files. 
               
                    for construct in construct_matches:

                        # Normalize multiline and multispaces
                        construct = re.sub(r'\n?\s+', r' ', construct)

                        # This uses the three part regex that was set near
                        # the top of this script. 
                        analyze_match = re.search(link_categories_regex, 
                          construct)

                        # zero out all the components so none is left from
                        # a prior analysis.
                        label             = None
                        #target_file_path  = None
                        xcref_path_or_url = None
                        xcref             = None
                        articulated_xcref = None
                        target_label      = None
                        # The following are only 
                        # used for a URL, and
                        # even then, not all of
                        # them are always used.
                        # For example `filename`
                        # is often not present:
                        url_proto       = None
                        url_domain      = None
                        url_path        = None
                        url_filename    = None
                        fragment        = None
                        #url_params      = None
                        url_query       = None 
                        url_no_fragment_nor_query = None

                        normal_target_file_path = None


                        # Having applied the analysis 3-part regex, I look
                        # for which part of the match applied. Unfortunately,
                        # these are just the count of the matching group
                        # opening paren. It would be nice if it was something 
                        # more elegant, but this works. If that group is not
                        # null, then I use the other matching groups that 
                        # follow it to pull out the key parts.
                        # Look to the articulated_xcref value to see exactly
                        # what kind of link is being analyzed.
                        if analyze_match:
                            url_analysis = None
                            #if analyze_match.group(11):
                            #    import pdb; pdb.set_trace()
                            # An xref with a local filesystem reference).
                            if analyze_match.group(2):
                                target_file_path = analyze_match.group(4)
                                fragment = analyze_match.group(7)
                                xcref = "xref"
                                articulated_xcref = "an xref"

                            # An xref with a URL reference.
                            elif analyze_match.group(9):
                                url =  analyze_match.group(11)
                                
                                xcref              = "xref"
                                articulated_xcref  = "an xref with a URL"

                            # A confref, which always has a local file ref-
                            # erence
                            elif analyze_match.group(12):
                                target_file_path = analyze_match.group(15)
                                fragment = analyze_match.group(18)
                                xcref = "conref"
                                articulated_xcref = "a conref"
                                  
                            else:
                                import pdb; pdb.set_trace()

                            # That sets the starting conditions, but I need to
                            # try to resolve 
                            # The following is entered if the articulated xcref 
                            # is a conref or an xref with a local filesystem 
                            # file.
                            if articulated_xcref != "an xref with a URL":
                                posix_target_file_path = Path(target_file_path)
                                rel_rel_path = posix_rel_parent_dir_path.\
                                  resolve(posix_target_file_path)
                                if path_root == 'relative':
                                    normal_target_file_path = os.path.relpath(
                                      os.path.join(os.path.dirname(
                                        path_record), target_file_path))
                                    reference_file_path = \
                                      normal_target_file_path

                                    file_path_sans_start_dir = \
                                      remove_start_dir_for_display(root_dir,
                                        normal_target_file_path)

                                    node_id, portal, content_domain, \
                                      label_part_1of2, title, label, \
                                      color, cloud = path_or_url_to_node(
                                      normal_target_file_path, group_lookup,
                                      group_default_color, 
                                      sf_internal_domains, nn_elem_delim, 
                                      nn_area_delim)
                                    ref_file_name = normal_target_file_path.\
                                      split(os.sep)[-1]

                                    try:
                                        established_path_record = \
                                          files_of_interest[ref_file_name]\
                                            ['paths'][reference_file_path]
                                    except KeyError:
                                        continue

                                    if established_path_record\
                                      ['internal title'] is None:
                                        f = open(reference_file_path, 'r' )
                                        whole_file = f.read()
                                        files_of_interest[ref_file_name]\
                                          ['paths'][reference_file_path]\
                                          ["history count"] += 1
                                        files_of_interest[ref_file_name]\
                                          ['paths'][reference_file_path]\
                                           ["history"].append(
                                             'File was successfully opened '\
                                             + 'and read for analysis as a '\
                                             + 'target document.')
            
                                        src_doc_title = get_xml_elements(
                                          whole_file, reference_file_path)
                                        # At this point, every file should 
                                        # have some kind of title or
                                        # title-like thing in the 
                                        # "src_doc_title" name. We can then put
                                        # it reliably into the file/filepath
                                        # record. 
                                        files_of_interest[ref_file_name]\
                                          ['paths'][reference_file_path]\
                                          ['internal title'] = src_doc_title
                                        files_of_interest[ref_file_name]\
                                          ['paths'][reference_file_path]\
                                          ["history count"] += 1
                                        files_of_interest[ref_file_name]\
                                          ['paths'][reference_file_path]\
                                          ["history"].append(
                                            'File\'s internal title was found'\
                                            + ' to be: \'' \
                                            + f'{src_doc_title}\'.' )
                                        files_of_interest[ref_file_name]\
                                          ['paths'][reference_file_path]\
                                          ['internal title'] = src_doc_title
                                        files_of_interest[ref_file_name]\
                                          ['paths'][reference_file_path]\
                                          ['label'] += f' - {src_doc_title}'
                                
                                elif path_root == 'absolute':
                                    normal_target_file_path = os.path.abspath(
                                      os.path.join(os.path.dirname(
                                        path_record), target_file_path))
                                else:
                                    quit('Unknown setting for path root: '\
                                      + f'"{path_root}". Check your C.L. '\
                                      + 'params '\
                                      + 'for the setting of --path_root, '\
                                      + 'or the defaults.yaml setting for '\
                                      + 'the value of "path root". The only '\
                                      + 'acceptable values are "relative", '\
                                      + 'and "absolute".')
                            
                            # Else, it's at least starting its existence as a
                            # file with a URL.
                            else:

                                # When I first set up this function, I was 
                                # only returning the node_name. But I was
                                # running into problems with the fact that
                                # some references among the URL refs
                                # actually do resolve to a local file path,
                                # and when I resolve them, I was not 
                                # tracking the fact that it had come in 
                                # from a URL. 
                                node_id, portal, content_domain, label_part_1of2, \
                                  title, label, color, cloud = \
                                  path_or_url_to_node(url, group_lookup,
                                  group_default_color, sf_internal_domains,
                                  nn_elem_delim, nn_area_delim)

                                # substituting the simpler and more reliable
                                # urlparse here:
                                url_analysis = urlparse(url)
                                url_proto    = url_analysis.scheme
                                url_domain   = url_analysis.netloc
                                url_path     = url_analysis.path
                                url_query    = url_analysis.query
                                fragment     = url_analysis.fragment
                                target_file_path = url_domain
                                url_no_fragment_nor_query = \
                                   f'{url_proto}://{url_domain}{url_path}'

                                # I send this target to 
                                # `path_or_url_to_node()` which tries to re-
                                # solve it to a local filepath if possible,
                                # and also re

                                # When I first set up this function, I was 
                                # only returning the node_name. But I was
                                # running into problems with the fact that
                                # some references among the URL refs
                                # actually do resolve to a local file path,
                                # and when I resolve them, I was not 
                                # tracking the fact that it had come in 
                                # from a URL. 

                                node_id, portal, content_domain, \
                                  label_part_1of2, title, label, color, \
                                  cloud = \
                                  path_or_url_to_node(
                                    full_path, group_lookup, 
                                    group_default_color, 
                                    sf_internal_domains, nn_elem_delim, 
                                    nn_area_delim)

                                the_hex_hash = hashlib.sha256(
                                  url_domain.encode()).hexdigest()
                                the_key = the_hex_hash[-key_width:]
                                
                            # A conref (it's implied that it is with a 
                            # filesystem reference, especially since conrefs
                            # don't ever use URL reference).

                            debug_match = re.search(
                              'forecasts3_enabling_data_sources',
                              analyze_match.group(0))

                            if not normal_target_file_path:
                                normal_target_file_path = url

                            # I think this should prolly be removed.
                            #import pdb; pdb.set_trace()
                            node_id, portal, content_domain, label_part_1of2, \
                              title, label, color, cloud = \
                              path_or_url_to_node(normal_target_file_path, 
                                group_lookup, group_default_color,
                                sf_internal_domains, nn_elem_delim,
                                nn_area_delim)

                            if normal_target_file_path not in \
                              files_of_interest[file_name]['paths']\
                              [path_record]['target nodes']:
                                files_of_interest[file_name]['paths']\
                                  [path_record]['target nodes']\
                                  [normal_target_file_path] = \
                                  {
                                      'node id'        : None,
                                      #'portal'         : None,
                                      'vim searchable' : '^  .',
                                      'content domain' : None,
                                      'label'          : None,
                                      'cloud'          : None,
                                      'color'          : color,
                                      'weight'         : 0,
                                      'reftype'        : [],
                                      'url'            : None,
                                      'fragment count' : 0,
                                      'fragments'      : [],
                                      'url param count': 0,
                                      'url params'     : []
                                  }


                            files_of_interest[file_name]['paths'][path_record]\
                              ['target nodes'][normal_target_file_path]\
                              ['node id'] = node_id 

                            #files_of_interest[file_name]['paths'][path_record]\
                            #  ['target nodes'][normal_target_file_path]\
                            #  ['portal'] = portal 

                            files_of_interest[file_name]['paths'][path_record]\
                              ['target nodes'][normal_target_file_path]\
                              ['vim searchable'] += ".".join(
                              normal_target_file_path.split("/")) + "."

                            files_of_interest[file_name]['paths'][path_record]\
                              ['target nodes'][normal_target_file_path]\
                              ['content domain'] = content_domain 

                            files_of_interest[file_name]['paths'][path_record]\
                              ['target nodes'][normal_target_file_path]\
                              ['label'] = label

                            files_of_interest[file_name]['paths'][path_record]\
                              ['target nodes'][normal_target_file_path]\
                              ['cloud'] = cloud

                            files_of_interest[file_name]['paths'][path_record]\
                              ['target nodes'][normal_target_file_path]\
                              ['weight'] += 1

                            files_of_interest[file_name]['paths'][path_record]\
                              ['target nodes'][normal_target_file_path]\
                              ['reftype'].append(xcref)
                            
                            files_of_interest[file_name]['paths'][path_record]\
                              ['target nodes'][normal_target_file_path]\
                              ['url'] = url_no_fragment_nor_query
                            

                            if fragment:
                                files_of_interest[file_name]['paths']\
                                  [path_record]['target nodes']\
                                  [normal_target_file_path]\
                                  ['fragment count'] += 1
                               
                                files_of_interest[file_name]['paths']\
                                  [path_record]['target nodes']\
                                  [normal_target_file_path]\
                                  ['fragments'].append(fragment)
                            else:
                                files_of_interest[file_name]['paths']\
                                  [path_record]['target nodes']\
                                  [normal_target_file_path]\
                                  ['fragments'].append(None)

                            if url_query:
                                files_of_interest[file_name]['paths']\
                                  [path_record]['target nodes']\
                                  [normal_target_file_path]\
                                  ['url param count'] += 1

                                files_of_interest[file_name]['paths']\
                                  [path_record]['target nodes']\
                                  [normal_target_file_path]\
                                  ['url params'].append(url_query)
                            else:
                                files_of_interest[file_name]['paths']\
                                  [path_record]['target nodes']\
                                  [normal_target_file_path]\
                                  ['url params'].append(None)
                                
                            ensure_files_of_interest_entry(root_dir, 
                              path_record, group_lookup, group_default_color, 
                              sf_internal_domains, nn_elem_delim, 
                              nn_area_delim, files_of_interest,
                              key_width, key_counts)

                        else:
                            # The contents fo this "else:" should never be
                            # reached, as long as the big regular expres-
                            # sion above correctly matches. 
                            print(f'construct unmatched: {construct}')
              
                    if xcref is None:
                        continue

                    store_actual_constructs(xcref, file_name, path_record,
                      node_id, weight_counting_store, construct_matches)                       

                    if os.path.basename(
                      normal_target_file_path) in files_of_interest:
                        if normal_target_file_path in files_of_interest[
                          os.path.basename(normal_target_file_path)]['paths']:
                            files_of_interest[os.path.basename\
                              (normal_target_file_path)]['paths']\
                              [normal_target_file_path]\
                              ['history count'] += 1

                            files_of_interest[os.path.basename\
                              (normal_target_file_path)]['paths']\
                              [normal_target_file_path]\
                              ['history'].append(
                                f"Found as {articulated_xcref} out of "\
                                + f"{path_record}.")
                            files_of_interest[os.path.basename(
                              normal_target_file_path)]['filename count'] += 1

                        else:
                            if normal_target_file_path \
                              not in unresolved_targets:
                                unresolved_targets[normal_target_file_path] = \
                                  {'count': 0}

                            unresolved_targets[normal_target_file_path]\
                            ['count'] += 1

            f.close()


if __name__ == "__main__":

    # Set up the arguments
    script_name = os.path.basename(__file__)
    script_name_no_ext = re.sub(r'^(.*?)\.[^.]+$', r'\1', script_name)
    yaml_file_name = script_name_no_ext + '_defaults.yaml'
    yaml_local_path = f'./{yaml_file_name}'
    with open(yaml_local_path, 'r') as defaults_ymlfile:
        yaml_defaults = yaml.load(defaults_ymlfile, Loader=yaml.FullLoader)
    raw_group_lookup = yaml_defaults['group lookup']
    
    group_lookup_keys = ['label','cloud', 'color']
    group_lookup = dict(
      map(lambda kv: (
        kv[0], dict(zip(group_lookup_keys,re.split(r'\s\s+', kv[1])))), 
        raw_group_lookup.items()
      )
    )
    for record in group_lookup:
        group_lookup[record]['color'] = re.sub(r'^\\+(#[0-9a-fA-F]{6})$', 
          r'\1', group_lookup[record]['color'])
          
    group_default_color = yaml_defaults['group default color'] 
    group_default_color = re.sub(r'^\\+(#[0-9a-fA-F]{6})$', r'\1',
      group_default_color)

    sf_internal_domains = yaml_defaults['sf internal domains']

    
    parser = argparse.ArgumentParser(

      description= f'''

        Analyze a corpus of documentation to show links between documents OR 
        show diagnostic data of this script and/or distilled other 
        characteristics of the corpus. All defaults are settable in the
        "{yaml_file_name}" file that 
        accompanies this script. If you change default values in that file (and
        save the changes), then this help message will update to mention the 
        new actual default values.''',
        formatter_class=SmartFormatter
        )

    
    suppress_analysis = yaml_defaults['operational']['suppress the analysis']
    parser.add_argument('-s', '--suppress', action='store_true',
      help='Suppress the actual anlysis of the corpus, to check the settings '\
        + 'before a run. The default is currently "%s".' % suppress_analysis, 
      default=suppress_analysis
    )

    yaml_default = yaml_defaults['informational']['display readme']
    parser.add_argument('-r', '--readme', dest='display_readme', 
      action='store_true', 
      help='Display a readme that tells what this file is for and the '\
        + 'context, or larger project of which this script is '\
        + 'a part. The default is '\
        + 'currently %s.' % yaml_default, 
      default=yaml_default)
    
    yaml_default = yaml_defaults['operational']['key width']
    parser.add_argument('-k', '--key_width', dest='key_width',
      help='Set the width to the final WIDTH characters of a SHA-256 '\
        + 'hash of filepath. This should not normally need to be changed, '\
        + 'but if there is a key crash, you should increase the digits. '\
        + 'The default is currently %s.' % yaml_default,
      default=yaml_default)
    
    yaml_default = yaml_defaults['diagnostic']['verbose']
    parser.add_argument('-v', '--verbose', action='count',
      help='Specify the diagnostic verbosity, increasing with each mention. '\
        + 'The default is currently %s.' % yaml_default, 
      default=yaml_default
    )
    
    display_links_regexes = yaml_defaults['diagnostic']\
      ['display links regexes']
    parser.add_argument('-d', '--display_links_regexes', action='store_true',
      help='Display the regular expressions that are being used to search '\
        + 'for links in the documents. Currently these are only for XML '\
        + 'documents, but eventually we will also have them for Markdown '\
        + 'documents. '\
        + 'The default is currently %s.' % display_links_regexes, 
      default=display_links_regexes
    )
    
    root_dir  = yaml_defaults['operational']['root dir']
    parser.add_argument('--root_dir', '-root_dir', dest='root_dir',
      help='The full path to the directory on which to start the recursive '\
        + 'search. The default value is currently "%s".' % root_dir,
      default=root_dir
    )

    path_root  = yaml_defaults['operational']['path root']
    parser.add_argument('--path_root', dest='path_root',
      help='The style of path to use, `absolute` or `relative`. '\
        + 'A relative path may be best if you are working with someone '\
        + 'collaboratively, who has a different starting directory on their '\
        + 'work machine. An absolute path style may be best if you are '\
        + 'working on your own (not collaborating), perhaps from a directory '\
        + 'that is not parent to the one you are using for as the root of '\
        + 'your search. The default value is currently "%s".' % path_root,
      default=path_root
    )

    nn_elem_delim  = yaml_defaults['operational']\
      ['node id element delimiter']
    parser.add_argument('--nned' '--nn_elem_delim', dest='nn_elem_delim',
      help='The delimiter used between elements of the node id. '\
        + 'The default value is currently "%s".' % nn_elem_delim,
      default=nn_elem_delim
    )
 
    nn_area_delim  = yaml_defaults['operational']['node id area delimiter']
    parser.add_argument('--nnad' '--nn_area_delim', dest='nn_area_delim',
      help='The delimiter used between elements of the area part node id '\
        + 'if there is more than one. Usually, you will not want this to be '\
        + 'the same as the node id element delimiter. '\
        + 'The default value is currently "%s".' % nn_area_delim,
      default=nn_area_delim
    )

    output_solo_nodes = yaml_defaults['operational']['output non-edge nodes']
    parser.add_argument('--solo_nodes', action='store_true', 
      dest='output_solo_nodes',
      help='Output nodes that are not linked to any others by an edge. '\
        + 'Suppressing display of unlinked nodes keeps the graph cleaner.'\
        + 'The default value is currently %s.' % output_solo_nodes,
      default=output_solo_nodes
    )
    
   
    output_json = yaml_defaults['operational']['output json']
    parser.add_argument('-j', '--json', action='store_true', 
      dest='output_json',
      help='Format the output as comma separated values (CSV). This '\
        + 'requires the analysis to have happened, so if "suppress the '\
        + 'analysis" is set in the defaults.yaml file, or in the command-'\
        + 'line parameters, this will output only an empty dict ("{}"). The '\
        + 'output will be made in the format given as a python "f" string in '\
        + 'the defaults.yaml file\'s section called "operational", the value '\
        + 'corresponding to the name "csv format". The default value is '\
        + 'currently %s.' % output_json,
      default=output_json
    )
    
    output_csv = yaml_defaults['operational']['output csv']
    parser.add_argument('-c', '--csv', action='store_true', dest='output_csv',
      help='Output the results as comma separated values (CSV). This requires'\
        + ' the analysis to have happened, so if "suppress the analysis" is '\
        + 'set in the defaults.yaml file, or in the command-line parameters, '\
        + 'this will output nothing. See --format_csv for more on the actual '\
        + 'format. The default value is currently %s.' % output_csv,
      default=output_csv
    )

        
    csv_titles = yaml_defaults['operational']['csv titles']
    parser.add_argument('--titles_csv', dest='csv_titles',
      help='CSV titles'\
        + '.'\
        + ' The default value is currently %s.'\
        % csv_titles,
      default=csv_titles
    )

    
    csv_format = yaml_defaults['operational']['csv format']
    parser.add_argument('--format_csv', dest='csv_format',
      help='CSV output, when chosen,'\
        + 'will be made in the format given in the defaults.yaml file\'s '\
        + 'section called "operational", as the value corresponding to the '\
        + 'the analysis" is set "csv format". The format is given as a '\
        + 'python "f" string, evaluated in the script, and de-referencing '\
        + 'variables that are in scope that section of the script. One '\
        + 'shortcoming of this approach is that, to write a new format, one '\
        + 'needs developer/maintainer level knowledge of the script\'s '\
        + 'workings. To mitigate this, I will write alternative '\
        + 'values that can sit, commented out, in the local defaults file. '\
        + 'The user can uncomment just the format (s)he needs, and leave the '\
        + 'others commented out. The default value is currently %s.'\
        % csv_format,
      default=csv_format
    )
    
    output_pydot = yaml_defaults['operational']['output pydot']
    parser.add_argument('-p', '--pydot', action='store_true', 
      dest='output_pydot',
      help='Output the results as a pydot-generated graphical file. This is '\
        + 'not intended to supplant the more sophisticated networkx-Tableau '\
        + 'stack, but as a fast-turnaround proof-of-concept, and check on '\
        + 'how changes to handling of URL\'s and short directory paths '\
        + 'affects output. The default value is currently %s.' % output_csv,
      default=output_pydot
    )
    
    pydot_format = yaml_defaults['operational']['pydot format']
    parser.add_argument('--pdformat', dest='pydot_format',
      help='Output the results as the file type given. Possible alternatives'\
        + ' are currently ".svg" and ".png". The .svg format seems to work '\
        + 'best for the complexity and extent of the data this generates. '\
        + 'Output requires the analysis to have happened, so if "suppress '\
        + 'the analysis" is set in the defaults.yaml file, or in the '\
        + 'command-line parameters, this will output nothing. The default '\
        + 'value is default is currently "%s".' % pydot_format,
      default=pydot_format
    )
    
    output_networkx = yaml_defaults['operational']['output networkx']
    parser.add_argument('-n', '--networkx', action='store_true', 
      dest='output_networkx',
      help='Output the results as a networkx-generated graphical file. This '\
        + 'is only partially implemented at the moment.  '\
        + 'The default value is currently %s.' % output_csv,
      default=output_networkx
    )
    
    if len(sys.argv) == 1:
        print('''
        To learn more about this script, invoke it again with either the -h
        flag (for help), or the -r flag (for a readme). 

        For the readme, append up to 4 'v's for the most complete explanation:
            {script_name} -rvvvv

        ''')
        quit()

    args = parser.parse_args()
    
    display_readme        = args.display_readme
    display_links_regexes = args.display_links_regexes
    root_dir              = args.root_dir
    key_width             = args.key_width
    suppress_analysis     = args.suppress
    path_root             = args.path_root
    nn_elem_delim         = args.nn_elem_delim
    nn_area_delim         = args.nn_area_delim
    output_solo_nodes     = args.output_solo_nodes
    output_json           = args.output_json
    output_csv            = args.output_csv
    output_pydot          = args.output_pydot
    pydot_format          = args.pydot_format
    csv_titles            = args.csv_titles
    csv_format            = args.csv_format
    verbose               = args.verbose

    if display_links_regexes:
        print(json.dumps(printable_constructs, indent=2))

    if display_readme:

        readme_content = f'''
        This script, "{script_name}", 
        and associated settings file "{yaml_file_name}",
        are part of a toolset to display document relationships graphically.

        This script is intended to be the data gathering part of that toolset.

        Internally in this script, all data gathered are organized into a 
        Python data structure, which is available on-demand as a JSON data 
        structure. 

        This script supplies the data to the graphical display library in comma
        separated value (CSV) format. The CSV file generally follows the format
        of a source file, a target file, and a "weight", which is the count of
        instance where the target file was found from the same source file. The
        specific CSV format is settable in the accompanying .yaml settings 
        file.'''

        if verbose == 0:
            readme_content += f'''

        More information, including a "Synopisis of Simple Use" is available at
        higher verbosity settings:

        {os.path.basename(__file__)} -rv

          or

        {os.path.basename(__file__)} -rvv

          etc.

        '''

        if verbose >= 1:

            readme_content += f'''

        To use this script, first ensure that there is a copy of your XML
        repository on your local machine, and that the absolute path location
        of the top of that repository is given, either as the value of "root 
        dir" in the defaults file: {yaml_file_name}, or as an override as an
        argument to the --root_dir parameter (described in help).

        Synopsis of Simple Use:        

          Generate the Readme: 
          (to generate a readme that tells more about the script)

            {script_name} 

              or

            {script_name} -r

          (to generate the most information in the readme)

            {script_name} -rvvvv

          Basic Use: 
          (to generate a CSV file for consumption by the graphing software)

            {script_name} -c
          
          Retrieve Help:
          (to see all the parameters, and their default values)

            {script_name} -h 

          Diagnostic Use:
          (to see internally-used values)
            
            {script_name} -j

          All output for all flags is written to stdout (the screen). To put it
          into a file, just use the greater than sign to redirect the output
          to a filename of your choice. 

        Extended (and Experimental) Use:
        
          Output an a basic pydot graph as an .svg file:

            {script_name} -p



        '''

        if verbose == 1:
            readme_content += f'''

        More information, including a high level "Details of Operation of this 
        Script" is available at higher verbosity settings:

        {os.path.basename(__file__)} -rvv

          or

        {os.path.basename(__file__)} -rvvv

          etc.

        '''

        if verbose >= 2:

            readme_content += '''

        Details of Operation of this Script:

        Gathering the data involves recursing directories below the "root dir",
        to find each file of which the name ends in ".xml". The script builds
        an internal table as a Python dictionary, for which the index entry is 
        each file name ending in ".xml". Among the values below the particular
        file name is a "paths" key, for which the value is a dictionary. The
        index entry or key of each value in "paths" dict is the path for each
        instance of the filename. By default, the path listed is relative, and
        from the point of view of the root dir. A command line setting, 
        "path_root" allows changing all paths to absolute.

        Since it is a tenet of dev-doc writing at Salesforce that the filename 
        choice result in a unique-in-the-repository filename, you may reason-
        ably ask why there would be more than one path for a filename. The 
        answer is that downstream of the filename choice, localization (trans-
        lation) may occur. In a localized folder, there is another instance of
        a filename. It is also possible that a filename be used twice by
        accident. The arrangement of entering with the filename, then the path,
        keeps together potentially several instances of path under the same 
        filename.

        In a second pass through the files, now taking their paths in turn from
        the internal table (as opposed to recursing from the root dir), the 
        script opens each file, and parses it. Currently parsing is done in two
        ways. 

        First, as an XML tree, to find title elements and title-like elements
        (these are <glossterm>s which are the closest thing to a title in
        glossary entries). Next the same file is read line by line using a 
        regular expression (regex) to search for content references (ConRefs), 
        and external references (ExRefs). The paths for each of these are
        either listed as a relative file structure path within the file 
        structure, or (for XRefs only) as an HTTP URL. The URL points either 
        externally, or to a file within the file structure.

        For the file paths, this script takes just file name, and the path. It
        then resolves the path to convert it from a relative path the point of
        view of the containing file, to a relative path from the root dir. This
        allows the script to then re-enter the internal data structure with the
        filename and a normalized file path, to find the details of the 
        particular file.
        
        For the URLs, this script converts the ".html" ended page name to an 
        .xml-terminated file name, then attempts to find the file name in the
        internal data structure. If no filename can be found, then the URL is
        assumed to be external. "External" in this case, only means that it is
        not pointing to an XML file in the file structure below the root dir.

        For external URLs, this script tries to reduce the number of 
        relationships by agglomerating distinct URL's under their domain.
        
        Finally output can be any of several types. For production use, this 
        will be CSV output. For diagnostic, a JSON dump of the internal data
        structure is provided, 
        '''
        
        if verbose == 2:
            readme_content += f'''

        More information, "Known or Foreseen Opportunities for Improvement"
        is available at a higher verbosity setting:

        {os.path.basename(__file__)} -rvvv

          or

        {os.path.basename(__file__)} -rvvvv

          etc.

        '''


        if verbose >= 3:
            readme_content += '''

        Known or Foreseen Opportunities for Improvement:

        This script could be made to agglomerate some of the files under areas,
        areas under books, and books under portals. It does not currently do 
        this, but doing so could reduce the complexity of the generated graph,
        so there are not as many edges. It's my understanding that Tyrin has
        been manually updating this information, so this should be on a short
        list for changes to this script.

        This script does not currently provide any color information or 
        grouping that can be used to provide a color dimension to the graphed
        data. It's my understanding that Tyrin has been providing this kind of
        color data manually, based on the book. Each book has a different color
        and all targets of a book share that color. Since this is causing 
        unscalable manual labor, color data should be provided by this script.
        However, coloring endpoints the same color as their source may need to
        be open to change in the future.

        This script currently requires re-entering the main in-memory table to
        get the node id of the targets. I don't think this is the best way
        to do it, because it undermines the ability to set the CSV format from
        the defaults.yaml file, or from the command line. It is sort of denorm-
        lizing to have the node id appear in several places (both the main 
        record of the node, but also in its mention as a target), but it seems
        to be a necessary aspect. 

        This script puts a "history" into each file record, showing the incep-
        tion of the file, and every filname where the file was found as an
        XRef or ConRef. This history is a good thing: I want to keep it. But
        it is too wordy to be immediately actionable. I want to summarize
        what it expresses in a succinct mention and count of referring pages.
                
        This script could be extended to Markdown (.md) files, but does not 
        currently handle them.

        This script could be made to take more than one root dir, possibly even
        mixing Markdown and .XML file formats below the various root dirs. This
        might possibly form a picture of relationships that were, until that
        change, only listed as external URLs.

        When resolving URL's that point to documents in the file structure, 
        this script just takes the first (0th) path found. While this works for
        an unlocalized repository, it may not work for a localized repository,
        where there are more than one instance of a file name, under different
        directories. This should not be too difficult to fix, but it may
        require gathering information on the language of the referring page.

        This script does not currently allow fine-tuning of the agglomerated
        URL, but puts all instances under the domain.'''

        
        if verbose == 3:
            readme_content += f'''

        More information: a "Change History"
        is available at a higher verbosity setting:

        {os.path.basename(__file__)} -rvvvv

        '''

        if verbose >= 4:
            readme_content += '''

        Change History:

        2022 Feb 17

        This script was updated to more reliably normalize relative paths, to
        allow the optional use of absolute paths, and to provide some grouping
        of URLs under their domain. Grouping URLs needs some more work.

        2022 Feb 21

        Added to the help message, and created a readme that comes when the 
        script is invoked with a -r or --readme. Also added a clue in case the
        script is invoked without any parameters at all. 

        '''
        print(readme_content)
        quit()

    files_of_interest = list_relpaths_by_filename(root_dir, group_lookup, 
      group_default_color, sf_internal_domains, files_of_interest,
      nn_elem_delim, nn_area_delim, 'xml',
      key_width)

    if not suppress_analysis:
        analyze_files_for_links(root_dir, files_of_interest, group_lookup, 
          group_default_color, sf_internal_domains, nn_elem_delim, 
          nn_area_delim, key_width, key_counts)

    if output_json: 
        print(json.dumps(files_of_interest, indent=2))
        print(json.dumps(unresolved_targets, indent=2))
        print(f"files_of_interest: {len(files_of_interest)}")
        print(f"unresolved_targets: {len(unresolved_targets)}")
        print("unresolved_targets that are URLs: " + str(
          len(
            [key for key in unresolved_targets.keys() if key[0:4] == 'http'])))
        print("unresolved_targets that are not URLs: " + str(
          len(
            [key for key in unresolved_targets.keys() if key[0:4] != 'http'])))
    
    if output_csv:
        print(csv_titles)
        for file_name in files_of_interest:
            for full_path in files_of_interest[file_name]['paths']:
                # I'll shorten the first four nodes of the data structure to
                # just "record".
                source = files_of_interest[file_name]['paths'][full_path]
                for target_node_name in source["target nodes"]:
                    target = source["target nodes"][target_node_name]
                    # import pdb; pdb.set_trace()
                    print(eval(csv_format))
            
    if output_pydot:
        import pydot
        print("start of pydot output")
        #graph = pydot.Dot(graph_type='graph')
        graph = pydot.Dot(graph_type='digraph', rankdir='LR', ratio='0.6666', 
          nodesep ='0.2', splines='spline', fontsize='80', fontname='Courier')
        graph.set_node_defaults(shape='Mrecord',penwidth=1)
        for file_name in files_of_interest:
            for filepath in files_of_interest[file_name]['paths']:
                node_name = files_of_interest[file_name]['paths'][filepath]\
                  ['node id']
                if not files_of_interest[file_name]['paths'][filepath]\
                  ['target nodes']:
                    #print(f'{node_name}')
                    graph.add_node(pydot.Node(name=node_name))
                else:
#                    pass
                    #print("multi")
                    for target in files_of_interest[file_name]['paths']\
                      [filepath]['target nodes']:
                        target_base_fn = os.path.basename(target)
                        if target_base_fn in files_of_interest:
                            if target in files_of_interest[target_base_fn]\
                              ['paths']:
                                target_node_name = files_of_interest\
                                [target_base_fn]['paths'][target]\
                                ['node id']

                            else:
                                pass
                        else:
                            pass
                         
                    #   print(f'{node_name} ---> {target}')
                        graph.add_edge(pydot.Edge(node_name, target_node_name))
        print("finished with in-memory graph creation")
        #graph.write_png('info_topo_mod_02.png')
        #graph.write_svg('./info_topo_mod_02.svg')
        graph.write_raw('info_topo_mod_02.dot')
        print("finished with output to a .svg file")

    if output_networkx:
        import networkx as nx
        import matplotlib as plt
        print("start of networkx output")
        DG = nx.DiGraph()
        for node_name in files_of_interest:
            if not files_of_interest[node_name]['target nodes'].values:
                DG.addNode(node_name)
            else:
                for target in files_of_interest[node_name]['target nodes']:
                    DG.add_edge(node_name, target)
        print("finished with in-memory networkx graph creation")
        nx.draw(DG, with_labels=True, font_weight='bold')
        plt.savefig("info_topo_mod_02_mpl.png")
        print("finished with output. ")

#if  xml_files_without_titles:
#    print("There are XML files without titles:")
#for file in xml_files_without_titles:
#    print(f'\t{file}')
#if  xml_files_with_conrefs_as_titles:
#    print("There are XML files without titles:")
#for file in xml_files_with_conrefs_as_titles:
#    print(f'\t{file}')
#if url_analysis:
#    for url_analysum in url_analysis:
#        print(f'\t{url_analysum}')
#        
