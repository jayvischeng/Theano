
# import op
# import variable

import re, os
import ConfigParser

def hashgen():
    hashgen.next += 1
    return  hashgen.next
hashgen.next = 0

class MethodNotDefined(Exception): 
    """
    To be raised by functions defined as part of an interface.

    When the user sees such an error, it is because an important interface
    function has been left out of an implementation class.
    """

class object2(object):
    __slots__ = []
    if 0:
        def __hash__(self):
            # this fixes silent-error-prone new-style class behavior
            if hasattr(self, '__eq__') or hasattr(self, '__cmp__'):
                raise TypeError("unhashable object: %s" % self)
            return id(self)
    def __ne__(self, other):
        return not self == other

class scratchpad:
    def clear(self):
        self.__dict__.clear()
    def __update__(self, other):
        self.__dict__.update(other.__dict__)
        return self
    def __str__(self):
        return "scratch" + str(self.__dict__)

class D:
    def __init__(self, **d):
        self.__dict__.update(d)


def memoize(f):
    """Cache the return value for each tuple of arguments
    (which must be hashable) """
    cache = {}
    def rval(*args, **kwargs):
        kwtup = tuple(kwargs.items())
        key = (args, kwtup)
        if key not in cache:
            val = f(*args, **kwargs)
            cache[key] = val
        else:
            val = cache[key]
        return val
    return rval



def deprecated(filename, msg=''):
    """Decorator which will print a warning message on the first call.
    
    Use it like this:

    @deprecated('myfile', 'do something different...')
    def fn_name(...)
        ...

    And it will print

    WARNING myfile.fn_name deprecated. do something different...

    """
    def _deprecated(f):
        printme = [True]
        def g(*args, **kwargs):
            if printme[0]:
                print 'WARNING: %s.%s deprecated. %s'\
                        % (filename, f.__name__, msg)
                printme[0] = False
            return f(*args, **kwargs)
        return g
    return _deprecated

def uniq(seq):
    #TODO: consider building a set out of seq so that the if condition is constant time -JB
    return [x for i, x in enumerate(seq) if seq.index(x) == i]

def difference(seq1, seq2):
    """
    Returns all elements in seq1 which are not in seq2: i.e seq1\seq2 
    """
    try: 
        # try to use O(const * len(seq1)) algo
        if len(seq2) < 4: # I'm guessing this threshold -JB
            raise Exception('not worth it')
        set2 = set(seq2)
        return [x for x in seq1 if x not in set2]
    except Exception, e:
        # maybe a seq2 element is not hashable
        # maybe seq2 is too short
        # -> use O(len(seq1) * len(seq2)) algo
        return [x for x in seq1 if x not in seq2]


def partition(f, seq):
    seqt = []
    seqf = []
    for elem in seq:
        if f(elem):
            seqt.append(elem)
        else:
            seqf.append(elem)
    return seqt, seqf
    
def attr_checker(*attrs):
    def f(candidate):
        for attr in attrs:
            if not hasattr(candidate, attr):
                return False
        return True
    f.__doc__ = "Checks that the candidate has the following attributes: %s" % ", ".join(["'%s'"%attr for attr in attrs])
    return f


def all_bases(cls, accept):
    rval = set([cls])
    for base in cls.__bases__:
        rval.update(all_bases(base, accept))
    return [cls for cls in rval if accept(cls)]



def all_bases_collect(cls, raw_name):
    rval = set()
    name = "__%s__" % raw_name
    if name in cls.__dict__: # don't use hasattr
        rval.add(getattr(cls, name))
    cut = "__%s_override__" % raw_name
    if not cls.__dict__.get(cut, False):
        for base in cls.__bases__:
            rval.update(all_bases_collect(base, raw_name))
    return rval


def camelcase_to_separated(string, sep = "_"):
    return re.sub('(.)([A-Z])', '\\1%s\\2' % sep, string).lower()


def to_return_values(values):
    if len(values) == 1:
        return values[0]
    else:
        return values

def from_return_values(values):
    if isinstance(values, (list, tuple)):
        return values
    else:
        return [values]


