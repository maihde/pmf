#!/usr/bin/env python
"""
The Python Modelling Framework is an attempt to capture some of the features
found in the Eclipse Modeling Framework using Pythonic approaches.

Currently, the two primary features being implemented are notification,
containment, and adapters.
"""

class Notification(object):
    """
    Notifications indicate that something about the object has been modified.
    """
    EventTypes = frozenset(["ADD",
                            "ADD_MANY",
                            "MOVE",
                            "MOVE_MANY",
                            "REMOVE",
                            "REMOVE_MANY",
                            "SET",
                            "SET_MANY",
                           ]) 

    # Use slots for memory efficency, since a large model may
    # have a large number of Notifications
    __slots__ = [
                 "notifier",
                 "eventType",
                 "newValue",
                 "oldValue",
                 "position",
                 "feature",
                ]

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, None)
        for k, v in kw.items():
            setattr(self, k, v)
    
    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        # Clever __repr__ implementation to only print values that are non-None
        initArgs = ["%s=%r" % (k, getattr(self, k)) for k in self.__slots__ if getattr(self, k) != None]
        return "Notification(%s)" % (", ".join(initArgs))




class MObject(object):
    """
    The base class for all model objects.

    All public attributes of a MObject are treated
    all model attributes.  Public lists and dictionaries
    will be converted into their appropriate notifying objects
    
    Attribute modification:
       eventType = SET | SET_MANY
       notifier = The object whose attribute has been modified
       oldValue =  The old value
       new Value = The new value
       attribute = The attribute name
       
    Notifications can be disabled by setting _mDeliver to False.
    """
    def __init__(self):
        self._mDeliver = True
        self._mContainer = None
        self._mAdapters = []
        if hasattr(type(self), "mContainment"):
            self._mContainment = frozenset(getattr(type(self), "mContainment"))
        else:
            self._mContainment = frozenset([])

    def __setattr__(self, key, value):
        """
        Implement __setattr__ to produce notfications.
        """
        if key.startswith("_"):
            super(MObject, self).__setattr__(key, value)
        else:
            try:
                oldValue = getattr(self, key)
            except AttributeError:
                oldValue = None
            # If the oldValue is a MObject, unset containment
            if isinstance(oldValue, MObject) and key in self._mContainment:
                oldValue._mContainer = None
            # Adapt regular lists/dicts into their PMF equivalents
            if type(value) == list:
                value = MList(value,
                              container=self,
                              feature=self.__class__.__name__ + "." + key,
                              containment=(key in self._mContainment))
            if type(value) == dict:
                value = MDict(value)
            # Call the regular Python set attribute
            super(MObject, self).__setattr__(key, value)
            # If the value is a MObject, set containment
            if isinstance(value, MObject) and key in self._mContainment:
                value._mContainer = self
            # Emit a notification
            self.mNotify(notifier=self,
                         eventType="SET",
                         newValue=value,
                         oldValue=oldValue,
                         feature=self.__class__.__name__ + "." + key)

    def mAddAdapter(self, adapter):
        """
        Add an adapter to this object.  Has no effect if the adapter
        has already been added.
        """
        if adapter not in self._mAdapters:
            self._mAdapters.append(adapter)
            if adapter.target == None:
                adapter.target = self

    def mRemoveAdapter(self, adapter):
        """
        Remove an adapter from the object.  Has no effect if the adapter has
        not been added to the object.
        """
        if adapter in self._mAdapters:
            self._mAdapters.remove(adapter)
            if adapter.target == self:
                adapter.target = None
                    
    def mNotificationRequired(self):
        """
        Returns true if any adapters are registered to this object and if
        notifications have not bee disabled.
        """
        return ((len(self._mAdapters) > 0) and self._mDeliver)
    
    def mNotify(self, **kw):
        """
        Called when a notification needs to be sent.
        """
        if self.mNotificationRequired():
            notification = Notification(**kw)
            for adapter in self._mAdapters:
                adapter.notify(notification)
                    


 
