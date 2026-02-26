##==============================================================================
## BHPTNRSurrogate module
## Description : checks hash of h5 files
## Author : Tousif Islam, Aug 2022 [tislam@umassd.edu / tousifislam24@gmail.com]
##==============================================================================

import os
import hashlib
import logging
import urllib.request

logger = logging.getLogger(__name__)

#----------------------------------------------------------------------------------------------------
def md5(fname, h5_data_dir, zenodo_ID):
    """ Compute hash from file. code taken from
    https://stackoverflow.com/questions/3431825/generating-an-md5-checksum-of-a-file"""

    file_path = os.path.join(h5_data_dir, fname)

    # download file if not already there
    if not os.path.isfile(file_path):
        url = 'https://zenodo.org/record/%s/files/%s' % (zenodo_ID, fname)
        logger.info('%s file is not found in the directory - PATH-TO/BHPTNRSurrogate/data/' % fname)
        logger.info('... downloading h5 file from zenodo')
        logger.info('... this might take some time')
        try:
            urllib.request.urlretrieve(url, file_path)
        except Exception as e:
            raise RuntimeError(
                "Failed to download %s from %s: %s" % (fname, url, e)
            )
        logger.info('... downloaded')

    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

#----------------------------------------------------------------------------------------------------
def check_current_hash(file_hash, zenodo_current_hash, url, fname):
    # chech if the h5file is the most recent one or if it is corrupted
    if file_hash != zenodo_current_hash:
        raise AttributeError("%s out of date.\n \
                             Please download new version from %s"\
                             %(fname,url))
    else:
        pass