def partial(func, *args, **keywords):
    def newfunc(*fargs, **fkeywords):
        newkeywords = keywords.copy()
        newkeywords.update(fkeywords)
        return func(*(args + fargs), **newkeywords)
    newfunc.func = func
    newfunc.args = args
    newfunc.keywords = keywords
    return newfunc


class ClsInit(type):
    """Class initializer for L{Op} subclasses"""
    def __init__(cls, name, bases, dct):
        """
        Validate and initialize the L{Op} subclass 'cls'

        This function:
          - changes class attributes input_names and output_names to be lists if they are single strings.
        """
        type.__init__(cls, name, bases, dct)

        cls.__clsinit__(cls, name, bases, dct)


def toposort(prereqs_d):
    """
    Sorts prereqs_d.keys() topologically. prereqs_d[x] contains all the elements
    that must come before x in the ordering.
    """

#     all1 = set(prereqs_d.keys())
#     all2 = set()
#     for x, y in prereqs_d.items():
#         all2.update(y)
#     print all1.difference(all2)
    
    seq = []
    done = set()
    postreqs_d = {}
    for x, prereqs in prereqs_d.items():
        for prereq in prereqs:
            postreqs_d.setdefault(prereq, set()).add(x)
    next = set([k for k in prereqs_d if not prereqs_d[k]])
    while next:
        bases = next
        next = set()
        for x in bases:
            done.add(x)
            seq.append(x)
        for x in bases:
            for postreq in postreqs_d.get(x, []):
                if not prereqs_d[postreq].difference(done):
                    next.add(postreq)
    if len(prereqs_d) != len(seq):
        raise Exception("Cannot sort topologically: there might be cycles, " + \
                        "prereqs_d does not have a key for each element or " + \
                        "some orderings contain invalid elements.")
    return seq


def print_for_dot(self):
    #TODO: popen2("dot -Tpng | display") and actually make the graph window pop up
     print "digraph unix { size = '6,6'; node [color = lightblue2; style = filled];"
     for op in self.order:
         for input in op.inputs:
             if input.owner:
                 print input.owner.__class__.__name__ + str(abs(id(input.owner))), " -> ", op.__class__.__name__ + str(abs(id(op))), ";"

class Keyword:

    def __init__(self, name, nonzero=True):
        self.name = name
        self.nonzero = nonzero

    def __nonzero__(self):
        return self.nonzero

    def __str__(self):
        return "<%s>" % self.name

    def __repr__(self):
        return "<%s>" % self.name

ABORT = Keyword("ABORT", False)
RETRY = Keyword("RETRY", False)
FAILURE = Keyword("FAILURE", False)


simple_types = (int, float, str, bool, None.__class__, Keyword)


ANY_TYPE = Keyword("ANY_TYPE")
FALL_THROUGH = Keyword("FALL_THROUGH")

def comm_guard(type1, type2):
    def wrap(f):
        old_f = f.func_globals[f.__name__]
        def new_f(arg1, arg2, *rest):
            if (type1 is ANY_TYPE or isinstance(arg1, type1)) \
                   and (type2 is ANY_TYPE or isinstance(arg2, type2)):
                pass
            elif (type1 is ANY_TYPE or isinstance(arg2, type1)) \
                     and (type2 is ANY_TYPE or isinstance(arg1, type2)):
                arg1, arg2 = arg2, arg1
            else:
                try:
                    return old_f(arg1, arg2, *rest)
                except:
                    raise

            try:
                variable = f(arg1, arg2, *rest)
            except:
                raise
            if variable is FALL_THROUGH:
                try:
                    return old_f(arg1, arg2, *rest)
                except:
                    raise
            else:
                return variable

        new_f.__name__ = f.__name__
        def typename(type):
            if isinstance(type, Keyword):
                return str(type)
            elif isinstance(type, (tuple, list)):
                return "(" + ", ".join([x.__name__ for x in type]) + ")"
            else:
                return type.__name__
        new_f.__doc__ = str(old_f.__doc__) + "\n" + ", ".join([typename(type) for type in (type1, type2)]) + "\n" + str(f.__doc__ or "")
        return new_f
    return wrap