class MList(list, MObject):
    """
    A list object that provides notifications.
    
    List Modification
       eventType = ADD | ADD_MANY
       notifier = The list object
       oldValue = None
       newValue = Either the element being added (ADD) or an iterable (ADD_MANY)
       position = The index of the element (ADD) or a slice object (ADD_MANY)
       
       eventType = REMOVE | REMOVE_MANY
       notifier = The list object
       oldValue = The element being removed (REMOVE) or an iterable (REMOVE_MANY)
       newValue = None
       position = The index of the element (REMOVE) or a slice object (REMOVE_MANY)
       
       eventType = SET | SET_MANY
       notifier = The list object
       oldValue =  The old value (SET) or an iterable (SET_MANY)
       new Value = The new value (SET) or an iterable (SET_MANY)
       position = The index of the element (SET) or a slice object (SET_MANY)
       
       As a special circumstance, MOVE_MANY will be emitted if sort() or 
       reverse() are called.
       
       eventType = MOVE_MANY
       notifier = The list object
       oldValue = None
       newValue = None
       position = A slice object for the entire list
    """
    def __init__(self, iterable=tuple(), container=None, containment=False, feature=None):
        MObject.__init__(self)
        list.__init__(self, iterable)
        self._container = container
        self._containment = containment
        self._feature = feature

    def append(self, value):
        list.append(self, value)
        if isinstance(value, MObject) and self._container != None:
            value._mContainer = self._container
        self.mNotify(notifier=self,
                     eventType="ADD",
                     newValue=value,
                     position=len(self)-1,
                     feature=self._feature)

    def extend(self, values):
        list.extend(self, values)
        for value in values:
            if isinstance(value, MObject) and self._container != None:
                value._mContainer = self._container
        self.mNotify(notifier=self,
                     eventType="ADD_MANY",
                     newValue=values,
                     position=slice(len(self)-len(values), len(self)-1),
                     feature=self._feature)

    def insert(self, key, value):
        list.append(self, value)
        if isinstance(value, MObject) and self._container != None:
            value._mContainer = self._container
        self.mNotify(notifier=self,
                     eventType="ADD",
                     newValue=value,
                     position=key,
                     feature=self._feature)
    
    def pop(self, key):
        try:
            oldValue = self[key]
        except IndexError:
            raise IndexError("pop index out of range")
        if isinstance(oldValue, MObject) and self._container != None:
            oldValue._mContainer = None
        list.pop(self, key)
        self.mNotify(notifier=self,
                     eventType="REMOVE",
                     oldValue=oldValue,
                     position=key,
                     feature=self._feature)

    def remove(self, value):
        try:
            position = self.index(value)
        except IndexError:
            position = None
        if isinstance(value, MObject) and self._container != None:
            value._mContainer = None
        list.remove(self, value)
        self.mNotify(notifier=self,
                     eventType="REMOVE",
                     oldValue=value,
                     position=position,
                     feature=self._feature)

    def reverse(self):
        list.reverse(self)
        self.mNotify(notifier=self,
                     eventType="MOVE_MANY",
                     position=slice(0, len(self)-1),
                     feature=self._feature)

    def sort(self):
        list.sort(self)
        self.mNotify(notifier=self,
                     eventType="MOVE_MANY",
                     position=slice(0, len(self)-1),
                     feature=self._feature)

    def __setslice__(self, i, j, values):
        oldValues = tuple(self[i:j])
        list.__setslice__(self, i, j, values)
        for value in values:
            if isinstance(value, MObject) and self._container != None:
                value._mContainer = self._container
        self.mNotify(notifier=self,
                     eventType="SET_MANY",
                     newValue=values,
                     oldValue=oldValues,
                     position=slice(i,j),
                     feature=self._feature)

    def __setitem__(self, key, value):
        try:
            oldValue = self[key]
        except IndexError:
            oldValue = None
        list.__setitem__(self, key, value)
        if isinstance(value, MObject) and self._container != None:
            value._mContainer = self._container
        self.mNotify(notifier=self,
                     eventType="SET",
                     newValue=value,
                     oldValue=oldValue,
                     position=key,
                     feature=self._feature)

    def __delslice__(self, i, j, values):
        oldValues = tuple(self[i:j])
        for oldValue in oldValues:
            if isinstance(oldValue, MObject) and self._container != None:
                oldValue._mContainer = None
        list.__setslice__(self, i, j, values)
        self.mNotify(notifier=self,
                     eventType="REMOVE_MANY",
                     oldValue=oldValues,
                     position=slice(i,j),
                     feature=self._feature)

    def __delitem__(self, key):
        try:
            oldValue = self[key]
        except IndexError:
            oldValue = None
        if isinstance(oldValue, MObject) and self._container != None:
            oldValue._mContainer = None
        list.__delitem__(self, key)
        self.mNotify(notifier=self,
                     eventType="REMOVE",
                     oldValue=oldValue,
                     position=key,
                     feature=self._feature)
  


