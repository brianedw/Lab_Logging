class LeaseRecord:
    """
    An object for storing a single record of usage in a FlexNet license manager
    software.

    The hash is defined on the immutable attributes of the record.  This is
    useful for finding overlap between two different license usage snapshots.
    """

    def __init__(self, user, module, server, terminal, version,
                 licServer, start, lastSeen=None, checkedOut=True):
        """
        Standard initialization.  Saves arguements as instance attributes.

        Arguments:
            user (str) -- username on the user on their terminal computer.
            module (str) -- the module for which the license is checked out.
            server (str) -- the computer name where the module is being used.
            terminal (str) -- the computer name where the user is working.
            version (str) -- Licensed program version number
            licServer (str) -- Computer serving the license
            start (datetime) -- When the module was originally checked out.

        Keyword Arguments:
            lastSeen (datetime) -- The last time the module had been witnessed as still in use (default: {None})
            checkedOut (bool) -- If the module is still checked out. (default: {True})
        """

        self.user = user
        self.module = module
        self.server = server
        self.terminal = terminal
        self.version = version
        self.licServer = licServer
        self.start = start
        if lastSeen is None:
            self.lastSeen = start
        else:
            self.lastSeen = lastSeen
        self.checkedOut = checkedOut
        self.licNumber = None

    def getSig(self):
        """
        Creates a signature based on all immuatble aspects of the record.

        Returns:
            tuple(immutable stuff) -- The record signature.
        """

        # signature intentionally ignores 'lastSeen' and 'checkedOut' as these
        # are considered mutable.
        return (self.user, self.module, self.server, self.terminal,
                self.version, self.licServer, self.start)

    def equiv(self, other):
        '''
        Defines if two records are equivalent such that they represent the same
        checked out license, albeit possibly at different moments in time.

        Arguments:
            other (LeaseRecord) -- The other LeaseRecord to compare to.

        Returns:
            [bool] -- True if equivalent; false otherwise.
        '''

        selfSig = self.getSig()
        otherSig = other.getSig()
        return (selfSig == otherSig)

    def __hash__(self):
        return hash(self.getSig())

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __repr__(self):
        outTuple = (self.user, self.module, self.server,
                    self.terminal, self.version, self.licServer, self.start,
                    self.lastSeen, self.checkedOut)
        return 'LeaseRecord' + repr(outTuple)