def type_guard(type1):
    def wrap(f):
        old_f = f.func_globals[f.__name__]
        def new_f(arg1, *rest):
            if (type1 is ANY_TYPE or isinstance(arg1, type1)):
                variable = f(arg1, *rest)
                if variable is FALL_THROUGH:
                    return old_f(arg1, *rest)
                else:
                    return variable
            else:
                return old_f(arg1, *rest)


        new_f.__name__ = f.__name__
        def typename(type):
            if isinstance(type, Keyword):
                return str(type)
            elif isinstance(type, (tuple, list)):
                return "(" + ", ".join([x.__name__ for x in type]) + ")"
            else:
                return type.__name__
        new_f.__doc__ = str(old_f.__doc__) + "\n" + ", ".join([typename(type) for type in (type1,)]) + "\n" + str(f.__doc__ or "")
        return new_f
    return wrap

default_={
'ProfileMode.n_apply_to_print':15,
'ProfileMode.n_ops_to_print':20,
'tensor_opt.local_elemwise_fusion':False,
'lib.amdlibm':False,
}


class TheanoConfig(object):
    """Return the value for a key after parsing ~/.theano.cfg and 
    the THEANO_FLAGS environment variable.
    
    We parse in that order the value to have:
    1)the pair 'section.option':value in default_ 
    2)The ~/.theano.cfg file
    3)The value value provided in the get*() fct.
    The last value found is the value returned.
    
    The THEANO_FLAGS environement variable should be a list of comma-separated [section.]option[=value] entries. If the section part is omited, their should be only one section with that contain the gived option.
    """

    def __init__(self):
        d={} # no section
        for k,v in default_.items():
            if len(k.split('.'))==1:
                d[k]=v

        #set default value common for all section
        self.config = ConfigParser.SafeConfigParser(d)
        
        #set default value specific for each section
        for k, v in default_.items():
            sp = k.split('.',1)
            if len(sp)==2:
                if not self.config.has_section(sp[0]):
                    self.config.add_section(sp[0])
                self.config.set(sp[0], sp[1], str(v))


        #user config file override the default value
        self.config.read(['theano.cfg', os.path.expanduser('~/.theano.cfg')])

        self.env_flags=os.getenv("THEANO_FLAGS","")
        #The value in the env variable THEANO_FLAGS override the previous value
        for flag in self.env_flags.split(','):
            if not flag:
                continue
            sp=flag.split('=',1)
            if len(sp)==1:
                val=True
            else:
                val=sp[1]
            val=str(val)
            sp=sp[0].split('.',1)#option or section.option
            if len(sp)==2:
                self.config.set(sp[0],sp[1],val)
            else:
                found=0
                for sec in self.config.sections():
                    for opt in self.config.options(sec):
                        if opt == sp[0]:
                            found+=1
                            section=sec
                            option=opt
                if found==1:
                    self.config.set(section,option,val)
                elif found>1:
                    raise Exception("Ambiguous option (%s) in THEANO_FLAGS"%(sp[0]))
                
    def __getitem__(self, key):
        """:returns: a str with the value associated to the key"""
        return self.get(key)

    def get(self, key, val=None):
        """ 
        :param key: the key that we want the value
        :type key: str

        :returns: a str with the value associated to the key
        """
        #self.config.get(section, option, raw, vars)
        if val is not None:
            return val
        sp = key.split('.',1)
        if len(sp)!=2:
            raise Exception("When we get a key, their must be a section and an option")
        return self.config.get(sp[0],sp[1], False)

    def getfloat(self, key, val=None):
        """ :return: cast the output of self.get to a float"""
        if val is not None:
            return float(val)
        return float(self.get(key))

    def getboolean(self, key, val=None):
        """ :return: cast the output of self.get to a boolean"""
        if val is None:
            val=self.get(key)
        if val == "False" or val == "0" or not val:
            val = False
        else:
            val = True
        return val

    def getint(self, key, val=None):
        """ :return: cast the output of self.get to an int"""
        if val is not None:
            return int(val)
        return int(self.get(key))

config = TheanoConfig()