class MDict(dict, MObject):
    """
    A dict object that provides notifications.
    
    For _MANY notifications, the oldValue and newValues are returned
    as a list of [(key, value)] paris, similar to .items()
    """
    def __init__(self, arg=tuple(), container=None, containment=False, feature=None):
        MObject.__init__(self)
        dict.__init__(self, arg)
        self._container = container
        self._containment = containment
        self._feature = feature

    def __setitem__(self, key, value):
        oldValue = self.get(key, None)
        dict.__setitem__(self, key, value)
        if isinstance(value, MObject) and self._container != None:
            value._mContainer = self._container
        self.mNotify(notifier=self,
                     eventType="SET",
                     newValue=value,
                     oldValue=oldValue,
                     position=key)
        
    def setdefault(self, key, value):
        oldValue = self.get(key, None)
        newValue = dict.setdefault(self, key, value)
        if isinstance(newValue, MObject) and self._container != None:
            newValue._mContainer = self._container
        self.mNotify(notifier=self,
                     eventType="SET",
                     newValue=newValue,
                     oldValue=oldValue,
                     position=key)
        return newValue

    def update(self, *args, **kw):
        newValues = {}
        if len(args) > 0:
            newValues = dict(args[0])
        newValues.update(kw)

        oldValues = {}
        for k in newValues.keys():
            try:
                oldValues[k, self[k]]
            except KeyError:
                pass
        for oldValue in oldValues.values():
            if isinstance(oldValue, MObject) and self._container != None:
                oldValue._mContainer = None
        dict.update(self, *args, **kw)
        for newValue in newValues.values():
            if isinstance(newValue, MObject) and self._container != None:
                newValue._mContainer = self._container
        self.mNotify(notifier=self,
                     eventType="SET_MANY",
                     newValue=newValues.items(),
                     oldValue=oldValues.items(),
                     position=newValues.keys())
        
    def pop(self, key, default=None):
        oldValue = self.get(key, None)
        v = dict.pop(self, key, default)
        if isinstance(oldValue, MObject) and self._container != None:
            oldValue._mContainer = None
        self.mNotify(notifier=self,
                     eventType="REMOVE",
                     oldValue=oldValue,
                     position=key)
        return v
        
    def popitem(self):
        oldValue = dict.popitem(self)
        if isinstance(oldValue, MObject) and self._container != None:
            oldValue._mContainer = None
        self.mNotify(notifier=self,
                     eventType="REMOVE",
                     oldValue=oldValue[1],
                     position=oldValue[0])
        return oldValue

    def __delitem__(self, key):
        oldValue = self.get(key, None)
        dict.__delitem__(self, key)
        if isinstance(oldValue, MObject) and self._container != None:
            oldValue._mContainer = None
        self.mNotify(notifier=self,
                     eventType="REMOVE",
                     oldValue=oldValue,
                     position=key)

    def clear(self):
        oldValues = self.items()
        oldKeys = self.keys()
        dict.clear(self)
        for oldValue in oldValues.values():
            if isinstance(oldValue, MObject) and self._container != None:
                oldValue._mContainer = None
        self.mNotify(notifier=self,
                     eventType="REMOVE_MANY",
                     oldValue=oldValues,
                     position=oldKeys,
                     feature=self._feature)



