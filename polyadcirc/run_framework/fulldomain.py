# -*- coding: utf-8 -*-

# Copyright (C) 2013 Lindley Graham

"""
This module contains a set of methods and a class for interacting with NCSU
Subdomain Modeling Python code and associated files. The focus of this module
is the :class:`fulldomain`.
"""
import subprocess, glob, sys, os
import numpy as np
import scipy.io as sio
import polyadcirc.run_framework.domain as dom
import polyadcirc.pyADCIRC.post_management as post
import polyadcirc.run_framework.random_manningsn as rmn
import polyadcirc.pyADCIRC.output as output

class fulldomain(dom.domain):
    """
    Objects of this class contain all the data needed by :mod:`py.genbcs`,
    :mod:`py.genfull`, and :mod:`py.gensub` for a particular full domain
    mesh/grid. References to :class:`polyadcirc.run_framework.subdomain` objects
    are also contained in an instantiation of this class.
    """
    def __init__(self, path, subdomains=None, node_num=0, element_num=0,
                 node=None, element=None):
        """
        Initialization
        """
        super(fulldomain, self).__init__(path, node_num, element_num, node,
                                         element)
        # figure out where the script dir for the ncsu subdomain code is
        for sys_path in sys.path:
            potential_file_list = glob.glob(os.path.join(sys_path, 'py'))
            if potential_file_list:
                self.script_dir = potential_file_list[0]
                break

        #: list of :class:`~polyadcirc.run_framework.subdomain`
        if subdomains is None:
            self.subdomains = list()
        else:
            self.subdomains = subdomains

    def add_subdomain(self, subdomain):
        """
        Adds subdomain to self.subdomains.

        :type subdomain: :class:`~polyadcirc.run_framework.subdomain`
        :param subdomain: subdomain within this domain

        """
        self.subdomains.append(subdomain)
        subdomain.fulldomain = self

    def add_subdomains(self, subdomains):
        """
        Adds subdomain to self.subdomains.

        :type subdomains: list of :class:`~polyadcirc.run_framework.subdomain`
        :param subdomains: subdomains within this domain

        """
        self.subdomains.extend(subdomains)
        for s in subdomains:
            s.fulldomain = self

    def update_subdomains(self):
        """
        Update relational references between fulldomain and it's subdomains by
        setting subdomain.fulldomain = self
        """
        for subdomain in self.subdomains:
            subdomain.fulldomain = self

    def genfull(self, noutgs=1, nspoolgs=1, subdomains=None):
        """
        Generate the full domain control file, ``fort.015``, and save it to
        ``self.path``.

        :param int noutgs: flag controlling whether or not ``fort.06*`` will be
            written out
        :param int nspoolgs: the number of timesteps at which information is
            written to the new output files ``fort.06*``
        :rtype: string
        :returns: command line for invoking genfull.py

        """
        if subdomains is None:
            subdomains = self.subdomains
        if len(subdomains) == 0:
            with open(os.path.join(self.path, 'genfull.in'), 'w') as fid:
                fid.write(str(noutgs)+'\n')
                fid.write(str(nspoolgs)+'\n')
            command = "python "+self.script_dir+" -a "+self.path+'/ '
            command += " < genfull.in"
            subprocess.call(command, shell=True, cwd=self.path)
        else:
            with open(os.path.join(self.path, 'genfull.in'), 'w') as fid:
                fid.write(str(noutgs)+'\n')
                fid.write(str(nspoolgs)+'\n')
                for subdomain in subdomains:
                    subdomain.nspoolgs = nspoolgs
                    fid.write(subdomain.path+'/\n')
            command = "python "+self.script_dir+"/genfull.py -s "+self.path+'/ '
            command += str(len(subdomains)) + " < genfull.in"
            subprocess.call(command, shell=True, cwd=self.path)
        return command

    def genbcss(self, forcing_freq=None, dt=None, nspoolgs=None, h0=None,
                L=False): 
        """
        Generate the ``fort.019`` files for the subdomains. This requires the
        presence of the output files from a fulldomain run, ``fort.06*``.

        :param list forcing_freq: number of timesteps at which infomration
            is written to a boudnary conditions file (``fort.019``)
        :param list dt: One timestep in seconds
        :param list nspoolgs: the number of timesteps at which information is
            written to the new output files ``fort.06*``
        :param list h0: minimum water depth for a node to be wet
        :param bool L: flag whether or not :program:`PADCIRC` was run with
            ``-L`` flag and if local files need to be post-processed into
            global files
        :rtype: list
        :return: command lines for invoking genbcs.py

        """
        commands = []
        if L:
            # create post-processing input file
            post.write_sub(self.path)
            # run ADCPOST
            subprocess.call('./adcpost < in.postsub > post_o.txt', shell=True,
                            cwd=self.path)

        if self.check_fulldomain():
            if forcing_freq is None:
                forcing_freq = [1 for i in self.subdomains]
            if dt is None:
                dt = [self.time.dt for i in self.subdomains]
            if nspoolgs is None:
                nspoolgs = [1 for i in self.subdomains]
            if h0 is None:
                h0 = [None for s in self.subdomains]
            for f, d, ns, h, subdomain in zip(forcing_freq, dt, nspoolgs, h0,
                                              self.subdomains):
                commands.append(subdomain.genbcs(f, d, ns, h))
        else:
            print "Output files from the fulldomain run do not exist"
        return commands

    def check_fulldomain(self):
        """
        Check to see if the ``fort.06*`` and ``PE*/fort.065`` files exist

        :rtype: bool
        :returns: False if the ``fort.06*`` files don't exist

        """
        fort06 = glob.glob(os.path.join(self.path, 'fort.06*'))
        fort065 = glob.glob(os.path.join(self.path, 'PE*', 'fort.065'))
        return (len(fort06) > 0 and len(fort065) > 0)

    def check_subdomains(self):
        """
        Check all the subdomains to make sure the ``fort.019`` file exists

        :rtype: bool
        :returns: False if ``fort.019`` is missing from at least one of the
            subdomains

        """
        for sub in self.subdomains:
            if not sub.check():
                return False
            else:
                return True

    def setup_all(self):
        """
        Set up all of the subdomains
        """
        for sub in self.subdomains:
            sub.setup()


    def read_and_save_output(self, ts_names, nts_names, save_file=None,
                             timesteps=None, save=False):
        """
        Reads in output files from this fulldomain and saves to a file. 

        NOTE THIS DOES NOT CURRENTLY WORK FOR STATION DATA! ONLY USE FOR GLOBAL
        DATA i.e files that are fort.*3 or fort.*4

        NOTE THIS DOES NOT CURRENTLY WORK FOR ANY NTS DATA EXCEPT FOR MAXELE

        :param list ts_names: names of ADCIRC timeseries
            output files to be recorded from each run
        :param list nts_names: names of ADCIRC non timeseries
            output files to be recorded from each run
        :param string save_file: name of file to save comparision matricies to
        :param int timesteps: number of timesteps to read from file
        :rtype: dict
        :returns: full_dict

        """
        
        if save_file is None:
            save_file = os.path.join(self.path, 'full.mat')
        fulldict = dict()

        # Get nts_error
        for fid in nts_names:
            key = fid.replace('.', '')
            fulldict[key] = output.get_nts_sr(self.path, self, fid)

        # Get ts_data
        for fid in ts_names:
            key = fid.replace('.', '')
            fulldict[key] = output.get_ts_sr(self.path,
                                             fid, timesteps=timesteps,
                                             ihot=self.ihot)[0]

        # fix dry nodes
        if fulldict.has_key('fort63'):
            fulldict['fort63'] = np.expand_dims(fulldict['fort63'], axis=2)
            fulldict = rmn.fix_dry_nodes(fulldict, self)
            fulldict['fort63'] = np.squeeze(fulldict['fort63'])
        # fix dry data
        if fulldict.has_key('fort61'):
            fulldict['fort61'] = np.expand_dims(fulldict['fort61'], axis=1)
            fulldict = rmn.fix_dry_data(fulldict, self)
            fulldict['fort61'] = np.squeeze(fulldict['fort61'])
        # fix dry nodes nts
        if fulldict.has_key('maxele63'):
            fulldict['maxele63'] = np.expand_dims(fulldict['maxele63'], axis=1)
            fulldict = rmn.fix_dry_nodes_nts(fulldict, self)
            fulldict['maxele63'] = np.squeeze(fulldict['maxele63'])

        if save:
            sio.savemat(save_file, fulldict, do_compression=True)

        return fulldict
