.. _subdomain:

=============================
Running with Subdomain ADCIRC
=============================

Getting the Subdomain ADCIRC Code
---------------------------------

This code extends the :program:`PolyADCIRC` framework to work with :program:`Subdomain
ADCIRC v.50`. :program:`Subdomain ADCIRC v.50` was developed by Alper Altuntas
and Jason Simon under the direction of John Baugh; Department of Civil,
Construction, and Enviromental Engineering North Carolina State University
(NCSU), Raleigh, NC 27695. Since I am using :program:`ADICRC v 50.99.09` I
merged their original source with :program:`ADCIRC v 50.99.09` and updated it
so that the command line ``-I`` and ``-O`` options are availiable. I have also
added an ``__init__.py`` file so that their :program:`Python` script directory
is recongized as a package.

As the file structure and set up for :program:`Subdomain ADCIRC` closely
parallels that of :program:`ADCIRC` the repo containing the subdomain code will
need to be cloned into your ``$WORK`` directory using the
``--separate-git-dir=$HOME/v50_subdomain`` options::

    $ git clone --separate-git-dir=$HOME/v50_subdomain ices-workstation:/org/groups/chg/lgraham/v50_subdomain

If you would like a copy of :program:`Subdomain ADCIRC` it is availiable at
`Subdomain Modeling in ADCIRC <http://www4.ncsu.edu/~jwb/subdomain/>`_. They
have a great graphical interface for the `ADCIRC Subdomain Modeling
Tool <https://github.com/atdyer/SMT>`_.

Modifying Subdomain ADCIRC
---------------------------

You will need to modify :program:`Subdomain ADCIRC` by making the ``py``
directory in the :program:`Subdomain ADCIRC` directory into an importable
python package. This requires adding a ``__init__.py`` file and then either
installing it as a Python package or adding it to your Python path.

Setting up the Subdomain ``grid_dir``
-------------------------------------
The subdomain specific files and symbolic linkes generated by the following script
``[subdomain]/fort.{015,019,13,14,...}`` will need to be copied/moved to the
``grid_dir`` directory specified in your ``run_lonestar_test.py`` script. You
can also simply specifify a ``grid_dir`` for the subdomain and one for the
fulldomain and then move/copy the ``fort.13`` file to the directory containing
the ``sae_dir`` for the subdomain.

setup_subdomain
~~~~~~~~~~~~~~~
This script can be found in ``Polysim/examples``.
Allow running from the command line::

    #! /usr/bin/env/python

Import necessary modules::

    import polyadcirc.run_framework.subdomain as subdom
    import polyadcirc.run_framework.fulldomain as fulldom
    import glob

Specify the path to directory containing the compiled :program:`PADCIRC`
executables::

    adcirc_dir = '/work/01837/lcgraham/v50_subdomain/work'

Specify the path to directory containing the input files for the
:class:`~polyadcirc.run_framework.fulldomain.fulldomain`. This folder should also
contain a copy of the compiled executable :program:`ADCPREP`::

    fulldomain = fulldom.fulldomain(adcirc_dir+'/fulldomain')

Specify the path to the directory that will contain files specific to the
:class:`~polyadcirc.run_framework.subdomain.subdomain`. This folder should also
contian a copy of the compiled executables :program:`ADCPREP`::

    subdomain = subdom.subdomain(adcirc_dir+'/subdomain')

Update object references between the
:class:`~polyadcirc.run_framework.subdomain.subdomain` and the
:class:`~polyadcirc.run_framework.fulldomain.fulldomain`. This is somewhat clunky
with a possiblity of circular references, so I might alter it in the future::

    subdomain.set_fulldomain(fulldomain)

Specify the number of processors for each :program:`PADCIRC` run. This can be
done separately for each run. Make sure this number is less than or equal to
the total number of processors requested in your job submission script::

    num_procs = 2

Check to see if shape file exists, if not make it::
    
    if len(glob.glob(subdomain.path+'/shape.*14')) <= 0:
        subdomain.ellipse([40824.6, 98559.5], [98559.5, 40824,6], 60000)

The following steps correspond to Table 1 in Subdomain ADICRC v.50 User Guide.
    
Step 1a. Generate Sudomain::

    subdomain.setup()

Step 1b. Generate Full Domain Control File::
    
    subdomain.genfull()

Step 2. Run ADCIRC on the full domain::

    fulldomain.update()
    if subdomain.check_fulldomain():
        disp =  "Output files ``fort.06*`` exist, but running ADCIRC on fulldomain"
        print disp+"anyway."
    else:
        print "Output files ``fort.06*`` do not exist, running ADCIRC on fulldomain."
    fulldomain.run(num_procs, adcirc_dir)

Step 3. Extract Subdomain Boundary Conditions::

    subdomain.update()
    subdomain.genbcs(h0 = 0)

Step 4 Run ADCIRC on the subdomain::

    if subdomain.check():
        subdomain.run(num_procs, adcirc_dir)
    else:
        print "Input file ``fort.019`` does not exit."

Compare subdomain and fulldomain results::

    subdomain.update_sub2full_map()
    ts_data, nts_data, time_obs = subdomain.compare_to_fulldomain(['fort.63',
                                    'fort.64'],['maxele.63','maxvel.63'])


Setting up your ``landuse_##`` folders
--------------------------------------
Use the subdomain specific ``fort.14`` and ``fort.13`` files to generate a set
of landuse basis folders, see :doc:`landuse_stuff`. These ``landuse_##``
folders will need to be moved to the ``basis_dir`` directory specificed in your
``run_lonestar_test.py`` script.

Running PolyADCIRC with Subdomains
----------------------------------
Finally, update the directory paths in a copy of ``run-lonestar-test``. This
file may be run with no other changes as all the necessary files for
:program:`Subdomain ADCIRC` are now located in the ``grid_dir``.

